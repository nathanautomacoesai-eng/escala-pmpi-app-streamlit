import streamlit as st
import pandas as pd
import sqlite3
import base64
import os
from datetime import datetime, timedelta

# =================================================================
# FUNÇÃO PARA CONVERTER IMAGEM LOCAL EM BASE64
# =================================================================
def carregar_imagem_base64(caminho_imagem):
    if os.path.exists(caminho_imagem):
        with open(caminho_imagem, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/png;base64,{encoded_string}"
    return ""

# =================================================================
# LISTAS DE REFERÊNCIA DA PMPI
# =================================================================
LISTA_PATENTES = [
    "Coronel (Cel)",
    "Tenente-Coronel (Ten-Cel)",
    "Major (Maj)",
    "Capitão (Cap)",
    "1º Tenente (1º Ten)",
    "2º Tenente (2º Ten)",
    "Aspirante-a-Oficial (Asp)",
    "Subtenente (Sub-Ten)",
    "1º Sargento (1º Sgt)",
    "2º Sargento (2º Sgt)",
    "3º Sargento (3º Sgt)",
    "Cabo (Cb)",
    "Soldado (Sd)"
]

LISTA_OPMS_PMPI = [
    # Capital (Teresina)
    "1º BPM - CENTRO",
    "5º BPM - ZONA LESTE",
    "6º BPM - ZONA SUL",
    "8º BPM - ZONA SUDESTE",
    "9º BPM - ZONA NORTE",
    "13º BPM - GRANDE SANTA MARIA",
    "17º BPM - EXTREMO SUL / PORTO ALEGRE",
    "21º BPM - USINA SANTANA / SUDESTE",
    "22º BPM - PROMORAR",
    "29º BPM - REFORÇO ZONA LESTE",
    
    # Interior
    "2º BPM - PARNAÍBA",
    "3º BPM - FLORIANO",
    "4º BPM - PICOS",
    "7º BPM - CORRENTE",
    "10º BPM - URUÇUÍ",
    "11º BPM - SÃO RAIMUNDO NONATO",
    "12º BPM - PIRIPIRI",
    "14º BPM - SIMPLÍCIO MENDES",
    "15º BPM - CAMPO MAIOR",
    "16º BPM - JOSÉ DE FREITAS",
    "18º BPM - ÁGUA BRANCA",
    "19º BPM - BOM JESUS",
    "20º BPM - PAULISTANA",
    "23º BPM - VALENÇA DO PIAUÍ",
    "24º BPM - LUÍS CORREIA",
    "27º BPM - PARNAÍBA (DIVISA NORTE)",
    "30º BPM - BARRAS",
    "31º BPM - COCAL",
    
    # Especializados
    "BOPE - OPERAÇÕES ESPECIAIS",
    "BPRONE - RONDAS ESPECIAIS",
    "BPCHOQUE - POLICIAMENTO DE CHOQUE",
    "BPROCAM - RONDAS SOBRE MOTOCICLETAS",
    "BEPI - POLICIAMENTO DO INTERIOR",
    "BPA - POLICIAMENTO AMBIENTAL",
    "BPTRAN - POLICIAMENTO DE TRÂNSITO",
    "BPGDAS - POLICIAMENTO DE GUARDA"
]

# =================================================================
# 1. BANCO DE DADOS LOCAL (SQLITE)
# =================================================================
def conectar_banco():
    conn = sqlite3.connect('escala.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS efetivo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE,
            posto_graduacao TEXT,
            nome_guerra TEXT,
            status TEXT,
            batalhao TEXT
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE efetivo ADD COLUMN posto_graduacao TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escala (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            turno TEXT,
            policial_escalado TEXT,
            batalhao TEXT
        )
    ''')
    conn.commit()
    return conn

def obter_batalhoes_cadastrados(conn):
    df_batalhoes = pd.read_sql_query("SELECT DISTINCT batalhao FROM efetivo WHERE batalhao IS NOT NULL AND batalhao != ''", conn)
    if not df_batalhoes.empty:
        return sorted(df_batalhoes['batalhao'].tolist())
    return [LISTA_OPMS_PMPI[0]]

# =================================================================
# 2. ALGORITMO DE GERAÇÃO DE ESCALA
# =================================================================
def gerar_escala_inteligente(df_efetivo, df_escala, regime):
    if 'posto_graduacao' in df_efetivo.columns:
        df_efetivo['nome_completo'] = df_efetivo.apply(
            lambda r: f"{r['posto_graduacao']} {r['nome_guerra']}" if pd.notnull(r['posto_graduacao']) and r['posto_graduacao'] != "" else r['nome_guerra'], 
            axis=1
        )
    else:
        df_efetivo['nome_completo'] = df_efetivo['nome_guerra']

    pms_ativos = df_efetivo[df_efetivo['status'] == 'Ativo']['nome_completo'].tolist()
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
# 3. INTERFACE VISUAL
# =================================================================
st.set_page_config(page_title="Sistema PMPI - Multi-Batalhão", layout="wide")

conn = conectar_banco()
lista_batalhoes_filtrados = obter_batalhoes_cadastrados(conn)

st.sidebar.header("⚙️ Configurações da OPM")
batalhao_selecionado = st.sidebar.selectbox("Unidade Policial (OPM):", lista_batalhoes_filtrados)

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

# -----------------------------------------------------------------
# TELA 1: PAINEL DE ESCALAS
# -----------------------------------------------------------------
with aba_painel:
    st.title(f"SISTEMA DE GESTÃO - {batalhao_selecionado.upper()}")
    
    df_efetivo = pd.read_sql_query("SELECT * FROM efetivo WHERE batalhao = ?", conn, params=(batalhao_selecionado,))
    df_escala_banco = pd.read_sql_query("SELECT data, turno, policial_escalado FROM escala WHERE batalhao = ?", conn, params=(batalhao_selecionado,))
    
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
            st.info(f"Nenhum policial cadastrado para o {batalhao_selecionado}. Cadastre na aba P/1.")
        else:
            df_visualizacao = df_efetivo.copy()
            mapeamento_bolinhas = {"Ativo": "🟢 Ativo", "Férias": "🟡 Férias", "Afastado": "🔴 Afastado", "Licença": "🔵 Licença"}
            df_visualizacao['status'] = df_visualizacao['status'].map(mapeamento_bolinhas).fillna(df_visualizacao['status'])
            df_visualizacao['Policial'] = df_visualizacao['posto_graduacao'].fillna('') + ' ' + df_visualizacao['nome_guerra']
            
            st.dataframe(
                df_visualizacao[['matricula', 'Policial', 'status']], 
                use_container_width=True, 
                hide_index=True,
                column_config={"matricula": "Matrícula", "Policial": "Posto / Nome", "status": "Status"}
            )
        
    with col2:
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            if conflito_de_regime:
                st.warning(f"Escala vigente está em formato {regime_detectado_banco}!")
                if st.button("⚠️ Limpar Escala Antiga", type="secondary", use_container_width=True):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM escala WHERE batalhao = ?", (batalhao_selecionado,))
                    conn.commit()
                    st.success("Escala antiga limpa!")
                    st.rerun()
            else:
                if st.button("Gerar Escala", type="primary", use_container_width=True):
                    if df_efetivo.empty:
                        st.error("Cadastre policiais para esta unidade antes de gerar!")
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
                            escala_gerada['batalhao'] = batalhao_selecionado
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM escala WHERE batalhao = ?", (batalhao_selecionado,))
                            escala_gerada.to_sql('escala', conn, if_exists='append', index=False)
                            st.success(f"Escala gerada com sucesso para o {batalhao_selecionado}!")
                            st.rerun()
                        
        with cc2:
            linhas_tabela = ""
            for idx, row in df_escala.iterrows():
                linhas_tabela += f"<tr><td>{row.iloc[0]}</td><td>{row.iloc[1]}</td><td>{row.iloc[2]}</td></tr>"
                
            # Carrega a imagem local 'brasao.png'
            brasao_src = carregar_imagem_base64("brasao.png")
            
            tag_imagem = f'<img class="brasao" src="{brasao_src}" alt="Brasão PMPI">' if brasao_src else ''
                
            html_escala = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; color: #000; margin: 20px; }}
                    .header {{ display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 20px; }}
                    .brasao {{ width: 85px; height: auto; }}
                    .header-text {{ text-align: left; }}
                    .header h1 {{ font-size: 16pt; margin: 0; text-transform: uppercase; font-weight: bold; font-family: Arial, sans-serif; }}
                    .title {{ text-align: center; font-size: 14pt; font-weight: bold; text-transform: uppercase; margin-top: 20px; margin-bottom: 25px; letter-spacing: 1px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                    th {{ background-color: #ffffff; color: #000; font-size: 11pt; font-weight: bold; text-transform: uppercase; padding: 8px; border: 1px solid #000; text-align: center; }}
                    td {{ padding: 8px; border: 1px solid #000; font-size: 11pt; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="header">
                    {tag_imagem}
                    <div class="header-text">
                        <h1>{batalhao_selecionado.upper()}</h1>
                    </div>
                </div>
                
                <div class="title">ESCALA DE SERVIÇO</div>
                
                <table>
                    <thead>
                        <tr>
                            <th>DATA</th>
                            <th>TURNO</th>
                            <th>POLICIAL ESCALADO</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_tabela}
                    </tbody>
                </table>
                <script>window.onload = function() {{ window.print(); }}</script>
            </body>
            </html>
            """
            st.download_button(
                label="🖨️ Exportar PDF / Imprimir",
                data=html_escala,
                file_name=f"escala_{batalhao_selecionado.lower().replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True
            )
            
        with cc3:
            ativos_qtd = len(df_efetivo[df_efetivo['status'] == 'Ativo']) if not df_efetivo.empty else 0
            st.metric(label="EFETIVO ATIVO", value=str(ativos_qtd))
            
        st.subheader("Visualização da Escala Gerada")
        st.dataframe(
            df_escala, 
            use_container_width=True, 
            hide_index=True,
            column_config={"data": "Data", "turno": "Turno", "policial_escalado": "Policial Escalado"}
        )
        st.caption("Desenvolvido por: Nathanael Augusto")

# -----------------------------------------------------------------
# TELA 2: CADASTRO DE PMs (P/1)
# -----------------------------------------------------------------
with aba_cadastro:
    st.title("Gerenciamento do Efetivo - P/1")
    
    with st.form("form_cadastro", clear_on_submit=True):
        st.subheader("Cadastrar Novo Policial")
        c1, c2, c3, c4, c5 = st.columns([2, 3, 3, 2, 4])
        
        with c1:
            nova_matricula = st.text_input("Matrícula (Ex: 102345-1)")
        with c2:
            novo_posto = st.selectbox("Posto / Graduação", options=LISTA_PATENTES)
        with c3:
            novo_nome = st.text_input("Nome de Guerra (Ex: Geovanio)")
        with c4:
            status_cadastro_visual = st.selectbox("Status Inicial", ["🟢 Ativo", "🟡 Férias", "🔴 Afastado", "🔵 Licença"])
            novo_status = status_cadastro_visual.split(" ")[1]
        with c5:
            batalhao_cadastro = st.selectbox("Batalhão / OPM", options=LISTA_OPMS_PMPI)
            
        botao_cadastrar = st.form_submit_button("Salvar Policial no Banco", type="primary")
        
        if botao_cadastrar:
            if nova_matricula and novo_nome and batalhao_cadastro:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO efetivo (matricula, posto_graduacao, nome_guerra, status, batalhao) VALUES (?, ?, ?, ?, ?)",
                        (nova_matricula, novo_posto, novo_nome, novo_status, batalhao_cadastro)
                    )
                    conn.commit()
                    st.success(f"{novo_posto} {novo_nome} cadastrado com sucesso no {batalhao_cadastro}!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Erro: Já existe um policial cadastrado com esta Matrícula!")
            else:
                st.warning("Preencha todos os campos obrigatórios!")

    st.write("---")
    st.subheader(f"Efetivo Cadastrado - {batalhao_selecionado}")
    
    df_gerenciar = pd.read_sql_query("SELECT * FROM efetivo WHERE batalhao = ?", conn, params=(batalhao_selecionado,))
    
    if df_gerenciar.empty:
        st.info(f"Nenhum policial cadastrado para o {batalhao_selecionado} até o momento.")
    else:
        col_hdr_mat, col_hdr_posto, col_hdr_nome, col_hdr_status, col_hdr_acao = st.columns([2, 2, 3, 3, 2])
        with col_hdr_mat: st.markdown("**Matrícula**")
        with col_hdr_posto: st.markdown("**Posto/Grad.**")
        with col_hdr_nome: st.markdown("**Nome de Guerra**")
        with col_hdr_status: st.markdown("**Status Atual**")
        with col_hdr_acao: st.markdown("**Ações**")
        st.write("")

        lista_status_visual = ["🟢 Ativo", "🟡 Férias", "🔴 Afastado", "🔵 Licença"]
        
        for idx, row in df_gerenciar.iterrows():
            col_mat, col_posto, col_nome, col_status, col_acao = st.columns([2, 2, 3, 3, 2])
            
            with col_mat:
                st.write(row['matricula'])
                
            with col_posto:
                st.write(row['posto_graduacao'] if pd.notnull(row['posto_graduacao']) else '-')
                
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