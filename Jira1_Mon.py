# V4.1 - 11/03/2025 - Degan
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import time
import pytz
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Monitoria", layout="wide")

# Dicionário de usuários e senhas
USERS = {
    "admin": "admin",
    "henrique.degan": "12345",
    "user2": "password2",
    "user3": "password3"
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

    # Função de autenticação (corrigida)
    def authenticate_user(username, password):
        return USERS.get(username) == password

    if st.button("Entrar"):
        if authenticate_user(username, password):
            st.session_state.authenticated = True
            st.session_state.jira_url = "https://carboncars.atlassian.net"
            st.session_state.email = "henrique.degan@oatsolutions.com.br"
            st.session_state.api_token = "b4mAs0sXJCx3101YvgkhBD3F"  # Certifique-se de não expor tokens sensíveis
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

    if menu_option == "Dash de monitoria":
        st.title("Dashboard de Monitoria")  # Título para a seção de dashboard

        # Definir a JQL (movido para antes do uso)
        queries = {
            "🤖 AUTOMAÇÕES AP 🤖": {
                "AP-Sem link de DOC": 'project = AP AND issuetype = Recebimento AND issueLinkType not in (ADM-Documentações-AB, Documentações) AND created >= 2024-05-01 AND resolved IS EMPTY',
                "AP-Sem link de VIDRO": 'project = AP AND issuetype = Recebimento AND issueLinkType not in (P-Vidro) AND created >= 2024-05-01 AND resolved IS EMPTY',
                "AP-Sem Link de AÇO": 'project = AP AND issuetype = Recebimento AND issueLinkType not in (P-Aço) AND created >= 2024-05-01 AND resolved IS EMPTY',
                "AP-Sem link de MANTA": 'project = AP AND issuetype = Recebimento AND issueLinkType not in (P-Manta) AND created >= 2024-05-01 AND resolved IS EMPTY',
                "AP-Sem link de SVIDRO": 'project = AP AND issuetype = Recebimento AND status != Cancelado AND issueLinkType not in ("P-Suporte Vidro") AND created >= 2024-05-01 AND resolved IS EMPTY',
                "AP-Sem link de PB": 'project = AP AND issuetype = Recebimento AND status = "Produção PB" AND issueLinkType not in ("PB - Produção Blindados") AND created >= 2024-05-01 AND resolved IS EMPTY',
                "AP - Ag.Ent-Data Exército preenchida": 'project = AP and issuetype = Recebimento and status = "Aguardando entrada" and "Data de Liberação do Exército[Date]" is not empty and summary !~ TESTE',
                "PB-Sem link de VL": 'project = PB AND status was "Definir Técnico Montagem" and issueLinkType not in (VAL) and created >= startOfYear(-1)',
                "PB-Ag. Limpeza QA1": 'project = PB and status = "135 - Aguardando Limpeza QA1" and type = "Produção Blindados"',
                "PB-Parado em Ag. Exército": 'project = PB and status = "130 - Aguardando Exército" and "JSW_P-Validação (TM) - Done" is not empty',
                "PB-Parado em Exército Concluído": 'project = PB and status = "131 - Exército Concluído"',
                "PB-Veículo Finalizado sem Validação": 'filter in ("10983") AND project = PB AND "Veiculo Finalizado na Produção" is not EMPTY AND "12 - Aguardando Validações" is EMPTY',
                "PB-Passou-131-Exército/TM/aberto": 'project = PB AND status changed to "131 - Exército Concluído" after startOfYear() and "JSW_P-Validação (TM) - Done" is empty',
                "PB-DT.CONTRATO vazia": 'filter in ("10983") AND type in ("Produção Blindados", "Produção Blindados - QA") AND DT.CONTRATO is EMPTY AND status != Cancelado',
                "PB-6.3-Finalizar Toyota": 'filter in ("10549") AND issuetype = "Produção Blindados" AND status = "6.3 - Finalizar Toyota" AND "Tag Toyota" = TOYOTA',
                "Compras sem Supply": 'filter in ("10549") AND project = COM AND created >= 2023-07-01 AND issueLinkType = EMPTY',
                "Monitoria de processo Incidentes": 'filter in ("10549") AND project = SJM AND issuetype = "[System] Incident" AND labels = ⚠️MONITORIA⚠️ AND resolution = Unresolved and status = "Aguardando Atendimento"',
                "PB - Sem/Veiculo Marca/Modelo ": 'filter in ("10549") AND created >= 2023-07-01 AND project in (PB, AP) AND "Veiculo - Marca/Modelo[Short text]" is EMPTY AND resolution = Unresolved',
                "AP/PB/VAM - Sem Veiculo ": 'filter in ("10549") AND (filter in ("10549") AND project in (VIDRO, MANTA, ACO, "SUPORTE VIDRO", "CONJUNTO AÇO DO VIDRO") AND "Veiculo - Marca/Modelo[Short text]" is EMPTY AND created >= -120d AND summary !~ RNC AND summary !~ AVULSA AND status not in (Cancelado) AND statusCategory != Done AND "Tipo Card[Select List (cascading)]" = "NÃO RNC" OR project in (AP, PB, VL) AND "veiculo - marca/modelo[short text]" is EMPTY AND resolution = Unresolved)',
                "Pós Venda - Veiculos - Marca/Modelo": 'filter in ("10549") AND project = PV AND issuetype in ("[System] Incident", "Sub-Task - Eletrônica", "Sub-Task - Estética", "Sub-Task - Montagem") AND created >= 2023-08-25 AND "Veiculo - Marca/Modelo[Short text]" is EMPTY AND resolution = Unresolved',
                "PBV - Volvo sem Tork's": 'project = PBV AND resolution = Done AND "marca[short text]" ~ "VOLVO" AND "modelo[short text]" !~ "EX30 SUV" AND "Modelo[Short text]" !~ "C40 COUPE" AND "Torque Vidro[Radio Buttons]" IS EMPTY ORDER BY created DESC',
                "PB - Instalando Vidro erro": 'project = "Produção Blindados" AND status = "Instalando Vidro"  AND issueLinkType = "PB > VF" AND issueLinkType = "PB > VM" AND resolution = "Done" ORDER BY created DESC',
                "Peças sem Marca/Veiculo": 'project = SUPPLY AND type = "Supply Chain" AND "Request Type (Custom)[Short text]" ~ "Peças Produção" and "Marca[Short text]" IS EMPTY',
                "Vidro EXPORT": 'project = VIDRO AND type = Vidro AND "blindagem[short text]" ~ "EXPORT" and labels  != 🟢EXPORT',
            },
        }

        # Criar duas colunas para os botões
        col1, col2 = st.columns(2)

        # Botão de atualização de dados na primeira coluna
        with col1:
            if st.button("Atualizar Dados"):
                st.cache_data.clear()  # Limpa o cache para forçar a busca de novos dados
                st.rerun()  # Recarrega a página

        # Botão para exibir issues alarmadas na segunda coluna
        with col2:
            if st.button("Exibir Issues Alarmadas"):
                st.session_state.show_alarmed_issues = True  # Ativar a exibição da tabela

        # Verificar se o botão foi clicado e exibir a tabela
        if st.session_state.get('show_alarmed_issues', False):
            st.subheader("Issues Alarmadas")
            # Buscar todas as issues alarmadas
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
            # Exibir a tabela de issues alarmadas
            if alarmed_issues:
                df_alarmed = pd.DataFrame(alarmed_issues)
                st.data_editor(
                    df_alarmed,
                    column_config={
                        "Chave": st.column_config.LinkColumn("Chave"),  # Transforma a coluna Chave em um link clicável
                        "Criado": st.column_config.DatetimeColumn("Criado", format="DD/MM/YY HH:mm"),
                    },
                    hide_index=True,
                    use_container_width=True,
                    num_rows="dynamic",
                    disabled=True,
                    column_order=["Chave", "Tipo", "Resumo", "Criado", "Relator", "Responsável", "Status", "Resolução"]
                )
                # Reproduzir som de alarme usando JavaScript
                st.markdown(
                    """
                    <audio autoplay>
                        <source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" type="audio/mp3">
                        Seu navegador não suporta o elemento de áudio.
                    </audio>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("Nenhuma issue alarmada encontrada.")

        # Espaço reservado para os resultados
        results_placeholder = st.empty()

        # Atualização a cada 5 segundos
        if 'last_update_time' not in st.session_state:
            st.session_state.last_update_time = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")

        # Mostrar barra de status de atualização
        status_bar.markdown(
            f"""
            <div style="background-color: #f0f0f0; padding: 10px; text-align: center; border-radius: 5px; margin-bottom: 10px;">
                <strong>Última atualização:</strong> {st.session_state.last_update_time}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Max de 6 colunas
        max_columns = 6  # Máximo de colunas
        num_columns = min(len(queries["🤖 AUTOMAÇÕES AP 🤖"]), max_columns)
        cols = results_placeholder.columns(num_columns)  # Max de 6 colunas

        # Limpar conteúdo anterior
        for col in cols:
            col.empty()

        # Renderizar todos os cards primeiro
        for i, (query_name, jql) in enumerate(queries["🤖 AUTOMAÇÕES AP 🤖"].items()):
            response = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql)
            if response.status_code == 200:
                data = response.json()
                issue_count = data.get('total', 0)  # Obter o número total de issues

                # Exibir o card inicial
                with cols[i % num_columns]:  # Distribuir os cards nas colunas disponíveis
                    if issue_count > 0:
                        # Exibir GIF e fundo amarelo quando a quantidade for maior que 0
                        st.markdown(
                            f"""
                            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; text-align: center; width: 100%; max-width: 100%; height: auto; display: flex; flex-direction: column; justify-content: center; align-items: center; margin: 10px; background-color: #ffff99;">
                                <h5 style="font-size: 12px; margin: 0; padding: 0;">{query_name}</h5>
                                <h2 style="font-size: 20px; margin: 0; padding: 0;">{issue_count}</h2>
                                <span style="font-size: 12px; margin: 0; padding: 0;">Total de Tickets</span>
                                <img src="https://em-content.zobj.net/source/animated-noto-color-emoji/356/police-car-light_1f6a8.gif" width="50" height="50" style="margin-top: 5px;">
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        # Exibir card sem GIF e com fundo branco quando a quantidade for 0
                        st.markdown(
                            f"""
                            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; text-align: center; width: 100%; max-width: 100%; height: auto; display: flex; flex-direction: column; justify-content: center; align-items: center; margin: 10px; background-color: #ffffff;">
                                <h5 style="font-size: 12px; margin: 0; padding: 0;">{query_name}</h5>
                                <h2 style="font-size: 20px; margin: 0; padding: 0;">{issue_count}</h2>
                                <span style="font-size: 12px; margin: 0; padding: 0;">Total de Tickets</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            else:
                st.error(f"Erro ao buscar dados do Jira para {query_name}: {response.status_code} - {response.text}")

        # Atualizar a última data de atualização
        st.session_state.last_update_time = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")
        st.write("Aqui estão os dados do dashboard de monitoria...")  # Conteúdo adicional do dashboard

        # Aguardar 60 segundos antes da próxima atualização
        time.sleep(60)
        st.rerun()

    elif menu_option == "Dashs Gestão":
        st.title("Dashs Gestão")
        st.warning("🚧 Esta seção está em construção! 🚧")
        st.info("Estamos trabalhando para trazer novidades. Aguarde!")

    elif menu_option == "Relatorio Geral ITSM":
        st.title("Relatorio Geral ITSM")
        # JQL para buscar issues ordenadas pela data de criação
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
                    # Converter Criado para datetime
                    criado = datetime.strptime(issue['fields']['created'], "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.timezone('America/Sao_Paulo'))
                    relator = fields.get('reporter', {}).get('displayName', 'N/A')
                    responsavel = fields.get('assignee', {}).get('displayName', 'N/A') if fields.get('assignee') else 'Não atribuído'
                    # Converter Resolvido para datetime ou usar None se vazio
                    resolvido = datetime.strptime(fields.get('resolutiondate', '1970-01-01T00:00:00.000+0000'), "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.timezone('America/Sao_Paulo')) if fields.get('resolutiondate') else None
                    status = fields.get('status', {}).get('name', 'N/A')  # Campo Status
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
                # Converter para DataFrame
                df = pd.DataFrame(table_data)
                # Configurar as colunas para filtros interativos
                st.data_editor(
                    df,
                    column_config={
                        "Chave": st.column_config.LinkColumn("Chave"),  # Transforma a coluna Chave em um link clicável
                        "Criado": st.column_config.DatetimeColumn("Criado", format="DD/MM/YY HH:mm"),
                        "Resolvido": st.column_config.DatetimeColumn("Resolvido", format="DD/MM/YY HH:mm"),
                    },
                    hide_index=True,
                    use_container_width=True,  # Torna a tabela responsiva
                    num_rows="dynamic",  # Permite paginação e filtros
                    disabled=True,  # Desabilita edição dos dados
                    column_order=["Chave", "Tipo", "Resumo", "Criado", "Relator", "Responsável", "Resolvido", "Status", "Resolução"]
                )
            else:
                st.info("Nenhuma issue encontrada.")
        else:
            st.error(f"Erro ao buscar dados do Jira: {response.status_code} - {response.text}")
            # JQL para buscar issues criadas e resolvidas neste mês
            jql_created = 'created >= startOfMonth() AND project = JSM AND created <= endOfMonth() ORDER BY created DESC'
            jql_resolved = 'resolutiondate >= startOfMonth() AND project = JSM AND resolutiondate <= endOfMonth() ORDER BY resolutiondate DESC'
            # Buscar issues criadas
            response_created = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql_created)
            if response_created.status_code == 200:
                data_created = response_created.json()
                total_created = data_created.get('total', 0)
                issues_created = data_created.get('issues', [])
            else:
                st.error(f"Erro ao buscar issues criadas: {response_created.status_code} - {response_created.text}")
                total_created = 0
                issues_created = []

            # Buscar issues resolvidas
            response_resolved = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql_resolved)
            if response_resolved.status_code == 200:
                data_resolved = response_resolved.json()
                total_resolved = data_resolved.get('total', 0)
            else:
                st.error(f"Erro ao buscar issues resolvidas: {response_resolved.status_code} - {response_resolved.text}")
                total_resolved = 0

            # Criar gráfico de pizza
            labels = ['Criadas', 'Resolvidas']
            values = [total_created, total_resolved]
            fig_pie = px.pie(
                names=labels,
                values=values,
                title="Issues Criadas vs Resolvidas no Mês",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            # Exibir o gráfico de pizza
            st.plotly_chart(fig_pie, use_container_width=True)

            # Gráfico de barras por assignee
            if issues_created:
                # Contar issues por assignee
                assignee_count = {}
                for issue in issues_created:
                    # Verificar se o campo 'assignee' existe e não é None
                    assignee = issue['fields'].get('assignee')
                    if assignee:  # Se o assignee existir
                        assignee_name = assignee.get('displayName', 'Não Atribuído')
                    else:  # Se o assignee for None
                        assignee_name = 'Não Atribuído'
                    # Contar issues por assignee
                    if assignee_name in assignee_count:
                        assignee_count[assignee_name] += 1
                    else:
                        assignee_count[assignee_name] = 1

                # Preparar dados para o gráfico de barras
                assignees = list(assignee_count.keys())
                counts = list(assignee_count.values())

                # Criar gráfico de barras
                fig_bar = px.bar(
                    x=assignees,
                    y=counts,
                    labels={'x': 'Assignee', 'y': 'Número de Issues'},
                    title="Issues por Assignee no Mês",
                    text=counts,
                    color=assignees,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_bar.update_traces(textposition='outside')  # Posicionar os números acima das barras

                # Exibir o gráfico de barras
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("Nenhuma issue criada encontrada para exibir o gráfico de assignees.")

    elif menu_option == "User List":
        # Importar e executar o código do arquivo import_user_jira.py
        from import_user_jira import main
        main(
            jira_url=st.session_state.jira_url,
            email=st.session_state.email,
            api_token=st.session_state.api_token
        )

    # Exibir a data e hora atual no rodapé
    current_time = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(
        f"""
        <div style="position: fixed; bottom: 0; right: 20px; font-size: 12px;">
           ✅ - Desenvolvido por Degan - 🌐 - Versão 1.1  - 🛂 - Usuário logado: {st.session_state.email} | Data e Hora: {current_time}
        </div>
        """,
        unsafe_allow_html=True
    )
