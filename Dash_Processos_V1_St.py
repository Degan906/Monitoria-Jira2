import streamlit as st
from jira import JIRA
import pandas as pd
from datetime import datetime, timedelta
import time  # Importar o módulo time

# Configurar o layout da página
st.set_page_config(layout="wide")

# Inicializar o estado da sessão
if 'search_term' not in st.session_state:
    st.session_state.search_term = ""
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")  # Data/hora inicial

# Configurações do Jira
jira_url = "https://carboncars.atlassian.net"
email = "henrique.degan@oatsolutions.com.br"
api_token = "b4mAs0sXJCx3101YvgkhBD3F"

# Lista ordenada dos status
status_order = [
    "AGUARDANDO ENTRADA",
    "AGUARDANDO LAVAGEM",
    "FAZENDO LAVAGEM",
    "AGUARDANDO CHECKLIST ENTRADA",
    "FAZENDO CHECKLIST ENTRADA",
    "REPARO EXTERNO ENTRADA",
    "RECEBIDO NÃO ENCAMINHADO EXÉRCITO",
    "RECEBIDO ENCAMINHADO EXÉRCITO",
    "RECEBIDOS LIBERADOS",
    "AGUARDANDO DESENVOLVIMENTO",
    "FAZENDO DESENVOLVIMENTO",
    "DESENVOLVIMENTO FINALIZADO",
    "RECEBIDOS LIBERADOS COM VAM",
    "AGUARDANDO DESMONTAGEM",
    "DESMONTANDO"
]

# Função para conectar ao Jira
def connect_to_jira():
    try:
        jira = JIRA(server=jira_url, basic_auth=(email, api_token))
        return jira
    except Exception as e:
        st.error(f"Erro ao conectar ao Jira: {e}")
        return None

# Query JQL
jql_queries = {
    "AGUARDANDO ENTRADA": 'project = AP AND type = Recebimento AND status = "Aguardando entrada"',
    "AGUARDANDO LAVAGEM": 'project = AP AND type = Recebimento AND status = "Aguardando lavagem"',
    "FAZENDO LAVAGEM": 'project = AP AND type = Recebimento AND status = "Em lavagem"',
    "AGUARDANDO CHECKLIST ENTRADA": 'project = AP AND type = Recebimento AND status = "Aguardando checklist entrada"',
    "FAZENDO CHECKLIST ENTRADA": 'project = AP AND type = Recebimento AND status = "Fazendo check-In"',
    "REPARO EXTERNO ENTRADA": 'project = AP AND type = Recebimento AND status = "Reparo Externo" ORDER BY created DESC',
    "RECEBIDO NÃO ENCAMINHADO EXÉRCITO": 'project = AP AND type = Recebimento AND status = "Recebido com Pendencias" ORDER BY created DESC',
    "RECEBIDO ENCAMINHADO EXÉRCITO": 'project = AP AND type = Recebimento AND status = "Recebido encaminhado Exército" ORDER BY created DESC',
    "RECEBIDOS LIBERADOS": 'project = PB AND type IN ("Produção Blindados", "Produção Blindados - QA") AND status = "1 - Recebidos Liberados"',
    "AGUARDANDO DESENVOLVIMENTO": 'project = PB AND status = "Aguardando desenvolvimento" ORDER BY created DESC',
    "FAZENDO DESENVOLVIMENTO": 'project = PB AND status = "Fazendo Desenvolvimento" ORDER BY created DESC',
    "DESENVOLVIMENTO FINALIZADO": 'project = PB AND status = "Desenvolvimento Finalizado" ORDER BY created DESC',
    "RECEBIDOS LIBERADOS COM VAM": 'project = PB AND status = "2 - Recebidos com VAM" ORDER BY created DESC',
    "AGUARDANDO DESMONTAGEM": 'project = PB AND status = "3 - Aguardando Desmontagem" ORDER BY created DESC',
    "DESMONTANDO": 'project = PB AND status = "3.1 - Desmontando" ORDER BY created DESC',
}

