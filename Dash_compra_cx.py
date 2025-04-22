import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import textwrap
import time

# Configuração da API do Jira
JIRA_URL = "https://carboncars.atlassian.net/rest/api/2/search"
JIRA_USERNAME = "henrique.degan@oatsolutions.com.br"
JIRA_API_TOKEN = "b4mAs0sXJCx3101YvgkhBD3F"  # Recomendo usar variáveis de ambiente

# Função para buscar dados do Jira
def fetch_jira_data(jql_query):
    headers = {"Accept": "application/json"}
    auth = (JIRA_USERNAME, JIRA_API_TOKEN)
    params = {
        "jql": jql_query, 
        "fields": "key,summary,created,priority,customfield_11069,customfield_11070,customfield_11610,customfield_11141"
    }
    try:
        response = requests.get(JIRA_URL, headers=headers, auth=auth, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro na API Jira (Status {response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro na conexão com o Jira: {str(e)}")
        return None

# Mapeamento dos dias da semana de inglês para português
DIA_DA_SEMANA_PT = {
    "MON": "SEG",
    "TUE": "TER",
    "WED": "QUA",
    "THU": "QUI",
    "FRI": "SEX",
    "SAT": "SAB",
    "SUN": "DOM"
}

# Consultas JQL
queries = {
    "AGUARDANDO COMPRA CX": 'project = PB AND status = "Aguardando Compra CX" ORDER BY cf[11141] ASC',
    "FAZENDO COMPRA CX": 'project = PB AND status = "Fazendo Compra CX" ORDER BY cf[11141] ASC',
    "REPROVADO COMPRA CX": 'status = "Reprovado Compra CX" AND project = PB ORDER BY cf[11141] ASC',
    "AGUARDANDO EXÉRCITO": 'project = PB AND status = "130 - Aguardando Exército" AND type IN ("Produção Blindados", "Produção Blindados - QA") ORDER BY cf[11141] ASC',
    "AGUARDANDO TRANSFER TAMBAQUI ARUANÃ": 'project = PB AND type IN ("Produção Blindados", "Produção Blindados - QA") AND status = "120 - Aguardando Transfer Tambaqui-Aruanã" ORDER BY cf[11141] ASC'
}

# Layout do Streamlit
st.set_page_config(page_title="Status de Compras", layout="wide")

# CSS personalizado
st.markdown("""
<style>
.card {
    width: 100px;
    height: 100px; /* Aumentado para acomodar o novo campo */
    background-color: #d1e7dd; /* Verde claro padrão */
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 3px;
    text-align: center;
    font-size: 15px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    line-height: 1.2;
    margin-right: 10px;
    border: 3px solid black;
}
.card p {
    margin: 0;
    word-wrap: break-word;
    white-space: normal;
    font-weight: bold; /* Negrito padrão */
    font-size: 10px;   /* Tamanho padrão */
}
.card .summary {
    font-size: 20px; /* Tamanho maior para o summary */
}
.card .vaga {
    font-size: 18px; /* Tamanho maior para a vaga */
}
.circle-count-inline {
    width: 60px; /* Largura do círculo */
    height: 60px; /* Altura do círculo */
    color: black; /* Cor do texto (preto) */
    border-radius: 50%; /* Transforma o quadrado em um círculo */
    display: inline-flex; /* Alinha o conteúdo internamente */
    align-items: center; /* Centraliza verticalmente */
    justify-content: center; /* Centraliza horizontalmente */
    font-size: 25px; /* Tamanho da fonte */
    font-weight: bold; /* Negrito */
    vertical-align: middle; /* Alinha o círculo com outros elementos */
    margin-top: 35px; /* Ajusta a posição vertical para alinhar com os cards */
    border: 3px solid black; /* Adiciona uma borda preta ao redor do círculo */
    background-color: transparent; /* Fundo transparente */
}
.section-title {
    background-color: black;
    color: white;
    padding: 10px 20px;
    font-size: 18px;
    font-weight: bold;
    text-align: left;
    margin-bottom: 10px;
    margin-top: 20px;
}
.cards-row {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}
.footer {
    text-align: center;
    font-size: 18px;
    color: black;
    padding: 10px;
    border-top: 1px solid #ddd;
    position: fixed; /* Fixa o rodapé */
    bottom: 0; /* Alinha ao fundo da janela */
    left: 0; /* Alinha à esquerda */
    width: 100%; /* Ocupa toda a largura da janela */
    background-color: white; /* Fundo branco para melhor legibilidade */
    z-index: 1000; /* Garante que o rodapé fique acima de outros elementos */
}
</style>
""", unsafe_allow_html=True)

# Função para determinar a cor com base na diferença de dias
def get_background_color(contract_date):
    try:
        # Verifica se a data do contrato é válida
        if not contract_date or contract_date == "N/A":
            return "#ffffff"  # Branco (caso a data do contrato seja inválida ou ausente)
        
        # Converte a data do contrato para um objeto datetime
        contract_dt = datetime.strptime(contract_date[:10], "%Y-%m-%d")
        today = datetime.now()
        
        # Calcula a diferença em dias
        delta = (contract_dt - today).days
        
        # Debug: Exibir a diferença de dias no console
        #st.write(f"Diferença de dias: {delta} (Contrato: {contract_dt}, Hoje: {today})")
        
        # Define a cor com base nas regras
        if delta > 5:
            return "#c4e4b4"  # Verde
        elif 3 <= delta <= 5:
            return "#fff3cd"  # Laranja
        elif 0 <= delta <= 2:
            return "#f8d7da"  # Vermelho
        else:  # delta < 0 (data já passou)
            return "#946cec"  # Roxo
    except Exception as e:
        st.error(f"Erro ao processar data do contrato: {str(e)}")
        return "#ffffff"  # Branco (caso ocorra algum erro)

# Buscar e processar dados
@st.cache_data(ttl=60)  # Cache de 1 minuto
def get_jira_data():
    dataframes = {}
    for status, query in queries.items():
        response = fetch_jira_data(query)
        if response and "issues" in response:
            issues = response["issues"]
            data = []
            for issue in issues:
                try:
                    row = {
                        "Ticket ID": issue["key"],
                        "OS/PD": issue["fields"]["summary"][:20] + "..." if len(issue["fields"]["summary"]) > 20 else issue["fields"]["summary"],
                        "Marca": issue["fields"].get("customfield_11069", "N/A"),
                        "Modelo": issue["fields"].get("customfield_11070", "N/A"),
                        "Prioridade": issue["fields"]["priority"]["name"],
                        "Vaga nº": issue["fields"].get("customfield_11610", "N/A"),
                        "Data": issue["fields"].get("created", ""),
                        "DT.Contrato": issue["fields"].get("customfield_11141", ""),  # Novo campo
                        "DT.Contrato_Formatted": "N/A",  # Campo para armazenar a data formatada
                    }
                    # Formatação da data de criação
                    if row["Data"]:
                        try:
                            dt = datetime.strptime(row["Data"][:10], "%Y-%m-%d")
                            row["Data"] = dt.strftime("%d %b. %a.")
                        except:
                            row["Data"] = "N/A"
                    else:
                        row["Data"] = "N/A"
                    # Formatação do DT.Contrato
                    if row["DT.Contrato"]:
                        try:
                            dt_contrato = datetime.strptime(row["DT.Contrato"][:10], "%Y-%m-%d")
                            dia_semana_en = dt_contrato.strftime("%a").upper()  # Dia da semana em inglês
                            dia_semana_pt = DIA_DA_SEMANA_PT.get(dia_semana_en, dia_semana_en)  # Tradução para português
                            row["DT.Contrato_Formatted"] = dt_contrato.strftime(f"%d %b {dia_semana_pt}").upper()  # Formato: dd MMM DIA DA SEMANA
                        except:
                            row["DT.Contrato_Formatted"] = "N/A"
                    else:
                        row["DT.Contrato_Formatted"] = "N/A"
                    data.append(row)
                except Exception as e:
                    continue
            dataframes[status] = pd.DataFrame(data) if data else pd.DataFrame()
        else:
            dataframes[status] = pd.DataFrame()
    return dataframes

# Exibição dos dados
dataframes = get_jira_data()
for status, df in dataframes.items():
    count = len(df)  # Calcula a quantidade de registros no DataFrame
    # Exibe o título da seção
    st.markdown(f"<div class='section-title'>{status}</div>", unsafe_allow_html=True)
    # Cria duas colunas: uma para o círculo e outra para os cards
    col_circle, col_cards = st.columns([1, 9])  # Proporção 1:9 (círculo menor, cards maiores)
    with col_circle:
        # Exibe o círculo com a quantidade
        st.markdown(
            f"""
            <div style='display: flex; justify-content: center;'>
                <div class='circle-count-inline'>{count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_cards:
        # Exibe os cards
        cols = st.columns(15)  # Divide os cards em 10 colunas
        if not df.empty:
            for i, (_, row) in enumerate(df.iterrows()):
                with cols[i % 10]:
                    marca = textwrap.fill(row['Marca'], width=10)
                    modelo = textwrap.fill(row['Modelo'], width=10)
                    # Adicionando o campo "Vaga nº" (customfield_11610)
                    vaga_numero = row.get('Vaga nº', 'N/A')  # Obtém o valor do campo ou define como "N/A"
                    # Garantindo que o valor seja um número inteiro sem ponto, se for numérico
                    if isinstance(vaga_numero, (int, float)) and not isinstance(vaga_numero, bool):
                        vaga_numero = int(vaga_numero)  # Converte para inteiro
                    elif vaga_numero == "N/A":
                        pass  # Mantém como "N/A"
                    else:
                        vaga_numero = str(vaga_numero)  # Converte para string, caso seja outro tipo
                    # Incluindo o campo DT.Contrato formatado
                    dt_contrato_formatted = row.get('DT.Contrato_Formatted', 'N/A')
                    dt_contrato_original = row.get('DT.Contrato', 'N/A')
                    
                    # Determina a cor de fundo com base na data do contrato
                    background_color = get_background_color(dt_contrato_original)
                    
                    st.markdown(
                        f"""
                        <div class='card' style='background-color: {background_color};'>
                            <p class='summary'>{row['OS/PD']}</p> <!-- Classe 'summary' para o summary -->
                            <!--<p>{marca if marca else 'N/A'}</p>-->
                            <p>{modelo if modelo else 'N/A'}</p>
                            <p></strong> {dt_contrato_formatted}</p> <!-- Campo DT.Contrato formatado -->
                            <p class='vaga'>{vaga_numero}</p> <!-- Classe 'vaga' para o campo "Vaga nº" -->
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# Rodapé e atualização automática
st.markdown(
    f"<div class='footer'>Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>",
    unsafe_allow_html=True,
)
progress_bar = st.progress(0)
for seconds in range(60):
    time.sleep(1)
    progress_bar.progress((seconds + 1) / 60)
st.rerun()