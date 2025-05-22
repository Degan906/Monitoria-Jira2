# V4.7 - 09/04/2025 - Degan (Com Tooltips Funcionais)
# Adicionado as JQL de monitoria de Labels e tooltips funcionais
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import time
import pytz
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components


# Importação da função do Dashboard de Gestão
from dashboard_gestao import mostrar_dashboard_gestao

# Dicionário de tooltips para cada card
card_tooltips = {
   "⏫ Aço c/label": 'Verifica se há issues no projeto AP com o campo JSW_P-Aço marcado como "Done", com o label "A", e que ainda não foram canceladas. Útil para monitorar entregas finalizadas com etiqueta de aço. JQL: project = AP and JSW_P-Aço ~ Done and labels IN (A) AND status != Cancelado',
   "⏫ AP sem Aço": 'Verifica recebimentos no projeto AP que ainda estão em aberto (não resolvidos), foram criados após 01/05/2024 e que não possuem link com o tipo de item "P-Aço". Serve para identificar chamados que ainda não foram vinculados ao processo de aço. JQL: project = AP AND issuetype = Recebimento AND issueLinkType not in (P-Aço) AND created >= 2024-05-01 AND resolved IS EMPTY',
   "⏫ Ap Link Doc": 'Verifica recebimentos no projeto AP, criados após 01/05/2024 e ainda não resolvidos, que não possuem vínculo com os tipos de documentação "ADM-Documentações-AB" ou "Documentações". Útil para identificar chamados sem documentação obrigatória. JQL: project = AP AND issuetype = Recebimento AND issueLinkType not in (ADM-Documentações-AB, Documentações) AND created >= 2024-05-01 AND resolved IS EMPTY',
   "⏫ Ap Link Manta": 'Verifica recebimentos no projeto AP que foram criados após 01/05/2024, ainda não resolvidos, e que não possuem vínculo com o tipo de item "P-Manta". Serve para identificar chamados que não estão conectados ao processo de manta. JQL: project = AP AND issuetype = Recebimento AND issueLinkType not in (P-Manta) AND created >= 2024-05-01 AND resolved IS EMPTY',
   "⏫ Ap Link Pb": 'Verifica recebimentos no projeto AP com status "Produção PB", criados após 01/05/2024, que ainda não estão resolvidos e que não possuem link com o tipo "PB - Produção Blindados". Serve para identificar itens de produção que ainda não estão relacionados ao processo de PB. JQL: project = AP AND issuetype = Recebimento AND status = "Produção PB" AND issueLinkType not in ("PB - Produção Blindados") AND created >= 2024-05-01 AND resolved IS EMPTY',
   "⏫ Ap Link Svidro": 'Verifica recebimentos no projeto AP, não cancelados, criados após 01/05/2024, que ainda não estão resolvidos e que não possuem vínculo com o tipo de item "P-Suporte Vidro". Útil para detectar ausência de associação com o processo de suporte ao vidro. JQL: project = AP AND issuetype = Recebimento AND status != Cancelado AND issueLinkType not in ("P-Suporte Vidro") AND created >= 2024-05-01 AND resolved IS EMPTY',
   "⏫ Ap Link Vidro": 'Verifica chamados do tipo Recebimento no projeto AP criados após 01/05/2024 e não resolvidos, que não possuem vínculo com o tipo de link "P-Vidro". Identifica falhas no encadeamento com o processo de vidro. JQL: project = AP AND issuetype = Recebimento AND issueLinkType not in (P-Vidro) AND created >= 2024-05-01 AND resolved IS EMPTY',
   "⏫ Compras Supply": 'Monitora os chamados no projeto COM, criados após 01/07/2023, filtrados pelo ID "10549", que não possuem nenhum vínculo com outras issues (issueLinkType vazio). Serve para identificar itens de compras que ainda não foram relacionados a processos ou entregas. JQL: filter in ("10549") AND project = COM AND created >= 2023-07-01 AND issueLinkType = EMPTY',
   "⏫ Mantas Label": 'Verifica issues no projeto AP com o campo JSW_P-Manta marcado como "Done", com o label "M" e que não estejam canceladas. Ajuda a rastrear entregas de manta finalizadas e devidamente classificadas. JQL: project = AP and JSW_P-Manta ~ Done and labels IN (M) AND status != Cancelado',
   "⏫ Incidentes Proc": 'Monitora incidentes nos projetos JSM e SUPORTE do tipo "Incident" ou "Monitoria", com resolução ainda não definida, label de monitoramento ⚠️MONITORIA⚠️ e status na categoria "To Do". Útil para acompanhar incidentes abertos em fase inicial de análise. JQL: project IN (JSM, SUPORTE) AND type IN ("[System] Incident", Monitoria) AND resolution = Unresolved AND labels = ⚠️MONITORIA⚠️ and statusCategory = "To Do"',
   "⏫ Pb Instalando": 'Monitora chamados no projeto "Produção Blindados" com status "Instalando Vidro", já resolvidos, que possuem vínculos com os tipos "PB > VF" e "PB > VM". Ajuda a acompanhar instalações de vidro que já foram concluídas e vinculadas aos fluxos de montagem final e validação. JQL: project = "Produção Blindados" AND status = "Instalando Vidro" AND issueLinkType = "PB > VF" AND issueLinkType = "PB > VM" AND resolution = "Done" ORDER BY created DESC',
   "⏫ Pb Link Vl": 'Verifica chamados no projeto PB que já passaram pelo status "Definir Técnico Montagem", criados desde o início do ano anterior, e que ainda não possuem vínculo com o tipo de link "VAL". Útil para identificar chamados que não estão conectados ao fluxo de validação. JQL: project = PB AND status was "Definir Técnico Montagem" and issueLinkType not in (VAL) and created >= startOfYear(-1)',
   "⏫ Pb Contrato": 'Identifica chamados dos tipos "Produção Blindados" e "Produção Blindados - QA", filtrados pelo ID "10983", que ainda não possuem o campo DT.CONTRATO preenchido e não estão com status cancelado. Útil para monitorar pendências de registro contratual. JQL: filter in ("10983") AND type in ("Produção Blindados", "Produção Blindados - QA") AND DT.CONTRATO is EMPTY AND status != Cancelado',
   "⏫ Pb Ag Exercito": 'Monitora chamados no projeto PB com status "130 - Aguardando Exército" e que já possuem o campo "JSW_P-Validação (TM) - Done" preenchido. Indica veículos prontos para liberação militar, aguardando ação do Exército. JQL: project = PB and status = "130 - Aguardando Exército" and "JSW_P-Validação (TM) - Done" is not empty',
   "⏫ Pb Exercito Ok": 'Identifica chamados no projeto PB que estão com o status "131 - Exército Concluído". Serve para monitorar veículos que já passaram por toda a etapa de validação e liberação pelo Exército. JQL: project = PB and status = "131 - Exército Concluído"',
   "⏫ Pb Final Sem Val": 'Monitora chamados no projeto PB, filtrados pelo ID "10983", em que o campo "Veiculo Finalizado na Produção" está preenchido, mas o campo "12 - Aguardando Validações" ainda está vazio. Serve para identificar veículos finalizados que ainda não entraram na etapa de validação. JQL: filter in ("10983") AND project = PB AND "Veiculo Finalizado na Produção" is not EMPTY AND "12 - Aguardando Validações" is EMPTY',
   "⏫ Volvo Sem Tork": 'Verifica chamados resolvidos no projeto PBV da marca "VOLVO", exceto os modelos "EX30 SUV" e "C40 COUPE", que estão com o campo "Torque Vidro" vazio. Serve para identificar veículos Volvo entregues sem a informação de torque do vidro registrada. JQL: project = PBV AND resolution = Done AND "marca[short text]" ~ "VOLVO" AND "modelo[short text]" !~ "EX30 SUV" AND "Modelo[Short text]" !~ "C40 COUPE" AND "Torque Vidro[Radio Buttons]" IS EMPTY ORDER BY created DESC',
   "⏫ Pendencia Sem Os": 'Identifica chamados no projeto PD que estão com o campo "OS/PD" vazio. Serve para monitorar pendências que ainda não possuem número de ordem de serviço registrado. JQL: project = PD and "OS/PD[Short text]" IS EMPTY',
   "⏫ Svidro Label": 'Verifica chamados no projeto AP com o campo JSW_P-Svidro marcado como "Done", com o label "S" e que não estejam com status cancelado. Útil para acompanhar entregas finalizadas de suporte ao vidro com a devida classificação. JQL: project = AP and JSW_P-Svidro ~ Done and labels IN (S) AND status != Cancelado',
   "⏫ Tensylon Label": 'Verifica chamados no projeto AP com o campo JSW_P-Manta marcado como "Done", com o label "T" e que não estejam com status cancelado. Serve para monitorar entregas finalizadas relacionadas ao material Tensylon. JQL: project = AP and JSW_P-Manta ~ Done and labels IN (T) AND status != Cancelado',
   "⏫ Vidros Label": 'Monitora chamados no projeto AP com o campo JSW_P-Vidro marcado como "Done", com o label "V", não cancelados e com o campo "JSW_RNC-Vidro" ainda vazio. Indica entregas finalizadas de vidro que ainda não possuem registro de não conformidade. JQL: project = AP and JSW_P-Vidro ~ Done and labels IN (V) AND status != Cancelado and "JSW_RNC-Vidro[Short text]" IS EMPTY',
   "⏫ Rnc Sem Serial": 'Verifica chamados no projeto "Fábrica de Vidro" com tipo de card "RNC Produção" ou "RNC Assistência", criados a partir de 20/05/2025, que estão com todos os campos de serial em branco. Serve para identificar RNCs que não tiveram os dados de serial preenchidos. JQL: project = "Fábrica de Vidro" AND "Tipo Card[Select List (cascading)]" IN ("RNC Produção", "RNC Assistência") AND VGA-SERIAL IS EMPTY AND TSP-SERIAL IS EMPTY AND TSC-SERIAL IS EMPTY AND TSB-SERIAL IS EMPTY AND TSA-SERIAL IS EMPTY AND TME-SERIAL IS EMPTY AND TMD-SERIAL IS EMPTY AND QTE-SERIAL IS EMPTY AND QTD-SERIAL IS EMPTY AND QSE-SERIAL IS EMPTY AND QSD-SERIAL IS EMPTY AND QDE-SERIAL IS EMPTY AND QDD-SERIAL IS EMPTY AND PTE-SERIAL IS EMPTY AND PTD-SERIAL IS EMPTY AND PEE-SERIAL IS EMPTY AND PED-SERIAL IS EMPTY AND PDE-SERIAL IS EMPTY AND PDD-SERIAL IS EMPTY AND PBS-SERIAL IS EMPTY AND OPA-SERIAL IS EMPTY AND OLS-SERIAL IS EMPTY AND FTE-SERIAL IS EMPTY AND FTD-SERIAL IS EMPTY AND FDE-SERIAL IS EMPTY AND FDD-SERIAL IS EMPTY AND createdDate >= "2025-05-20"',
   "🔼  Ap Data Exercito": 'Verifica chamados do tipo Recebimento no projeto AP com status "Aguardando entrada", onde o campo "Data de Liberação do Exército" está preenchido e o resumo não contém a palavra "TESTE". Serve para monitorar entradas reais com liberação militar registrada. JQL: project = AP and issuetype = Recebimento and status = "Aguardando entrada" and "Data de Liberação do Exército[Date]" is not empty and summary !~ TESTE',
   "🔼  Incidentes Jira": 'Monitora incidentes nos projetos JSM e SUPORTE do tipo "[System] Incident", que ainda não foram resolvidos, estão na categoria de status "To Do" e têm o campo Sistema definido como "Jira". Serve para identificar incidentes pendentes relacionados à plataforma Jira. JQL: project IN (JSM, SUPORTE) AND type IN ("[System] Incident") AND resolution = Unresolved and statusCategory = "To Do" and Sistema = Jira',
   "🔼  Pb Passou 131": 'Identifica chamados no projeto PB que mudaram para o status "131 - Exército Concluído" após o início do ano e que ainda não possuem o campo "JSW_P-Validação (TM) - Done" preenchido. Serve para monitorar entregas concluídas pelo Exército, mas que ainda não foram validadas pelo time técnico. JQL: project = PB AND status changed to "131 - Exército Concluído" after startOfYear() and "JSW_P-Validação (TM) - Done" is empty',
   "🔼  Pb Prazo Contr": 'Monitora chamados dos tipos "Produção Blindados" e "Produção Blindados - QA" no projeto PB, criados a partir de 01/02/2024, que estão com o campo "Prazo Contrato" em branco. Serve para identificar demandas que ainda não possuem o prazo contratual definido. JQL: project = PB and type in ("Produção Blindados", "Produção Blindados - QA") and "Prazo Contrato[Short text]" is empty and created >= 2024-02-01',
   "🔽 Ap Pb Sem Veic": 'Verifica chamados nos projetos relacionados a VIDRO, MANTA, AÇO, SUPORTE VIDRO, CONJUNTO AÇO DO VIDRO, AP, PB e VL, criados nos últimos 120 dias, que ainda não possuem o campo "Veiculo - Marca/Modelo" preenchido, excluindo RNCs, avulsos, cancelados ou finalizados. Serve para identificar cards em aberto sem associação veicular obrigatória. JQL: filter in ("10549") AND (filter in ("10549") AND project in (VIDRO, MANTA, ACO, "SUPORTE VIDRO", "CONJUNTO AÇO DO VIDRO") AND "Veiculo - Marca/Modelo[Short text]" is EMPTY AND created >= -120d AND summary !~ RNC AND summary !~ AVULSA AND status not in (Cancelado) AND statusCategory != Done AND "Tipo Card[Select List (cascading)]" = "NÃO RNC" OR project in (AP, PB, VL) AND "veiculo - marca/modelo[short text]" is EMPTY AND resolution = Unresolved)',
   "🔽 Pb Sem Veiculo": 'Monitora chamados criados a partir de 01/07/2023 nos projetos PB e AP, filtrados pelo ID "10549", que ainda não possuem o campo "Veiculo - Marca/Modelo" preenchido e permanecem não resolvidos. Serve para identificar itens que ainda não foram associados a um veículo. JQL: filter in ("10549") AND created >= 2023-07-01 AND project in (PB, AP) AND "Veiculo - Marca/Modelo[Short text]" is EMPTY AND resolution = Unresolved',
   "🔽 Pb Ag Limpeza": 'Verifica chamados do tipo "Produção Blindados" no projeto PB que estão com o status "135 - Aguardando Limpeza QA1". Serve para identificar veículos prontos que aguardam a etapa de limpeza de qualidade. JQL: project = PB and status = "135 - Aguardando Limpeza QA1" and type = "Produção Blindados"',
   "🔽 Pb Final Toyota": 'Monitora chamados do tipo "Produção Blindados", filtrados pelo ID "10549", que estão com o status "6.3 - Finalizar Toyota" e com a "Tag Toyota" definida como TOYOTA. Serve para acompanhar a finalização de veículos da marca Toyota na produção. JQL: filter in ("10549") AND issuetype = "Produção Blindados" AND status = "6.3 - Finalizar Toyota" AND "Tag Toyota" = TOYOTA',
   "🔽 Posvenda Marca": 'Monitora chamados no projeto PV, filtrados pelo ID "10549", criados a partir de 25/08/2023, dos tipos "[System] Incident", "Sub-Task - Eletrônica", "Sub-Task - Estética" e "Sub-Task - Montagem", que estão sem o preenchimento do campo "Veiculo - Marca/Modelo" e permanecem não resolvidos. Serve para identificar registros de pós-venda sem associação a um veículo. JQL: filter in ("10549") AND project = PV AND issuetype in ("[System] Incident", "Sub-Task - Eletrônica", "Sub-Task - Estética", "Sub-Task - Montagem") AND created >= 2023-08-25 AND "Veiculo - Marca/Modelo[Short text]" is EMPTY AND resolution = Unresolved',
}