# Campos da API Jira
fields_to_fetch = [
    "summary", "labels", "status", "created", "project", "customfield_10256", "customfield_11298",
    "customfield_11069", "customfield_11070", "customfield_10038", "customfield_10257",
    "customfield_11040", "customfield_11333", "customfield_11496", "customfield_11332",
    "customfield_11328", "customfield_11141", "customfield_10039", "customfield_10253", "customfield_11504", "customfield_12668"
]

# Função para calcular os dias corridos até a entrega (data do contrato)
def calculate_days_until_delivery(contract_date):
    """
    Calcula os dias corridos da data atual até a Data do Contrato (dias restantes).
    :param contract_date: Data do contrato (datetime ou string no formato 'YYYY-MM-DD')
    :return: Número de dias corridos até a entrega (positivo se no futuro, 0 se já passou)
    """
    if not contract_date:
        return "N/A"
    try:
        if isinstance(contract_date, str):
            contract_date = datetime.strptime(contract_date.split("T")[0], "%Y-%m-%d")
        current_date = datetime.now()
        days_difference = (contract_date - current_date).days
        return max(days_difference, 0)  # Retorna 0 se a data do contrato já passou
    except Exception as e:
        return "Erro"

# Função para formatar a data no formato dd/MM/aa hh:mm
def format_date(created_date):
    """
    Formata a data no formato dd/MM/aa hh:mm.
    :param created_date: Data original (string ou datetime)
    :return: Data formatada no formato dd/MM/aa hh:mm
    """
    if not created_date:
        return "N/A"
    try:
        if isinstance(created_date, str):
            # Converter a string para datetime
            created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S.%f%z")
        # Formatar para o padrão desejado
        formatted_date = created_date.strftime("%d/%m/%y %H:%M")
        return formatted_date
    except Exception as e:
        return "Erro"

# Buscar todos os tickets com suporte a busca
def fetch_filtered_issues(jira_instance, jql_query, search_term=None):
    # Dividir a consulta JQL em duas partes: condições e ORDER BY
    if "ORDER BY" in jql_query:
        base_query, order_by_clause = jql_query.split("ORDER BY", 1)
        order_by_clause = "ORDER BY " + order_by_clause.strip()
    else:
        base_query = jql_query
        order_by_clause = ""
    # Adicionar o termo de busca à parte principal da consulta
    if search_term:
        base_query += f' AND summary ~ "{search_term}"'
    # Reconstruir a consulta final com ORDER BY, se existir
    final_jql_query = base_query
    if order_by_clause:
        final_jql_query += " " + order_by_clause
    # Executar a consulta JQL
    block_size = 50
    block_start = 0
    all_issues = []
    while True:
        issues = jira_instance.search_issues(
            final_jql_query,
            startAt=block_start,
            maxResults=block_size,
            fields=fields_to_fetch
        )
        if not issues:
            break
        all_issues.extend(issues)
        block_start += block_size
    return all_issues

