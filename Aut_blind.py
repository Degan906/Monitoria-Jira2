#24/04/25 - V1 -  Desenvolvido por Degan
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import textwrap
import time
import webbrowser
import json
import os
from pytz import timezone  # Importa o módulo de fuso horário

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
        "fields": "key,summary,created,priority,customfield_11069,customfield_11070,customfield_11610,customfield_11141,labels,project,customfield_10256,customfield_10253,customfield_11504,customfield_10038,customfield_10257,customfield_11040",
        "startAt": 0,  # Inicializa o índice de início
        "maxResults": 100  # Define o número máximo de resultados por página
    }
    all_issues = []  # Lista para armazenar todos os issues
    try:
        while True:
            response = requests.get(JIRA_URL, headers=headers, auth=auth, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])
                total = data.get("total", 0)  # Total de issues correspondentes à consulta
                all_issues.extend(issues)  # Adiciona os issues da página atual à lista
                # Verifica se há mais issues para buscar
                if len(all_issues) >= total:
                    break  # Sai do loop quando todos os issues forem recuperados
                # Atualiza o índice de início para a próxima página
                params["startAt"] += params["maxResults"]
            else:
                st.error(f"Erro na API Jira (Status {response.status_code}): {response.text}")
                return None
    except Exception as e:
        st.error(f"Erro na conexão com o Jira: {str(e)}")
        return None
    return {"issues": all_issues}  # Retorna todos os issues coletados

# Função para formatar data
def format_date(date_str):
    if not date_str:
        return "N/A"
    try:
        dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return date_str

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
    "AG ANÁLISE": 'project = DOC and type in ("Declaração de Blindagem", "Autorização de Blindagem") and status = "Aguardando análise"',
    "AG VENDA FINAL": 'project = DOC and type in ("Declaração de Blindagem", "Autorização de Blindagem") and status = "Aguardando venda final"',
    "AG DESPACHANTE": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Aguardando Despachante" ORDER BY Rank ASC',
    "AG NF ORIGEM": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Aguardando NF Origem" ORDER BY Rank ASC',
    "AG NF VENDA": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Aguardando NF Venda" ORDER BY Rank ASC',
    "AG DOCS CLIENTE": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Aguardando Docs Cliente" ORDER BY Rank ASC',
    "EMISSÃO IDONEIDADE PROACTA": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Aguardando Emissão Idoneidade Proacta" ORDER BY Rank ASC',
    "PENDENTE CR/ACESSO SICOVAB": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Pendente CR/ Acesso ao Sicovab" ORDER BY Rank ASC',
    "E-MAIL ENVIADO AO CLIENTE": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "E-mail Enviado ao Cliente" ORDER BY Rank ASC',
    "AG CERTIDÃO CLIENTE": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Aguardando Certidão Cliente" ORDER BY Rank ASC',
    "AG CERTIDÃO PROACTA": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Aguardando Certidão Proacta" ORDER BY Rank ASC',
    "PENDENTE CRLV": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Pendente CRLV" ORDER BY Rank ASC',
    "DOC OK": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Documentação OK" ORDER BY Rank ASC',
    "SOLICITADO AB/DB": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Solicitado AB/DB - Assessoria" ORDER BY Rank ASC',
    "ENCAMINHADO AB/DB AO EXÉRCITO": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Encaminhado AB/DB ao Exercito" ORDER BY Rank ASC',
    "AB/DB CONCLUÍDA": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "AB Concluida" ORDER BY Rank ASC',
    "TENTATIVA DE CONTATO": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "AB Concluida" ORDER BY Rank ASC',
    "REPARO EXTERNO": 'project = DOC AND type IN ("Declaração de Blindagem", "Autorização de Blindagem") AND status = "Reparo Externo" ORDER BY Rank ASC',
}

# Arquivo para armazenar as credenciais
CREDENTIALS_FILE = "credentials.json"

# Função para carregar credenciais
def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r") as f:
                return json.load(f)
        except:
            return {
                "henrique.degan": "12345",
                "vinicius.herrera": "12345",
                "dante.labate": "12345",
                "marcelo.lopes": "Carbon@25",
                "elizabeth.galoni": "Carbon@25"
            }
    else:
        # Credenciais padrão
        default_credentials = {
            "henrique.degan": "12345",
            "vinicius.herrera": "12345",
            "dante.labate": "12345"
        }
        # Salva as credenciais padrão
        save_credentials(default_credentials)
        return default_credentials