# Dicionário de links para cada card
card_links = {
    "AP-Sem link de DOC": "https://carboncars.atlassian.net/issues/?jql=project=AP",
    "AP-Sem link de VIDRO": "https://confluence.exemplo.com/vidro",
    "AP-Sem Link de AÇO": "https://confluence.exemplo.com/aco",
    "PB-Sem link de VL": "https://carboncars.atlassian.net/issues/?jql=project=PB",
    # Adicione os links reais para os demais cards conforme necessário
}

# Configuração da página
st.set_page_config(page_title="Monitoria", layout="wide")

# CSS para tooltips e animações
st.markdown("""
<style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 12px;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    .blinking-card {
        animation: blink 1s linear infinite;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        text-align: center;
        width: 100%;
        max-width: 100%;
        height: auto;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin: 10px;
    }
    @keyframes blink {
        0% { background-color: #ff3333; }
        50% { background-color: #ffff99; }
        100% { background-color: #ff3333; }
    }
</style>
""", unsafe_allow_html=True)

# Dicionário de usuários e senhas
USERS = {
    "admin": "omelhorchefedomundoevoce",
    "henrique.degan": "12345",
    "vinicius.herrera": "12345",
    "dante.labate": "12345"
}

# Função para buscar dados no Jira
@st.cache_data(ttl=60)  # Cache com tempo de vida de 60 segundos
def buscar_jira(jira_url, email, api_token, jql, max_results=100):
    headers = {
        "Accept": "application/json"
    }
    response = requests.get(
        f"{jira_url}/rest/api/2/search",
        headers=headers,
        auth=HTTPBasicAuth(email, api_token),
        params={
            "jql": jql,
            "maxResults": max_results
        }
    )
    return response

