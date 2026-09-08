import streamlit as st
import pandas as pd
import sqlite3
import base64
import os
from datetime import datetime, timedelta

# =================================================================
# ESTRUTURA COMPLETA DA PMPI (UNIDADES E SUBUNIDADES)
# =================================================================
ESTRUTURA_PMPI = {
    # 1. Batalhões de Área - Teresina e Entorno
    "1º BPM (Teresina - Centro/Zona Sul)": [
        "1ª Cia: Centro Comercial",
        "2ª Cia: Bairro Vermelha e Ilhotas",
        "3ª Cia: Bairro Poti Velho / Primavera"
    ],
    "5º BPM (Teresina - Zona Leste)": [
        "1ª Cia: Bairro Ininga e Jóquei",
        "2ª Cia: Bairro Pedra Mole e Tabajaras",
        "3ª Cia: Bairro Planalto Uruguai"
    ],
    "6º BPM (Teresina - Zona Sul)": [
        "1ª Cia: Bairro Lourival Parente",
        "2ª Cia: Distrito Industrial / Tabuleta",
        "3ª Cia: Bairro Saci e Bela Vista"
    ],
    "8º BPM (Teresina - Zona Sudeste)": [
        "1ª Cia: Bairro Dirceu Arcoverde I e II",
        "2ª Cia: Bairro Novo Horizonte / Parque Ideal",
        "3ª Cia: Bairro Redonda / Itararé"
    ],
    "9º BPM (Teresina - Zona Norte)": [
        "1ª Cia: Bairro Mocambinho",
        "2ª Cia: Bairro São Joaquim / Buenos Aires",
        "3ª Cia: Bairro Aeroporto"
    ],
    "13º BPM (Teresina - Zona Norte Extrema)": [
        "1ª Cia: Santa Maria da Codipi",
        "2ª Cia: Jacinta Andrade"
    ],
    "17º BPM (Teresina - Zona Sul Extrema e Entorno)": [
        "1ª Cia: Bairro Porto Alegre / Esplanada",
        "2ª Cia: Bairro Torquato Neto / Promorar",
        "3ª Cia: Sede no Município de Nazária"
    ],
    "21º BPM (Altos e Região)": [
        "1ª Cia: Altos (Sede)",
        "2ª Cia: Alto Longá",
        "3ª Cia: Coivaras / Beneditinos"
    ],
    "22º BPM (Teresina - Promorar e Região)": [
        "1ª Cia: Promorar",
        "2ª Cia: Vila Irmã Dulce"
    ],
    "26º BPM (Teresina - Usina Santana e Zona Rural Sudeste)": [
        "1ª Cia: Usina Santana",
        "2ª Cia: Caldeirão / Entrada de José de Freitas"
    ],

    # Interior do Estado
    "2º BPM (Parnaíba - Litoral)": [
        "1ª Cia: Parnaíba (Centro e Área Urbana)",
        "2ª Cia: Ilha Grande",
        "3ª Cia: Buriti dos Lopes"
    ],
    "3º BPM (Floriano)": [
        "1ª Cia: Floriano (Sede Urbana)",
        "2ª Cia: Barão de Grajaú e Entorno",
        "3ª Cia: Itaueira"
    ],
    "4º BPM (Picos)": [
        "1ª Cia: Picos (Sede Urbana)",
        "2ª Cia: Fronteiras",
        "3ª Cia: Jaicós",
        "4ª Cia: Simões"
    ],
    "7º BPM (Corrente)": [
        "1ª Cia: Corrente (Sede)",
        "2ª Cia: Avelino Lopes",
        "3ª Cia: Parnaguá"
    ],
    "10º BPM (Uruçuí)": [
        "1ª Cia: Uruçuí (Sede)",
        "2ª Cia: Baixa Grande do Ribeiro",
        "3ª Cia: Ribeiro Gonçalves"
    ],
    "11º BPM (São Raimundo Nonato)": [
        "1ª Cia: São Raimundo Nonato (Sede)",
        "2ª Cia: Anísio de Abreu",
        "3ª Cia: Caracol"
    ],
    "12º BPM (Piripiri)": [
        "1ª Cia: Piripiri (Sede)",
        "2ª Cia: Pedro II",
        "3ª Cia: Capitão de Campos"
    ],
    "14º BPM (Oeiras)": [
        "1ª Cia: Oeiras (Sede)",
        "2ª Cia: Simplício Mendes",
        "3ª Cia: Santa Cruz do Piauí"
    ],
    "15º BPM (Campo Maior)": [
        "1ª Cia: Campo Maior (Sede)",
        "2ª Cia: Castelo do Piauí",
        "3ª Cia: São Miguel do Tapuio"
    ],
    "16º BPM (União)": [
        "1ª Cia: União (Sede)",
        "2ª Cia: Miguel Alves",
        "3ª Cia: Lagoa Alegre"
    ],
    "18º BPM (Água Branca)": [
        "1ª Cia: Água Branca (Sede)",
        "2ª Cia: Amarante",
        "3ª Cia: Barro Duro"
    ],
    "19º BPM (Bom Jesus)": [
        "1ª Cia: Bom Jesus (Sede)",
        "2ª Cia: Curimatá",
        "3ª Cia: Gilbués"
    ],
    "20º BPM (Paulistana)": [
        "1ª Cia: Paulistana (Sede)",
        "2ª Cia: Simões / Caridade",
        "3ª Cia: Queimada Nova"
    ],
    "23º BPM (Valença do Piauí)": [
        "1ª Cia: Valença (Sede)",
        "2ª Cia: Elesbão Veloso",
        "3ª Cia: Inhuma"
    ],
    "24º BPM (Luís Correia)": [
        "1ª Cia: Luís Correia (Sede)",
        "2ª Cia: Cajueiro da Praia / Barra Grande"
    ],
    "25º BPM (Esperantina)": [
        "1ª Cia: Esperantina (Sede)",
        "2ª Cia: Luzilândia",
        "3ª Cia: Matias Olímpio"
    ],
    "28º BPM (Canto do Buriti)": [
        "1ª Cia: Canto do Buriti (Sede)",
        "2ª Cia: Brejo do Piauí"
    ],
    "29º BPM (Piracuruca)": [
        "1ª Cia: Piracuruca (Sede)",
        "2ª Cia: São José do Divino"
    ],
    "30º BPM (Barras)": [
        "1ª Cia: Barras (Sede)",
        "2ª Cia: Batalha",
        "3ª Cia: Cabeceiras do Piauí"
    ],

    # 2. Companhias Independentes (CIPM)
    "CIPPA - Proteção Ambiental": ["Sede Operacional"],
    "CIPE - Policiamento Escolar": ["Sede Operacional"],
    "CIPTUR - Policiamento Turístico": ["Sede Luís Correia / Barra Grande"],
    "CIPGD - Policiamento de Guarda": ["Sede Operacional"],
    "1ª CIPM - Promorar": ["Sede Promorar"],
    "2ª CIPM - São Pedro do Piauí": ["Sede São Pedro"],
    "3ª CIPM - Jaicós": ["Sede Jaicós"],
    "4ª CIPM - Fronteiras": ["Sede Fronteiras"],

    # 3. Batalhões Especializados (CPE)
    "BOPE - Operações Especiais": ["Sede Teresina"],
    "BPRONE - Rondas Ostensivas": ["Sede Teresina"],
    "BPCHOQUE - Policiamento de Choque": ["Sede Teresina"],
    "BEPI - Policiamento do Interior": ["Base Pavussu", "Base Torquato Neto", "Base Picos"],
    "BPA - Policiamento Ambiental": ["Sede Teresina"],
    "BPTRAN - Policiamento de Trânsito": ["Sede Teresina"],
    "BPRE - Polícia Rodoviária Estadual": ["Sede Teresina"],
    "BPGDAS - Guardas e Presídios": ["Sede Teresina"],
    "BPROCAM - Motocicletas (ROCAM)": ["Sede Teresina"],
    "BOPAER - Operações Aéreas": ["Base Hangar Teresina"],
    "RPMont - Cavalaria": ["Regimento Teresina"],

    # 4. Unidades Integradas de Segurança Pública (UISP)
    "UISP Centro / Praça da Bandeira (Teresina)": ["Sede UISP"],
    "UISP Parque Piauí (Teresina)": ["Sede UISP"],
    "UISP Dirceu Arcoverde / Itararé (Teresina)": ["Sede UISP"],
    "UISP Bairro Satélite (Teresina)": ["Sede UISP"],
    "UISP Mocambinho (Teresina)": ["Sede UISP"],
    "UISP Parnaíba (Litoral)": ["Sede UISP"],
    "UISP Picos (Centro-Sul)": ["Sede UISP"],
    "UISP Floriano (Médio Parnaíba)": ["Sede UISP"]
}

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

