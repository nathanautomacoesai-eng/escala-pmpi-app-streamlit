import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# =================================================================
# 1. CONFIGURAÇÃO E CRIAÇÃO DO BANCO DE DADOS LOCAL (SQLITE)
# =================================================================
def conectar_banco():
    conn = sqlite3.connect('escala.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS efetivo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE,
            nome_guerra TEXT,
            status TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escala (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            turno TEXT,
            policial_escalado TEXT
        )
    ''')
    conn.commit()
    return conn

conn = conectar_banco()

# =================================================================
# 2. ALGORITMO INTELIGENTE BASEADO EM DATAS REAIS
# =================================================================
def gerar_escala_inteligente(df_efetivo, df_escala, regime):
    pms_ativos = df_efetivo[df_efetivo['status'] == 'Ativo']['nome_guerra'].tolist()
    if not pms_ativos:
        return None

    ultimo_servico = {pm: None for pm in pms_ativos}
    horas_descanso = 72 if regime == "24x72" else 36

    for idx, row in df_escala.iterrows():
        data_escala_str = row['data']
        turno_escala = row['turno']
        
        data_atual = datetime.strptime(data_escala_str, "%d/%m/%Y")
        
        if "Noturno" in turno_escala:
            data_atual = data_atual + timedelta(hours=18)
        else:
            data_atual = data_atual + timedelta(hours=7)

        policial_escolhido = ""
        
        candidatos_validos = []
        for pm in pms_ativos:
            if ultimo_servico[pm] is None:
                candidatos_validos.append((pm, datetime.min))
            else:
                horas_desde_ultimo = (data_atual - ultimo_servico[pm]).total_seconds() / 3600
                if horas_desde_ultimo >= horas_descanso:
                    candidatos_validos.append((pm, ultimo_servico[pm]))
        
        if candidatos_validos:
            candidatos_validos.sort(key=lambda x: x[1])
            policial_escolhido = candidatos_validos[0][0]
        else:
            todos_pms = []
            for pm in pms_ativos:
                ult = ultimo_servico[pm] if ultimo_servico[pm] is not None else datetime.min
                if ult.strftime("%d/%m/%Y") != data_escala_str:
                    todos_pms.append((pm, ult))
            
            if todos_pms:
                todos_pms.sort(key=lambda x: x[1])
                policial_escolhido = todos_pms[0][0]

        if not policial_escolhido and pms_ativos:
            policial_escolhido = pms_ativos[idx % len(pms_ativos)]

        df_escala.loc[idx, 'policial_escalado'] = policial_escolhido
        ultimo_servico[policial_escolhido] = data_atual
            
    return df_escala

# =================================================================
# 3. INTERFACE VISUAL - STREAMLIT
# =================================================================
st.set_page_config(page_title="Sistema PMPI - Multi-Batalhão", layout="wide")

st.sidebar.header("⚙️ Configurações da OPM")
nome_batalhao = st.sidebar.text_input(
    "Identificação da Unidade:", 
    value="24º BATALHÃO DE POLÍCIA MILITAR - BPM"
)

qtd_pms_por_turno = st.sidebar.number_input(
    "PMs por Turno / Guarnição:", 
    min_value=1, max_value=10, value=1, step=1,
    help="Define quantos policiais cobrirão o mesmo turno simultaneamente."
)

st.sidebar.write("---")
st.sidebar.header("📅 Período da Escala")
data_inicio = st.sidebar.date_input("Data de Início:", value=datetime.today())
dias_escala = st.sidebar.number_input("Quantidade de Dias:", min_value=1, max_value=60, value=30, step=1)

aba_painel, aba_cadastro = st.tabs(["📊 Painel de Escalas", "👥 Cadastro de Policiais (P/1)"])

conn = conectar_banco()

# -----------------------------------------------------------------
# TELA 1: PAINEL DE ESCALAS
# -----------------------------------------------------------------
with aba_painel:
    st.title(f"SISTEMA DE GESTÃO - {nome_batalhao.upper()}")
    
    df_efetivo = pd.read_sql_query("SELECT * FROM efetivo", conn)
    df_escala_banco = pd.read_sql_query("SELECT data, turno, policial_escalado FROM escala", conn)
    
    regime_detectado_banco = "24x72"
    escala_ja_foi_gerada = False
    
    if not df_escala_banco.empty:
        if df_escala_banco['turno'].str.contains('12h').any():
            regime_detectado_banco = "12x36"
        if (df_escala_banco['policial_escalado'] != "").any():
            escala_ja_foi_gerada = True
        df_escala = df_escala_banco
    else:
        datas_geracao = pd.date_range(start=data_inicio, periods=dias_escala, freq="D")
        linhas_teste = []
        for d in datas_geracao:
            data_str = d.strftime("%d/%m/%Y")
            for _ in range(qtd_pms_por_turno):
                linhas_teste.append({"data": data_str, "turno": "24 Horas", "policial_escalado": ""})
        df_escala = pd.DataFrame(linhas_teste)

    regime_selecionado = st.selectbox("Selecione o Regime de Trabalho Ativo:", ["24x72", "12x36"])
    conflito_de_regime = escala_ja_foi_gerada and (regime_selecionado != regime_detectado_banco)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Efetivo Pronto")
        if df_efetivo.empty:
            st.info("Aguardando cadastro de policiais na aba P/1.")
        else:
            df_visualizacao = df_efetivo.copy()
            mapeamento_bolinhas = {"Ativo": "🟢 Ativo", "Férias": "🟡 Férias", "Afastado": "🔴 Afastado", "Licença": "🔵 Licença"}
            df_visualizacao['status'] = df_visualizacao['status'].map(mapeamento_bolinhas).fillna(df_visualizacao['status'])
            
            st.dataframe(
                df_visualizacao[['matricula', 'nome_guerra', 'status']], 
                width='stretch', 
                hide_index=True,
                column_config={"matricula": "Matrícula", "nome_guerra": "Nome de Guerra", "status": "Status"}
            )
        
    with col2:
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            if conflito_de_regime:
                st.warning(f"Escala vigente está em formato {regime_detectado_banco}!")
                if st.button("⚠️ Limpar Escala Antiga", type="secondary", width='stretch'):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM escala")
                    conn.commit()
                    st.success("Escala antiga limpa!")
                    st.rerun()
            else:
                if st.button("Gerar Escala no Python", type="primary", width='stretch'):
                    if df_efetivo.empty:
                        st.error("Cadastre policiais na outra tela antes de gerar!")
                    else:
                        datas_geracao = pd.date_range(start=data_inicio, periods=dias_escala, freq="D")
                        linhas_dinamicas = []
                        
                        for d in datas_geracao:
                            data_str = d.strftime("%d/%m/%Y")
                            if regime_selecionado == "24x72":
                                for i in range(qtd_pms_por_turno):
                                    linhas_dinamicas.append({"data": data_str, "turno": f"24 Horas (Vaga {i+1})" if qtd_pms_por_turno > 1 else "24 Horas", "policial_escalado": ""})
                            elif regime_selecionado == "12x36":
                                for i in range(qtd_pms_por_turno):
                                    linhas_dinamicas.append({"data": data_str, "turno": f"12h Diurno (Vaga {i+1})" if qtd_pms_por_turno > 1 else "12h Diurno", "policial_escalado": ""})
                                for i in range(qtd_pms_por_turno):
                                    linhas_dinamicas.append({"data": data_str, "turno": f"12h Noturno (Vaga {i+1})" if qtd_pms_por_turno > 1 else "12h Noturno", "policial_escalado": ""})
                                    
                        df_escala = pd.DataFrame(linhas_dinamicas)

                        escala_gerada = gerar_escala_inteligente(df_efetivo, df_escala, regime_selecionado)
                        if escala_gerada is not None:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM escala")
                            escala_gerada.to_sql('escala', conn, if_exists='append', index=False)
                            st.success("Escala parametrizada gerada!")
                            st.rerun()
                        
        with cc2:
            linhas_tabela = ""
            for idx, row in df_escala.iterrows():
                linhas_tabela += f"<tr><td>{row.iloc[0]}</td><td>{row.iloc[1]}</td><td>{row.iloc[2]}</td></tr>"
                
            brasao_pmpi_base64 = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 120' width='100' height='120'><path d='M50,10 C75,10 85,25 85,55 C85,85 50,110 50,110 C50,110 15,85 15,55 C15,25 25,10 50,10 Z' fill='none' stroke='%232c3e50' stroke-width='4'/><circle cx='50' cy='52' r='22' fill='none' stroke='%232c3e50' stroke-width='3'/><path d='M50,22 L50,82 M20,52 L80,52' stroke='%23e74c3c' stroke-width='2'/><path d='M35,35 L65,65 M35,65 L65,35' stroke='%23f1c40f' stroke-width='1.5'/><polygon points='50,42 53,49 61,49 55,54 57,61 50,57 43,61 45,54 39,49 47,49' fill='%23f1c40f'/></svg>"
                
            html_escala = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; margin: 30px; }}
                    .header {{ text-align: center; margin-bottom: 25px; }}
                    .brasao {{ width: 85px; height: auto; margin-bottom: 12px; }}
                    .header h1 {{ font-size: 16pt; margin: 5px 0; text-transform: uppercase; font-weight: bold; }}
                    .header h2 {{ font-size: 12pt; margin: 5px 0; text-transform: uppercase; font-weight: normal; color: #444; }}
                    .title {{ text-align: center; font-size: 14pt; font-weight: bold; text-transform: uppercase; margin: 25px 0; text-decoration: underline; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                    th {{ background-color: #2c3e50; color: white; font-size: 11pt; font-weight: bold; text-transform: uppercase; padding: 10px; border: 1px solid #1a252f; text-align: center; }}
                    td {{ padding: 10px; border: 1px solid #bdc3c7; font-size: 11pt; text-align: center; }}
                    tr:nth-child(even) td {{ background-color: #f9f9f9; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <img class="brasao" src="{brasao_pmpi_base64}" alt="PMPI">
                    <h1>{nome_batalhao.upper()}</h1>
                    <h2>POLÍCIA MILITAR DO PIAUÍ</h2>
                </div>
                <div class="title">ESCALA DE SERVIÇO GERAL</div>
                <table>
                    <thead><tr><th>Data</th><th>Turno</th><th>Policial Escalado</th></tr></thead>
                    <tbody>{linhas_tabela}</tbody>
                </table>
                <script>window.onload = function() {{ window.print(); }}</script>
            </body>
            </html>
            """
            st.download_button(
                label="🖨️ Exportar PDF / Imprimir",
                data=html_escala,
                file_name=f"escala_{nome_batalhao.lower().replace(' ', '_')}.html",
                mime="text/html",
                width='stretch'
            )
            
        with cc3:
            ativos_qtd = len(df_efetivo[df_efetivo['status'] == 'Ativo']) if not df_efetivo.empty else 0
            st.metric(label="EFETIVO ATIVO", value=str(ativos_qtd))
            
        st.subheader("Visualização da Escala Gerada")
        st.dataframe(
            df_escala, 
            width='stretch', 
            hide_index=True,
            column_config={"data": "Data", "turno": "Turno", "policial_escalado": "Policial Escalado"}
        )
        st.caption("Desenvolvido por: Nathanael Augusto")

# -----------------------------------------------------------------
# TELA 2: CADASTRO DE PMs
# -----------------------------------------------------------------
with aba_cadastro:
    st.title("Gerenciamento do Efetivo - P/1")
    
    with st.form("form_cadastro", clear_on_submit=True):
        st.subheader("Cadastrar Novo Policial")
        c1, c2, c3 = st.columns(3)
        with c1:
            nova_matricula = st.text_input("Matrícula (Ex: 102345-1)")
        with c2:
            novo_nome = st.text_input("Nome de Guerra (Ex: Cb Dos Anjos)")
        with c3:
            status_cadastro_visual = st.selectbox("Status Inicial", ["🟢 Ativo", "🟡 Férias", "🔴 Afastado", "🔵 Licença"])
            novo_status = status_cadastro_visual.split(" ")[1]
            
        botao_cadastrar = st.form_submit_button("Salvar Policial no Banco", type="primary")
        
        if botao_cadastrar:
            if nova_matricula and novo_nome:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO efetivo (matricula, nome_guerra, status) VALUES (?, ?, ?)",
                        (nova_matricula, novo_nome, novo_status)
                    )
                    conn.commit()
                    st.success(f"{novo_nome} cadastrado com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Erro: Já existe um policial cadastrado com esta Matrícula!")
            else:
                st.warning("Preencha todos os campos obrigatórios (Matrícula e Nome)!")

    st.write("---")
    st.subheader("Efetivo Cadastrado - Painel de Controle e Alterações")
    
    df_gerenciar = pd.read_sql_query("SELECT * FROM efetivo", conn)
    
    if df_gerenciar.empty:
        st.info("Nenhum policial cadastrado no banco local até o momento. Use o formulário acima!")
    else:
        col_hdr_mat, col_hdr_nome, col_hdr_status, col_hdr_acao = st.columns([2, 3, 3, 2])
        with col_hdr_mat: st.markdown("**Matrícula**")
        with col_hdr_nome: st.markdown("**Nome de Guerra**")
        with col_hdr_status: st.markdown("**Status Atual (Mude para Atualizar)**")
        with col_hdr_acao: st.markdown("**Ações**")
        st.write("")

        lista_status_visual = ["🟢 Ativo", "🟡 Férias", "🔴 Afastado", "🔵 Licença"]
        
        for idx, row in df_gerenciar.iterrows():
            col_mat, col_nome, col_status, col_acao = st.columns([2, 3, 3, 2])
            
            with col_mat:
                st.write(row['matricula'])
                
            with col_nome:
                st.write(row['nome_guerra'])
                
            with col_status:
                texto_status_banco = row['status']
                index_atual = 0
                if texto_status_banco == "Férias": index_atual = 1
                elif texto_status_banco == "Afastado": index_atual = 2
                elif texto_status_banco == "Licença": index_atual = 3
                
                status_selecionado_visual = st.selectbox(
                    "Status",
                    options=lista_status_visual,
                    index=index_atual,
                    key=f"status_{row['id']}",
                    label_visibility="collapsed"
                )
                
                status_puro_novo = status_selecionado_visual.split(" ")[1]
                
                if status_puro_novo != texto_status_banco:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE efetivo SET status = ? WHERE id = ?", (status_puro_novo, row['id']))
                    conn.commit()
                    st.toast(f"Status de {row['nome_guerra']} alterado para {status_selecionado_visual}!", icon="🔄")
                    st.rerun()
                    
            with col_acao:
                if st.button("Remover", key=f"del_{row['id']}", type="secondary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM efetivo WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.success("Policial removido!")
                    st.rerun()