# Função para salvar credenciais
def save_credentials(credentials):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(credentials, f)

# Layout do Streamlit
st.set_page_config(page_title="Autorização de Blindagem", layout="wide")

# Adicionar o logo no canto superior esquerdo
st.markdown("""
    <div style="position: absolute; top: 5px; left: 5px;">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCx0Ywq0Bhihr0RLdHbBrqyuCsRLoV2KLs2g&s" 
             width="70" height="70">
    </div>
""", unsafe_allow_html=True)

# Título do dashboard
st.markdown("<h1 style='text-align: center;'>Autorização de Blindagem</h1>", unsafe_allow_html=True)

# CSS personalizado com espaçamento vertical aumentado e tooltip
st.markdown("""
<style>
.card {
    width: 120px;
    height: 120px;
    background-color: #696969; /* Cinza escuro padrão */
    border: 0px solid #ccc;
    border-radius: 5px;
    padding: 20px;
    text-align: center;
    font-size: 15px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    line-height: 1.2;
    margin-right: 20px;
    margin-bottom: 25px; /* Adicionado espaçamento vertical entre os cards */
    border: 3px solid black;
    position: relative; /* Necessário para o tooltip */
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
.card .label {
    font-size: 12px; /* Tamanho menor para o label */
    color: Snow;     /* Cor branca para o label */
}
/* Estilo para o tooltip */
.tooltip {
    visibility: hidden;
    width: 300px;
    background-color: #555;
    color: #fff;
    text-align: left;
    border-radius: 6px;
    padding: 10px;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    margin-left: -150px;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 12px;
    line-height: 1.4;
    white-space: pre-line;
}
.card:hover .tooltip {
    visibility: visible;
    opacity: 1;
}
.card:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Efeito de sombra ao passar o mouse */
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
    margin-bottom: 40px; /* Aumentado o espaçamento entre as linhas de cards */
}
/* Adiciona espaçamento vertical entre as seções de cards */
.stHorizontalBlock {
    margin-bottom: 20px;
}
/* Adiciona espaçamento vertical entre as colunas de cards */
.row-widget.stHorizontalBlock > div {
    margin-bottom: 25px;
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
/* Estilo para o botão de atualização */
.update-button {
    background-color: #4CAF50;
    color: white;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 10px 0;
    cursor: pointer;
    border-radius: 5px;
    border: none;
}
.update-button:hover {
    background-color: #45a049;
}
/* Centraliza o botão de atualização */
.button-container {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
}
/* Estilo para links dentro dos cards */
.card-link {
    display: block;
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
    z-index: 5;
}
</style>
""", unsafe_allow_html=True)

# Função para criar o texto do tooltip
def create_tooltip_text(issue):
    # Extrai os valores dos campos personalizados com tratamento para campos ausentes
    fields = issue.get("fields", {})
    # Extrai os valores com tratamento para campos ausentes
    key = issue.get("key", "N/A")
    summary = fields.get("summary", "N/A")
    created = format_date(fields.get("created", ""))
    # Campos personalizados
    modelo = fields.get("customfield_11070", "N/A")
    marca = fields.get("customfield_11069", "N/A")
    labels = ", ".join(fields.get("labels", [])) or "N/A"
    # Projeto
    project_name = fields.get("project", {}).get("name", "N/A") if fields.get("project") else "N/A"
    # Outros campos personalizados
    os_pd = fields.get("customfield_10256", "N/A")
    placa = fields.get("customfield_10253", "N/A")
    veiculo_compras = fields.get("customfield_11504", "N/A")
    cor = fields.get("customfield_10038", "N/A")
    chassi = fields.get("customfield_10257", "N/A")
    blindagem = fields.get("customfield_11040", "N/A")
    # Formata o texto do tooltip
    tooltip_text = f"Key - Jira: {key}\nOS: {summary}\nVeiculo Marca/Modelo: {marca} {modelo}\nVAMEO: {labels}\nCriado: {created}\nProject: {project_name}\nOS/PD: {os_pd}\nMarca: {marca}\nModelo: {modelo}\nPlaca: {placa}\nVeiculo (compras): {veiculo_compras}\nCor: {cor}\nChassi: {chassi}\nBlindagem: {blindagem}"
    return tooltip_text

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
    raw_issues = {}
    for status, query in queries.items():
        response = fetch_jira_data(query)
        if response and "issues" in response:
            issues = response["issues"]
            raw_issues[status] = issues
            data = []
            for issue in issues:
                try:
                    row = {
                        "Ticket ID": issue["key"],
                        "OS/PD": issue["fields"]["summary"][:20] + "..." if len(issue["fields"]["summary"]) > 20 else issue["fields"]["summary"],
                        "Modelo": issue["fields"].get("customfield_11070", "N/A"),
                        "Labels": ", ".join(issue["fields"].get("labels", [])) or "N/A",  # Processa os labels
                    }
                    data.append(row)
                except Exception as e:
                    continue
            dataframes[status] = pd.DataFrame(data) if data else pd.DataFrame()
        else:
            dataframes[status] = pd.DataFrame()
            raw_issues[status] = []
    return dataframes, raw_issues