# =================================================================
# FUNÇÕES DE BANCO DE DADOS E SUPORTE
# =================================================================
def obter_brasao_local():
    pasta_atual = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.'
    opcoes = ['brasao.png', 'brasao.png.png', 'brasao.PNG', 'brasao.jpg']
    
    for nome in opcoes:
        caminho = os.path.join(pasta_atual, nome)
        if os.path.exists(caminho):
            with open(caminho, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode('utf-8')
                return f"data:image/png;base64,{encoded}"
    return ""

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
            batalhao TEXT,
            companhia TEXT
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE efetivo ADD COLUMN posto_graduacao TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE efetivo ADD COLUMN companhia TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escala (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            turno TEXT,
            policial_escalado TEXT,
            batalhao TEXT,
            companhia TEXT
        )
    ''')
    conn.commit()
    return conn

# =================================================================
# ALGORITMO DE ESCALA INTELIGENTE
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
# MODAL PARA EDIÇÃO COMPLETA DE DADOS DO POLICIAL
# =================================================================
@st.dialog("✏️ Editar Policial")
def modal_editar_policial(conn, policial_data):
    id_pm = policial_data['id']
    
    with st.form(key=f"form_edicao_{id_pm}"):
        edit_mat = st.text_input("Matrícula", value=str(policial_data['matricula']))
        
        idx_posto = LISTA_PATENTES.index(policial_data['posto_graduacao']) if policial_data['posto_graduacao'] in LISTA_PATENTES else 0
        edit_posto = st.selectbox("Posto / Graduação", options=LISTA_PATENTES, index=idx_posto)
        
        edit_nome = st.text_input("Nome de Guerra", value=str(policial_data['nome_guerra']))
        
        lista_batalhoes = list(ESTRUTURA_PMPI.keys())
        idx_bat = lista_batalhoes.index(policial_data['batalhao']) if policial_data['batalhao'] in lista_batalhoes else 0
        edit_bat = st.selectbox("Batalhão / Unidade", options=lista_batalhoes, index=idx_bat)
        
        opcoes_cias_edit = ESTRUTURA_PMPI.get(edit_bat, ["Sede / Geral"])
        idx_cia = opcoes_cias_edit.index(policial_data['companhia']) if policial_data['companhia'] in opcoes_cias_edit else 0
        edit_cia = st.selectbox("Companhia / UISP", options=opcoes_cias_edit, index=idx_cia)
        
        lista_status = ["Ativo", "Férias", "Afastado", "Licença"]
        idx_st = lista_status.index(policial_data['status']) if policial_data['status'] in lista_status else 0
        edit_status = st.selectbox("Status", options=lista_status, index=idx_st)
        
        btn_salvar = st.form_submit_button("Salvar Alterações", type="primary", use_container_width=True)
        
        if btn_salvar:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE efetivo 
                    SET matricula=?, posto_graduacao=?, nome_guerra=?, status=?, batalhao=?, companhia=?
                    WHERE id=?
                """, (edit_mat, edit_posto, edit_nome, edit_status, edit_bat, edit_cia, id_pm))
                conn.commit()
                st.success("Dados do policial atualizados com sucesso!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Erro: A matrícula informada já está cadastrada em outro policial.")

# =================================================================
# INTERFACE PRINCIPAL
# =================================================================
st.set_page_config(page_title="Sistema PMPI - Gestão de Escalas", layout="wide")
conn = conectar_banco()

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Filtro da Escala")

lista_batalhoes_existentes = list(ESTRUTURA_PMPI.keys())
batalhao_selecionado = st.sidebar.selectbox("Batalhão / Unidade:", lista_batalhoes_existentes)

opcoes_companhias = ESTRUTURA_PMPI.get(batalhao_selecionado, ["Todas"])
companhia_selecionada = st.sidebar.selectbox("Companhia / UISP:", ["Todas"] + opcoes_companhias)

qtd_pms_por_turno = st.sidebar.number_input(
    "PMs por Turno / Guarnição:", 
    min_value=1, max_value=10, value=1, step=1
)

st.sidebar.write("---")
st.sidebar.header("📅 Período da Escala")
data_inicio = st.sidebar.date_input("Data de Início:", value=datetime.today())
dias_escala = st.sidebar.number_input("Quantidade de Dias:", min_value=1, max_value=60, value=30, step=1)

# --- ABAS DA APLICAÇÃO ---
aba_painel, aba_visao_geral, aba_cadastro = st.tabs(["📊 Painel de Escalas", "📈 Visão Geral", "👥 Cadastro de Policiais"])

# -----------------------------------------------------------------
# TELA 1: PAINEL DE ESCALAS
# -----------------------------------------------------------------
with aba_painel:
    subtitulo_opm = f"{batalhao_selecionado.upper()}"
    if companhia_selecionada != "Todas":
        subtitulo_opm += f" - {companhia_selecionada.upper()}"
        
    st.title(f"SISTEMA DE GESTÃO - {subtitulo_opm}")
    
    if companhia_selecionada == "Todas":
        query_efetivo = "SELECT * FROM efetivo WHERE batalhao = ?"
        params_efetivo = (batalhao_selecionado,)
        query_escala = "SELECT data, turno, policial_escalado FROM escala WHERE batalhao = ?"
        params_escala = (batalhao_selecionado,)
    else:
        query_efetivo = "SELECT * FROM efetivo WHERE batalhao = ? AND companhia = ?"
        params_efetivo = (batalhao_selecionado, companhia_selecionada)
        query_escala = "SELECT data, turno, policial_escalado FROM escala WHERE batalhao = ? AND companhia = ?"
        params_escala = (batalhao_selecionado, companhia_selecionada)
        
    df_efetivo = pd.read_sql_query(query_efetivo, conn, params=params_efetivo)
    df_escala_banco = pd.read_sql_query(query_escala, conn, params=params_escala)
    
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
            st.info("Nenhum policial encontrado com os filtros selecionados.")
        else:
            df_visualizacao = df_efetivo.copy()
            mapeamento_bolinhas = {"Ativo": "🟢 Ativo", "Férias": "🟡 Férias", "Afastado": "🔴 Afastado", "Licença": "🔵 Licença"}
            df_visualizacao['status'] = df_visualizacao['status'].map(mapeamento_bolinhas).fillna(df_visualizacao['status'])
            df_visualizacao['Policial'] = df_visualizacao['posto_graduacao'].fillna('') + ' ' + df_visualizacao['nome_guerra']
            
            st.dataframe(
                df_visualizacao[['matricula', 'Policial', 'companhia', 'status']], 
                use_container_width=True, 
                hide_index=True,
                column_config={"matricula": "Matrícula", "Policial": "Posto / Nome", "companhia": "Companhia/UISP", "status": "Status"}
            )
        
    with col2:
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            if conflito_de_regime:
                st.warning(f"Escala vigente está em formato {regime_detectado_banco}!")
                if st.button("⚠️ Limpar Escala Antiga", type="secondary", use_container_width=True):
                    cursor = conn.cursor()
                    if companhia_selecionada == "Todas":
                        cursor.execute("DELETE FROM escala WHERE batalhao = ?", (batalhao_selecionado,))
                    else:
                        cursor.execute("DELETE FROM escala WHERE batalhao = ? AND companhia = ?", (batalhao_selecionado, companhia_selecionada))
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
                            escala_gerada['companhia'] = companhia_selecionada
                            cursor = conn.cursor()
                            if companhia_selecionada == "Todas":
                                cursor.execute("DELETE FROM escala WHERE batalhao = ?", (batalhao_selecionado,))
                            else:
                                cursor.execute("DELETE FROM escala WHERE batalhao = ? AND companhia = ?", (batalhao_selecionado, companhia_selecionada))
                                
                            escala_gerada.to_sql('escala', conn, if_exists='append', index=False)
                            st.success(f"Escala gerada com sucesso!")
                            st.rerun()
                        
        with cc2:
            linhas_tabela = ""
            for idx, row in df_escala.iterrows():
                linhas_tabela += f"<tr><td>{row.iloc[0]}</td><td>{row.iloc[1]}</td><td>{row.iloc[2]}</td></tr>"
                
            brasao_src = obter_brasao_local()
            tag_imagem = f'<img class="brasao" src="{brasao_src}" alt="Brasão PMPI">' if brasao_src else ''
                
            html_escala = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; color: #000; margin: 20px; }}
                    .header {{ display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 20px; }}
                    .brasao {{ width: 80px; height: auto; max-height: 100px; }}
                    .header h1 {{ font-size: 15pt; margin: 0; text-transform: uppercase; font-weight: bold; text-align: center; }}
                    .title {{ text-align: center; font-size: 14pt; font-weight: bold; text-transform: uppercase; margin-top: 15px; margin-bottom: 20px; letter-spacing: 1px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                    th {{ background-color: #ffffff; color: #000; font-size: 11pt; font-weight: bold; text-transform: uppercase; padding: 8px; border: 1px solid #000; text-align: center; }}
                    td {{ padding: 8px; border: 1px solid #000; font-size: 11pt; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="header">
                    {tag_imagem}
                    <div>
                        <h1>{subtitulo_opm}</h1>
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
                file_name=f"escala_{batalhao_selecionado.split()[0].lower()}.html",
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

# -----------------------------------------------------------------
# TELA 2: VISÃO GERAL / DASHBOARD
# -----------------------------------------------------------------
with aba_visao_geral:
    st.title("📈 Visão Geral do Efetivo")
    
    df_todos = pd.read_sql_query("SELECT * FROM efetivo", conn)
    
    if df_todos.empty:
        st.info("Nenhum policial cadastrado no banco para exibir métricas.")
    else:
        # --- CARDS DE MÉTRICAS NO TOPO ---
        total_pms = len(df_todos)
        total_ativos = len(df_todos[df_todos['status'] == 'Ativo'])
        total_ferias = len(df_todos[df_todos['status'] == 'Férias'])
        total_indisponiveis = total_pms - total_ativos
        taxa_prontidao = round((total_ativos / total_pms) * 100, 1) if total_pms > 0 else 0
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Efetivo Total", f"{total_pms} PMs")
        m2.metric("Prontos p/ Serviço", f"{total_ativos} PMs", delta=f"{taxa_prontidao}% do Total")
        m3.metric("Em Férias", f"{total_ferias} PMs")
        m4.metric("Indisponíveis", f"{total_indisponiveis} PMs", delta_color="inverse")
        
        st.write("---")
        
        # --- LINHA 1 DE GRÁFICOS / TABELAS ---
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("📌 Efetivo por Batalhão / Unidade")
            df_bat = df_todos.groupby(['batalhao', 'status']).size().unstack(fill_value=0)
            st.bar_chart(df_bat)
            
        with col_g2:
            st.subheader("🎖️ Distribuição por Posto / Graduação")
            df_posto = df_todos['posto_graduacao'].value_counts().reset_index()
            df_posto.columns = ['Posto / Graduação', 'Quantidade']
            st.dataframe(df_posto, use_container_width=True, hide_index=True)

        st.write("---")

        # --- LINHA 2 DE GRÁFICOS / TABELAS ---
        col_g3, col_g4 = st.columns(2)
        
        with col_g3:
            st.subheader("🏢 Efetivo por Companhia / UISP")
            df_cia = df_todos['companhia'].value_counts().reset_index()
            df_cia.columns = ['Companhia / UISP', 'Total PMs']
            st.dataframe(df_cia, use_container_width=True, hide_index=True)
            
        with col_g4:
            st.subheader("🚦 Situação Atual do Efetivo")
            df_status = df_todos['status'].value_counts().reset_index()
            df_status.columns = ['Status', 'Total']
            st.dataframe(df_status, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------
# TELA 3: CADASTRO E EDIÇÃO DE PMs
# -----------------------------------------------------------------
with aba_cadastro:
    st.title("Gerenciamento do Efetivo")
    
    if st.button("🚀 Gerar Base Fictícia para Testes"):
        pms_ficticios = [
            ("101001-1", "Capitão (Cap)", "Silva", "Ativo", "1º BPM (Teresina - Centro/Zona Sul)", "1ª Cia: Centro Comercial"),
            ("101002-2", "1º Tenente (1º Ten)", "Oliveira", "Ativo", "1º BPM (Teresina - Centro/Zona Sul)", "1ª Cia: Centro Comercial"),
            ("101003-3", "1º Sargento (1º Sgt)", "Santos", "Ativo", "1º BPM (Teresina - Centro/Zona Sul)", "2ª Cia: Bairro Vermelha e Ilhotas"),
            ("101004-4", "2º Sargento (2º Sgt)", "Souza", "Férias", "1º BPM (Teresina - Centro/Zona Sul)", "2ª Cia: Bairro Vermelha e Ilhotas"),
            ("101005-5", "Cabo (Cb)", "Lima", "Ativo", "1º BPM (Teresina - Centro/Zona Sul)", "3ª Cia: Bairro Poti Velho / Primavera"),
            ("101006-6", "Soldado (Sd)", "Ferreira", "Ativo", "1º BPM (Teresina - Centro/Zona Sul)", "3ª Cia: Bairro Poti Velho / Primavera"),
            ("101007-7", "Major (Maj)", "Costa", "Ativo", "5º BPM (Teresina - Zona Leste)", "1ª Cia: Bairro Ininga e Jóquei"),
            ("101008-8", "3º Sargento (3º Sgt)", "Pereira", "Ativo", "5º BPM (Teresina - Zona Leste)", "1ª Cia: Bairro Ininga e Jóquei"),
            ("101009-9", "Soldado (Sd)", "Alves", "Afastado", "5º BPM (Teresina - Zona Leste)", "2ª Cia: Bairro Pedra Mole e Tabajaras"),
            ("101010-0", "Capitão (Cap)", "Rodrigues", "Ativo", "BOPE - Operações Especiais", "Sede Teresina"),
            ("101011-1", "1º Tenente (1º Ten)", "Nascimento", "Ativo", "BOPE - Operações Especiais", "Sede Teresina"),
            ("101012-2", "Cabo (Cb)", "Araújo", "Ativo", "BOPE - Operações Especiais", "Sede Teresina")
        ]
        
        cursor = conn.cursor()
        cont = 0
        for pm in pms_ficticios:
            try:
                cursor.execute("INSERT INTO efetivo (matricula, posto_graduacao, nome_guerra, status, batalhao, companhia) VALUES (?, ?, ?, ?, ?, ?)", pm)
                cont += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        st.success(f"{cont} PMs fictícios foram inseridos!")
        st.rerun()

    st.subheader("Cadastrar Novo Policial")
    
    c_unid, c_comp = st.columns(2)
    with c_unid:
        bat_cad = st.selectbox("1. Batalhão / Unidade de Lotação:", options=list(ESTRUTURA_PMPI.keys()), key="cad_bat")
    with c_comp:
        cias_disponiveis = ESTRUTURA_PMPI.get(bat_cad, ["Sede / Geral"])
        cia_cad = st.selectbox("2. Companhia / UISP Subordinada:", options=cias_disponiveis, key="cad_cia")

    with st.form("form_cadastro", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2, 3, 3, 2])
        
        with c1:
            nova_matricula = st.text_input("Matrícula (Ex: 102345-1)")
        with c2:
            novo_posto = st.selectbox("Posto / Graduação", options=LISTA_PATENTES)
        with c3:
            novo_nome = st.text_input("Nome de Guerra (Ex: Geovanio)")
        with c4:
            status_cadastro_visual = st.selectbox("Status Inicial", ["🟢 Ativo", "🟡 Férias", "🔴 Afastado", "🔵 Licença"])
            novo_status = status_cadastro_visual.split(" ")[1]
            
        botao_cadastrar = st.form_submit_button("Salvar Policial no Banco", type="primary")
        
        if botao_cadastrar:
            if nova_matricula and novo_nome:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO efetivo (matricula, posto_graduacao, nome_guerra, status, batalhao, companhia) VALUES (?, ?, ?, ?, ?, ?)",
                        (nova_matricula, novo_posto, novo_nome, novo_status, bat_cad, cia_cad)
                    )
                    conn.commit()
                    st.success(f"{novo_posto} {novo_nome} cadastrado com sucesso em {bat_cad} ({cia_cad})!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Erro: Já existe um policial cadastrado com esta Matrícula!")
            else:
                st.warning("Preencha todos os campos obrigatórios!")

    st.write("---")
    st.subheader("Efetivo Cadastrado")
    
    f_bat = st.selectbox("Filtrar Tabela por Batalhão:", options=["Todos"] + list(ESTRUTURA_PMPI.keys()))
    
    if f_bat == "Todos":
        df_gerenciar = pd.read_sql_query("SELECT * FROM efetivo", conn)
    else:
        df_gerenciar = pd.read_sql_query("SELECT * FROM efetivo WHERE batalhao = ?", conn, params=(f_bat,))
    
    if df_gerenciar.empty:
        st.info("Nenhum policial cadastrado para o filtro selecionado.")
    else:
        col_hdr_mat, col_hdr_posto, col_hdr_nome, col_hdr_unid, col_hdr_status, col_hdr_acao = st.columns([2, 2, 3, 4, 2, 3])
        with col_hdr_mat: st.markdown("**Matrícula**")
        with col_hdr_posto: st.markdown("**Posto/Grad.**")
        with col_hdr_nome: st.markdown("**Nome de Guerra**")
        with col_hdr_unid: st.markdown("**Unidade / Cia**")
        with col_hdr_status: st.markdown("**Status**")
        with col_hdr_acao: st.markdown("**Ações**")
        st.write("")

        mapeamento_status = {"Ativo": "🟢 Ativo", "Férias": "🟡 Férias", "Afastado": "🔴 Afastado", "Licença": "🔵 Licença"}

        for idx, row in df_gerenciar.iterrows():
            col_mat, col_posto, col_nome, col_unid, col_status, col_acao = st.columns([2, 2, 3, 4, 2, 3])
            
            with col_mat:
                st.write(row['matricula'])
                
            with col_posto:
                st.write(row['posto_graduacao'] if pd.notnull(row['posto_graduacao']) else '-')
                
            with col_nome:
                st.write(row['nome_guerra'])
                
            with col_unid:
                cia_str = f" ({row['companhia']})" if pd.notnull(row['companhia']) else ""
                st.write(f"{row['batalhao']}{cia_str}")
                
            with col_status:
                st.write(mapeamento_status.get(row['status'], row['status']))
                    
            with col_acao:
                c_edit, c_del = st.columns(2)
                with c_edit:
                    if st.button("✏️", key=f"edit_{row['id']}", help="Editar todos os dados do PM"):
                        modal_editar_policial(conn, row)
                with c_del:
                    if st.button("🗑️", key=f"del_{row['id']}", help="Remover PM do banco"):
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM efetivo WHERE id = ?", (row['id'],))
                        conn.commit()
                        st.success("Policial removido!")
                        st.rerun()