# Interface de login
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Login")
    st.markdown(
        """
        <style>
        .logo-container {
            display: flex;
            justify-content: center;
        }
        </style>
        <div class="logo-container">
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCx0Ywq0Bhihr0RLdHbBrqyuCsRLoV2KLs2g&s" width="150" height="150">
        </div>
        """, 
        unsafe_allow_html=True
    )
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    def authenticate_user(username, password):
        return USERS.get(username) == password

    if st.button("Entrar"):
        if authenticate_user(username, password):
            st.session_state.authenticated = True
            st.session_state.jira_url = "https://carboncars.atlassian.net"
            st.session_state.email = "henrique.degan@oatsolutions.com.br"
            st.session_state.api_token = "b4mAs0sXJCx3101YvgkhBD3F"
            st.success("Login bem-sucedido!")
        else:
            st.error("Nome de usuário ou senha incorretos.")
else:
    # Barra de status no topo da tela
    status_bar = st.empty()

    # Menu lateral
    st.sidebar.title("Menu")
    menu_option = st.sidebar.selectbox(
        "Escolha uma opção:",
        ["Dash de monitoria", "Dashs Gestão", "Relatorio Geral ITSM", "User List"]
    )

    st.sidebar.markdown("[Clique aqui para acessar as licenças](https://licencascarbonjira.streamlit.app/)")

    if menu_option == "Dash de monitoria":
        st.title("Dashboard de Monitoria")
        st.markdown("📄 **Link Confluence:** [https://carboncars.atlassian.net/wiki/spaces/CARBON/overview](https://carboncars.atlassian.net/wiki/spaces/CARBON/overview)")

        # Definir a JQL
        queries = {
            "🤖 AUTOMAÇÕES AP 🤖": {
                "⏫ Aço c/label": 'project = AP and JSW_P-Aço ~ Done and labels IN (A) AND status != Cancelado',
                "⏫ AP sem Aço": 'project = AP AND issuetype = Recebimento AND issueLinkType not in (P-Aço) AND created >= 2024-05-01 AND resolved IS EMPTY',
                "⏫ Ap Link Doc": 'project = AP AND issuetype = Recebimento AND issueLinkType not in (ADM-Documentações-AB, Documentações) AND created >= 2024-05-01 AND resolved IS EMPTY',
                "⏫ Ap Link Manta": 'project = AP AND issuetype = Recebimento AND issueLinkType not in (P-Manta) AND created >= 2024-05-01 AND resolved IS EMPTY',
                "⏫ Ap Link Pb": 'project = AP AND issuetype = Recebimento AND status = "Produção PB" AND issueLinkType not in ("PB - Produção Blindados") AND created >= 2024-05-01 AND resolved IS EMPTY',
                "⏫ Ap Link Svidro": 'project = AP AND issuetype = Recebimento AND status != Cancelado AND issueLinkType not in ("P-Suporte Vidro") AND created >= 2024-05-01 AND resolved IS EMPTY',
                "⏫ Ap Link Vidro": 'project = AP AND issuetype = Recebimento AND issueLinkType not in (P-Vidro) AND created >= 2024-05-01 AND resolved IS EMPTY',
                "⏫ Compras Supply": 'filter in ("10549") AND project = COM AND created >= 2023-07-01 AND issueLinkType = EMPTY',
                "⏫ Mantas Label": 'project = AP and JSW_P-Manta ~ Done and labels IN (M) AND status != Cancelado',
                "⏫ Incidentes Proc": 'project IN (JSM, SUPORTE) AND type IN ("[System] Incident", Monitoria) AND resolution = Unresolved AND labels = ⚠️MONITORIA⚠️ and statusCategory = "To Do"',
                "⏫ Pb Instalando": 'project = "Produção Blindados" AND status = "Instalando Vidro" AND issueLinkType = "PB > VF" AND issueLinkType = "PB > VM" AND resolution = "Done" ORDER BY created DESC',
                "⏫ Pb Link Vl": 'project = PB AND status was "Definir Técnico Montagem" and issueLinkType not in (VAL) and created >= startOfYear(-1)',
                "⏫ Pb Contrato": 'filter in ("10983") AND type in ("Produção Blindados", "Produção Blindados - QA") AND DT.CONTRATO is EMPTY AND status != Cancelado',
                "⏫ Pb Ag Exercito": 'project = PB and status = "130 - Aguardando Exército" and "JSW_P-Validação (TM) - Done" is not empty',
                "⏫ Pb Exercito Ok": 'project = PB and status = "131 - Exército Concluído"',
                "⏫ Pb Final Sem Val": 'filter in ("10983") AND project = PB AND "Veiculo Finalizado na Produção" is not EMPTY AND "12 - Aguardando Validações" is EMPTY',
                "⏫ Volvo Sem Tork": 'project = PBV AND resolution = Done AND "marca[short text]" ~ "VOLVO" AND "modelo[short text]" !~ "EX30 SUV" AND "Modelo[Short text]" !~ "C40 COUPE" AND "Torque Vidro[Radio Buttons]" IS EMPTY ORDER BY created DESC',
                "⏫ Pendencia Sem Os": 'project = PD and "OS/PD[Short text]" IS EMPTY',
                "⏫ Svidro Label": 'project = AP and JSW_P-Svidro ~ Done and labels IN (S) AND status != Cancelado',
                "⏫ Tensylon Label": 'project = AP and JSW_P-Manta ~ Done and labels IN (T) AND status != Cancelado',
                "⏫ Vidros Label": 'project = AP and JSW_P-Vidro ~ Done and labels IN (V) AND status != Cancelado and "JSW_RNC-Vidro[Short text]" IS EMPTY',
                "⏫ Rnc Sem Serial": 'project = "Fábrica de Vidro" AND "Tipo Card[Select List (cascading)]" IN ("RNC Produção", "RNC Assistência") AND VGA-SERIAL IS EMPTY AND TSP-SERIAL IS EMPTY AND TSC-SERIAL IS EMPTY AND TSB-SERIAL IS EMPTY AND TSA-SERIAL IS EMPTY AND TME-SERIAL IS EMPTY AND TMD-SERIAL IS EMPTY AND QTE-SERIAL IS EMPTY AND QTD-SERIAL IS EMPTY AND QSE-SERIAL IS EMPTY AND QSD-SERIAL IS EMPTY AND QDE-SERIAL IS EMPTY AND QDD-SERIAL IS EMPTY AND PTE-SERIAL IS EMPTY AND PTD-SERIAL IS EMPTY AND PEE-SERIAL IS EMPTY AND PED-SERIAL IS EMPTY AND PDE-SERIAL IS EMPTY AND PDD-SERIAL IS EMPTY AND PBS-SERIAL IS EMPTY AND OPA-SERIAL IS EMPTY AND OLS-SERIAL IS EMPTY AND FTE-SERIAL IS EMPTY AND FTD-SERIAL IS EMPTY AND FDE-SERIAL IS EMPTY AND FDD-SERIAL IS EMPTY AND createdDate >= "2025-05-20"',
                "🔼 Ap Data Exercito": 'project = AP and issuetype = Recebimento and status = "Aguardando entrada" and "Data de Liberação do Exército[Date]" is not empty and summary !~ TESTE',
                "🔼 Incidentes Jira": 'project IN (JSM, SUPORTE) AND type IN ("[System] Incident") AND resolution = Unresolved and statusCategory = "To Do" and Sistema = Jira',
                "🔼 Pb Passou 131": 'project = PB AND status changed to "131 - Exército Concluído" after startOfYear() and "JSW_P-Validação (TM) - Done" is empty',
                "🔼 Pb Prazo Contr": 'project = PB and type in ("Produção Blindados", "Produção Blindados - QA") and "Prazo Contrato[Short text]" is empty and created >= 2024-02-01',
                "🔽 Ap Pb Sem Veic": 'filter in ("10549") AND (filter in ("10549") AND project in (VIDRO, MANTA, ACO, "SUPORTE VIDRO", "CONJUNTO AÇO DO VIDRO") AND "Veiculo - Marca/Modelo[Short text]" is EMPTY AND created >= -120d AND summary !~ RNC AND summary !~ AVULSA AND status not in (Cancelado) AND statusCategory != Done AND "Tipo Card[Select List (cascading)]" = "NÃO RNC" OR project in (AP, PB, VL) AND "veiculo - marca/modelo[short text]" is EMPTY AND resolution = Unresolved)',
                "🔽 Pb Sem Veiculo": 'filter in ("10549") AND created >= 2023-07-01 AND project in (PB, AP) AND "Veiculo - Marca/Modelo[Short text]" is EMPTY AND resolution = Unresolved',
                "🔽 Pb Ag Limpeza": 'project = PB and status = "135 - Aguardando Limpeza QA1" and type = "Produção Blindados"',
                "🔽 Pb Final Toyota": 'filter in ("10549") AND issuetype = "Produção Blindados" AND status = "6.3 - Finalizar Toyota" AND "Tag Toyota" = TOYOTA',
                "🔽 Posvenda Marca": 'filter in ("10549") AND project = PV AND issuetype in ("[System] Incident", "Sub-Task - Eletrônica", "Sub-Task - Estética", "Sub-Task - Montagem") AND created >= 2023-08-25 AND "Veiculo - Marca/Modelo[Short text]" is EMPTY AND resolution = Unresolved',
            },
        }

        # Criar duas colunas para os botões
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Atualizar Dados"):
                st.cache_data.clear()
                st.rerun()

        with col2:
            if st.button("Exibir Issues Alarmadas"):
                st.session_state.show_alarmed_issues = True

        if st.session_state.get('show_alarmed_issues', False):
            st.subheader("Issues Alarmadas")
            alarmed_issues = []
            for query_name, jql in queries["🤖 AUTOMAÇÕES AP 🤖"].items():
                response = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql)
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get('issues', [])
                    if issues:
                        for issue in issues:
                            fields = issue.get('fields', {})
                            chave = f"{st.session_state.jira_url}/browse/{issue['key']}"
                            tipo = fields.get('issuetype', {}).get('name', 'N/A')
                            resumo = fields.get('summary', 'N/A')
                            criado = datetime.strptime(fields.get('created', ''), "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.timezone('America/Sao_Paulo'))
                            relator = fields.get('reporter', {}).get('displayName', 'N/A')
                            responsavel = fields.get('assignee', {}).get('displayName', 'N/A') if fields.get('assignee') else 'Não atribuído'
                            status = fields.get('status', {}).get('name', 'N/A')
                            resolucao = fields.get('resolution', {}).get('name', 'N/A') if fields.get('resolution') else 'N/A'
                            alarmed_issues.append({
                                "Chave": chave,
                                "Tipo": tipo,
                                "Resumo": resumo,
                                "Criado": criado,
                                "Relator": relator,
                                "Responsável": responsavel,
                                "Status": status,
                                "Resolução": resolucao
                            })
            if alarmed_issues:
                df_alarmed = pd.DataFrame(alarmed_issues)
                st.data_editor(
                    df_alarmed,
                    column_config={
                        "Chave": st.column_config.LinkColumn("Chave"),
                        "Criado": st.column_config.DatetimeColumn("Criado", format="DD/MM/YY HH:mm"),
                    },
                    hide_index=True,
                    use_container_width=True,
                    num_rows="dynamic",
                    disabled=True,
                    column_order=["Chave", "Tipo", "Resumo", "Criado", "Relator", "Responsável", "Status", "Resolução"]
                )
            else:
                st.info("Nenhuma issue alarmada encontrada.")

        results_placeholder = st.empty()

        if 'last_update_time' not in st.session_state:
            st.session_state.last_update_time = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")

        status_bar.markdown(
            f"""
            <div style="background-color: #f0f0f0; padding: 10px; text-align: center; border-radius: 5px; margin-bottom: 10px;">
                <strong>Última atualização:</strong> {st.session_state.last_update_time} <strong>V4.7</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        max_columns = 6
        num_columns = min(len(queries["🤖 AUTOMAÇÕES AP 🤖"]), max_columns)
        cols = results_placeholder.columns(num_columns)

        for col in cols:
            col.empty()

        # Renderizar todos os cards com tooltips
        for i, (query_name, jql) in enumerate(queries["🤖 AUTOMAÇÕES AP 🤖"].items()):
            response = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql)
            if response.status_code == 200:
                data = response.json()
                issue_count = data.get('total', 0)
                tooltip_text = card_tooltips.get(query_name, "Sem descrição disponível")
                card_link = card_links.get(query_name, "#")  # "#" se não houver link definido
                
                with cols[i % num_columns]:
                    if issue_count > 0:
                        st.markdown(
                            f"""
                            <div class="tooltip blinking-card">
                                <h5 style="font-size: 12px; margin: 0; padding: 0;">{query_name}</h5>
                                <h2 style="font-size: 20px; margin: 0; padding: 0;">{issue_count}</h2>
                                <span style="font-size: 12px; margin: 0; padding: 0;">Total de Tickets</span>
                                <span class="tooltiptext">{tooltip_text}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"""
                            <div class="tooltip" style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; text-align: center; width: 100%; max-width: 100%; height: auto; display: flex; flex-direction: column; justify-content: center; align-items: center; margin: 10px; background-color: #ffffff;">
                                <h5 style="font-size: 12px; margin: 0; padding: 0;">{query_name}</h5>
                                <h2 style="font-size: 20px; margin: 0; padding: 0;">{issue_count}</h2>
                                <span style="font-size: 12px; margin: 0; padding: 0;">Total de Tickets</span>
                                <span class="tooltiptext">{tooltip_text}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            else:
                st.error(f"Erro ao buscar dados do Jira para {query_name}: {response.status_code} - {response.text}")

        st.session_state.last_update_time = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")
        st.write("Aqui estão os dados do dashboard de monitoria...")

        time.sleep(60)
        st.rerun()

    elif menu_option == "Dashs Gestão":
        mostrar_dashboard_gestao(
            jira_url=st.session_state.jira_url,
            email=st.session_state.email,
            api_token=st.session_state.api_token,
            buscar_jira=buscar_jira
        )

    elif menu_option == "Relatorio Geral ITSM":
        st.title("Relatorio Geral ITSM")
        jql_fila = 'project = JSM ORDER BY created DESC'
        response = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql_fila)
        if response.status_code == 200:
            data = response.json()
            issues = data.get('issues', [])
            if issues:
                table_data = []
                for issue in issues:
                    fields = issue.get('fields', {})
                    chave = f"[{issue['key']}]({st.session_state.jira_url}/browse/{issue['key']})"
                    tipo = fields.get('issuetype', {}).get('name', 'N/A')
                    resumo = fields.get('summary', 'N/A')
                    criado = datetime.strptime(issue['fields']['created'], "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.timezone('America/Sao_Paulo'))
                    relator = fields.get('reporter', {}).get('displayName', 'N/A')
                    responsavel = fields.get('assignee', {}).get('displayName', 'N/A') if fields.get('assignee') else 'Não atribuído'
                    resolvido = datetime.strptime(fields.get('resolutiondate', '1970-01-01T00:00:00.000+0000'), "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.timezone('America/Sao_Paulo')) if fields.get('resolutiondate') else None
                    status = fields.get('status', {}).get('name', 'N/A')
                    resolucao = fields.get('resolution', {}).get('name', 'N/A') if fields.get('resolution') else 'N/A'
                    table_data.append({
                        "Chave": chave,
                        "Tipo": tipo,
                        "Resumo": resumo,
                        "Criado": criado,
                        "Relator": relator,
                        "Responsável": responsavel,
                        "Resolvido": resolvido,
                        "Status": status,
                        "Resolução": resolucao
                    })
                df = pd.DataFrame(table_data)
                st.data_editor(
                    df,
                    column_config={
                        "Chave": st.column_config.LinkColumn("Chave"),
                        "Criado": st.column_config.DatetimeColumn("Criado", format="DD/MM/YY HH:mm"),
                        "Resolvido": st.column_config.DatetimeColumn("Resolvido", format="DD/MM/YY HH:mm"),
                    },
                    hide_index=True,
                    use_container_width=True,
                    num_rows="dynamic",
                    disabled=True,
                    column_order=["Chave", "Tipo", "Resumo", "Criado", "Relator", "Responsável", "Resolvido", "Status", "Resolução"]
                )
            else:
                st.info("Nenhuma issue encontrada.")
        else:
            st.error(f"Erro ao buscar dados do Jira: {response.status_code} - {response.text}")