# Tela de login
def login():
    credentials = load_credentials()
    st.markdown("""
    <div style="text-align: center; margin-top: 50px;">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCx0Ywq0Bhihr0RLdHbBrqyuCsRLoV2KLs2g&s" 
             width="150" height="150">
        <h1 style="font-size: 24px; margin-top: 20px;">Login</h1>
    </div>
    """, unsafe_allow_html=True)
    username = st.text_input("Usuário", key="username")
    password = st.text_input("Senha", type="password", key="password")
    if st.button("Entrar", type="primary"):
        if username in credentials and credentials[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["current_user"] = username
            st.success("Login bem-sucedido!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# Verificar se o usuário está logado
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login()
else:
    # Botão para atualização manual
    st.markdown("<div class='button-container'>", unsafe_allow_html=True)
    if st.button("Atualizar Dados", key="update_button", type="primary"):
        # Limpa o cache para forçar a atualização dos dados
        st.cache_data.clear()
        st.success("Dados atualizados com sucesso!")
    st.markdown("</div>", unsafe_allow_html=True)

    # Exibição dos dados
    dataframes, raw_issues = get_jira_data()
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
            cols = st.columns(10)  # Divide os cards em 10 colunas
            if not df.empty:
                for i, (_, row) in enumerate(df.iterrows()):
                    with cols[i % 10]:
                        ticket_id = row['Ticket ID']
                        modelo = textwrap.fill(row['Modelo'] if row['Modelo'] else "N/A", width=10)
                        labels = row['Labels']  # Obtém os labels formatados
                        # Encontra o issue correspondente para criar o tooltip
                        issue_data = next((issue for issue in raw_issues[status] if issue["key"] == ticket_id), None)
                        tooltip_text = create_tooltip_text(issue_data) if issue_data else "Informações não disponíveis"
                        # URL do Jira para o ticket
                        jira_url = f"https://carboncars.atlassian.net/browse/{ticket_id}"
                        # Cria um link clicável para o Jira
                        st.markdown(
                            f"""
                            <a href="{jira_url}" target="_blank" style="text-decoration: none; color: inherit;">
                                <div class='card'>
                                    <div class='tooltip'>{tooltip_text}</div>
                                    <p class='summary'>{row['OS/PD']}</p>
                                    <hr style='border: 1px solid black; margin: 5px 0;'> <!-- Linha adicionada -->
                                    <p>{modelo if modelo else 'N/A'}</p>
                                    <p class='label'>{labels}</p>
                                </div>
                            </a>
                            """,
                            unsafe_allow_html=True,
                        )
        # Adiciona um espaçador entre as seções
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # Rodapé com última atualização
    brazil_tz = timezone('America/Sao_Paulo')  # Define o fuso horário de Brasília
    current_time = datetime.now(brazil_tz).strftime('%d/%m/%Y %H:%M:%S')  # Obtém a data e hora no fuso horário correto
    st.markdown(
        f"<div class='footer'>Última atualização: {current_time}</div>",
        unsafe_allow_html=True,
    )

    # Atualização automática a cada 10 minutos
    progress_bar = st.progress(0)
    for seconds in range(600):
        time.sleep(1)
        progress_bar.progress((seconds + 1) / 600)
    st.rerun()