# Criar cards com espaçamento de 5mm
def create_card(issue, status):
    labels = issue.fields.labels
    imagens = {
        "V": "https://i.ibb.co/8gL1KfrR/V.png",
        "A": "https://i.ibb.co/67TFjyrn/A.png",
        "M": "https://i.ibb.co/9kHcRJH0/M.png",
        "E": "https://i.ibb.co/S4jr8vvW/E.png",
        "O": "https://i.ibb.co/Z6T2DJT8/O.png",
        "T": "https://i.ibb.co/rKXbM7yW/T.png",
        "S": "https://i.ibb.co/W4KyB5rp/S1.png"
    }
    imagens_to_display = [imagens[label] for label in labels if label in imagens]
    # Handle the case where there are no labels
    if not imagens_to_display:
        images_html = "<p style='font-size: 10px; text-align: center;'> </p>"
    else:
        images_html = ''.join([f'<img src="{img}" style="width: 12px; height: 12px; margin: 0,5px;">' for img in imagens_to_display])
    custom_field_value = getattr(issue.fields, 'customfield_11298', 'N/A')
    # Calcular os dias corridos até a entrega
    contract_date = getattr(issue.fields, 'customfield_11141', None)  # Data de Contrato
    if contract_date:
        try:
            # Formata a data do contrato para exibição
            formatted_contract_date = datetime.strptime(contract_date.split("T")[0], "%Y-%m-%d").strftime("%d/%m/%y")
            # Calcula os dias restantes até o contrato
            days_difference = calculate_days_until_delivery(contract_date)
        except Exception as e:
            formatted_contract_date = "Erro ao formatar"
            days_difference = "Erro"
    else:
        formatted_contract_date = "N/A"
        days_difference = "N/A"
    # Determinar a cor de fundo do card
    background_color = "#A8A8A8"  # Cor padrão (cinza)
    if status_order.index(status) > status_order.index("RECEBIDO NÃO ENCAMINHADO EXÉRCITO"):
        background_color = "#28a745"  # Verde para status posteriores
    # Verificar se os dias para entrega são menores que 25
    if isinstance(days_difference, int) and days_difference < 25:
        background_color = "#dc3545"  # Vermelho para alerta
    # Verificar o campo JSW_RNC-Vidro (customfield_12668)
    jsw_rnc_vidro = getattr(issue.fields, 'customfield_12668', None)
    border_style = "1px solid black"  # Borda padrão
    if jsw_rnc_vidro:  # Se o campo não estiver vazio
        border_style = "3px solid orange"  # Borda laranja mais grossa
    tooltip_text = f"""
    Key - Jira: {issue.key}
    OS: {issue.fields.summary}
    Veiculo Marca/Modelo: {custom_field_value}
    VAMEO: {', '.join(labels)}
    Criado: {format_date(issue.fields.created)}  
    Project: {issue.fields.project.name}
    OS/PD: {issue.fields.customfield_10256 if hasattr(issue.fields, "customfield_10256") else "N/A"}
    Marca: {issue.fields.customfield_11069 if hasattr(issue.fields, "customfield_11069") else "N/A"}
    Modelo: {issue.fields.customfield_11070 if hasattr(issue.fields, "customfield_11070") else "N/A"}
    Placa: {issue.fields.customfield_10253 if hasattr(issue.fields, "customfield_10253") else "N/A"}
    Veiculo (compras): {issue.fields.customfield_11504 if hasattr(issue.fields, "customfield_11504") else "N/A"}
    Cor: {issue.fields.customfield_10038 if hasattr(issue.fields, "customfield_10038") else "N/A"}
    Chassi: {issue.fields.customfield_10257 if hasattr(issue.fields, "customfield_10257") else "N/A"}
    Blindagem: {issue.fields.customfield_11040 if hasattr(issue.fields, "customfield_11040") else "N/A"}
    Data de Contrato: {formatted_contract_date}
    Prazo Contrato: {issue.fields.customfield_11328 if hasattr(issue.fields, "customfield_11328") else "N/A"}
    Situação: {issue.fields.customfield_10039 if hasattr(issue.fields, "customfield_10039") else "N/A"}
    Dias para entrega: {days_difference}
    """
    st.markdown(
        f"""
        <div style="
            width: 110px; 
            height: 60px; 
            background-color: {background_color}; 
            border-radius: 3px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            flex-direction: column; 
            overflow: hidden; 
            padding: 1px; 
            margin: 5px;
            box-sizing: border-box;
            border: {border_style};
        " title="{tooltip_text}">
            <p style="font-size: 16px; font-weight: bold; margin: 0; text-align: center;">{issue.fields.customfield_10256}</p>
            <div style="display: flex; gap: 2px; justify-content: center;">
                {images_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Função principal
def main():
    # Conectar ao Jira
    jira = connect_to_jira()
    if not jira:
        return
    # Atualizar o campo "Última atualização"
    st.session_state.last_update_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    # Exibir a data/hora da última atualização no canto superior direito
    col1, col2 = st.columns([10, 1])
    with col1:
        st.markdown(
            "<h1 style='text-align: center; font-weight: bold;'>CARBON PRODUÇÃO</h1>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<div style='text-align: right; font-size: 14px; color: gray;'>Última atualização: {st.session_state.last_update_time}</div>",
            unsafe_allow_html=True
        )
    # Campo de busca e botão
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Buscar por OS/PD:", placeholder="Digite aqui...", key="search_input")
    with col2:
        buscar_button = st.button("Buscar")
    # Atualizar o estado da sessão quando o botão for clicado
    if buscar_button:
        st.session_state.search_term = search_term
    # Filtrar tickets com base no termo de busca
    total_issues = 0
    status_to_issues = {}
    for status, jql_query in jql_queries.items():
        issues = fetch_filtered_issues(jira, jql_query, st.session_state.search_term)
        total_issues += len(issues)
        status_to_issues[status] = issues
    # Achatar a lista de issues de todos os status
    all_issues_flat = [issue for issues_list in status_to_issues.values() for issue in issues_list]
    # Remover duplicatas com base no campo 'key'
    unique_issues = {issue.key: issue for issue in all_issues_flat}.values()
    # Exibir o total de veículos no topo da tela, centralizado
    st.markdown(
        f"<h2 style='text-align: center;'>TOTAL DE VEÍCULOS ({len(unique_issues)})</h2>",
        unsafe_allow_html=True
    )
    # Renderizar os cards
    for status in status_order:
        issues_for_status = status_to_issues.get(status, [])
        # Remover duplicatas com base no campo 'key'
        unique_issues_for_status = {issue.key: issue for issue in issues_for_status}.values()
        # Adicionar uma divisória visual antes de cada status
        st.markdown(
            f"""
            <div style="
                border-top: 2px solid #000000; 
                margin: 10px 0; 
                padding-top: 10px;
            ">
                <h3>{status} ({len(unique_issues_for_status)})</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        # Container com colunas e espaçamento de 10px
        num_columns = 15
        cols_container = st.container()
        with cols_container:
            cols = st.columns(num_columns)
            for i, issue in enumerate(unique_issues_for_status):
                with cols[i % num_columns]:
                    create_card(issue, status)
    # Botão de exportação
    if st.button("Exportar para Excel"):
        data = []
        for status, jql_query in jql_queries.items():
            issues = fetch_filtered_issues(jira, jql_query)
            for issue in issues:
                contract_date = getattr(issue.fields, 'customfield_11141', None)
                days_until_delivery = calculate_days_until_delivery(contract_date) if contract_date else "N/A"
                data.append({
                    "Key": issue.key,
                    "OS/PD": issue.fields.customfield_10256 if hasattr(issue.fields, "customfield_10256") else "N/A",
                    "Summary": issue.fields.summary,
                    "Status": issue.fields.status.name,
                    "Veiculo": getattr(issue.fields, 'customfield_11298', 'N/A'),
                    "VAMEO": ', '.join(issue.fields.labels),
                    "Data Contrato": contract_date.split("T")[0] if contract_date else "N/A",
                    "Dias para Entrega": days_until_delivery,
                    "Placa": issue.fields.customfield_10253 if hasattr(issue.fields, "customfield_10253") else "N/A",
                    "Chassi": issue.fields.customfield_10257 if hasattr(issue.fields, "customfield_10257") else "N/A"
                })
        df = pd.DataFrame(data)
        file_path = "issues_export.xlsx"
        df.to_excel(file_path, index=False)
        st.success(f"Arquivo exportado para {file_path}")
    # Forçar a atualização automática a cada 60 segundos
    time.sleep(300)  # Aguardar 60 segundos
    st.rerun()  # Reiniciar o script

if __name__ == "__main__":
    main()