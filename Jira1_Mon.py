# V4.1 - 11/03/2025 - Degan
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import time
import pytz
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path
import os

# Adiciona o diretório atual ao path para garantir que imports locais funcionem
sys.path.append(str(Path(__file__).parent))

# Configuração da página
st.set_page_config(page_title="Monitoria", layout="wide")

# Dicionário de usuários e senhas
USERS = {
    "admin": "admin",
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

    # Função de autenticação (corrigida)
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
        ["Dash de monitoria", "Dashs Gestão", "Relatorio Geral ITSM", "User List", "Controle de licenças"]
    )

    if menu_option == "Dash de monitoria":
        st.title("Dashboard de Monitoria")

        queries = {
            "🤖 AUTOMAÇÕES AP 🤖": {
                "AP-Sem link de DOC": 'project = AP AND issuetype = Recebimento AND issueLinkType not in (ADM-Documentações-AB, Documentações) AND created >= 2024-05-01 AND resolved IS EMPTY',
                # ... (todas as outras queries originais)
            },
        }

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
                <strong>Última atualização:</strong> {st.session_state.last_update_time}
            </div>
            """,
            unsafe_allow_html=True
        )

        max_columns = 6
        num_columns = min(len(queries["🤖 AUTOMAÇÕES AP 🤖"]), max_columns)
        cols = results_placeholder.columns(num_columns)

        for col in cols:
            col.empty()

        st.markdown("""
        <style>
            @keyframes blink {
                0% { background-color: #ff3333; }
                50% { background-color: #ffff99; }
                100% { background-color: #ff3333; }
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
        </style>
        """, unsafe_allow_html=True)

        for i, (query_name, jql) in enumerate(queries["🤖 AUTOMAÇÕES AP 🤖"].items()):
            response = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql)
            if response.status_code == 200:
                data = response.json()
                issue_count = data.get('total', 0)
                with cols[i % num_columns]:
                    if issue_count > 0:
                        st.markdown(
                            f"""
                            <div class="blinking-card">
                                <h5 style="font-size: 12px; margin: 0; padding: 0;">{query_name}</h5>
                                <h2 style="font-size: 20px; margin: 0; padding: 0;">{issue_count}</h2>
                                <span style="font-size: 12px; margin: 0; padding: 0;">Total de Tickets</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
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

        st.session_state.last_update_time = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(60)
        st.rerun()

    elif menu_option == "Dashs Gestão":
        st.title("Dashboard de Gestão")
        
        col1, col2 = st.columns(2)
        
        with col1:
            data_inicio_criacao = st.date_input(
                "Data de início (criação)",
                value=datetime.now().replace(day=1),
                format="DD/MM/YYYY"
            )
        
        with col2:
            data_fim_criacao = st.date_input(
                "Data de fim (criação)",
                value=datetime.now(),
                format="DD/MM/YYYY"
            )
        
        st.subheader("Filtros para Chamados Resolvidos")
        col3, col4 = st.columns(2)
        
        with col3:
            usar_filtro_resolucao = st.checkbox("Usar filtro para data de resolução", value=False)
        
        with col4:
            if usar_filtro_resolucao:
                data_inicio_resolucao = st.date_input(
                    "Data de início (resolução)",
                    value=datetime.now().replace(day=1),
                    format="DD/MM/YYYY"
                )
                data_fim_resolucao = st.date_input(
                    "Data de fim (resolução)",
                    value=datetime.now(),
                    format="DD/MM/YYYY"
                )
        
        aplicar_filtros = st.button("Aplicar Filtros")
        
        jql_criados = f'project = JSM AND created >= "{data_inicio_criacao}" AND created <= "{data_fim_criacao}" AND "sistema[dropdown]" = Jira AND status != Cancelado'
        
        if usar_filtro_resolucao:
            jql_resolvidos = f'project = JSM AND resolutiondate >= "{data_inicio_resolucao}" AND resolutiondate <= "{data_fim_resolucao}" AND "sistema[dropdown]" = Jira AND status != Cancelado'
        else:
            jql_resolvidos = f'project = JSM AND resolutiondate >= "{data_inicio_criacao}" AND resolutiondate <= "{data_fim_criacao}" AND resolutiondate is not EMPTY AND "sistema[dropdown]" = Jira AND status != Cancelado'
        
        with st.spinner("Buscando dados do Jira..."):
            response_criados = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql_criados)
            total_criados = response_criados.json().get('total', 0) if response_criados.status_code == 200 else 0
            
            response_resolvidos = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql_resolvidos)
            total_resolvidos = response_resolvidos.json().get('total', 0) if response_resolvidos.status_code == 200 else 0
        
        st.subheader("Métricas Gerais")
        col_met1, col_met2, col_met3 = st.columns(3)
        
        with col_met1:
            st.metric("Chamados Criados", total_criados)
        
        with col_met2:
            st.metric("Chamados Resolvidos", total_resolvidos)
        
        with col_met3:
            diferenca = total_criados - total_resolvidos
            st.metric("Diferença", diferenca, delta_color="inverse")
        
        st.subheader("Chamados Criados vs Resolvidos")
        
        if total_criados > 0 or total_resolvidos > 0:
            fig = px.pie(
                names=['Criados', 'Resolvidos'],
                values=[total_criados, total_resolvidos],
                color=['Criados', 'Resolvidos'],
                color_discrete_map={'Criados':'#FF7F0E', 'Resolvidos':'#1F77B4'},
                hole=0.3
            )
            
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label+value',
                hoverinfo='label+percent+value'
            )
            
            fig.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
        
        expander = st.expander("Ver detalhes dos chamados")
        with expander:
            if total_criados > 0:
                jql_detalhes = f'{jql_criados} ORDER BY created DESC'
                response_detalhes = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql_detalhes)
                
                if response_detalhes.status_code == 200:
                    issues = response_detalhes.json().get('issues', [])
                    
                    if issues:
                        dados_tabela = []
                        for issue in issues:
                            fields = issue.get('fields', {})
                            dados_tabela.append({
                                "Chave": f"[{issue['key']}]({st.session_state.jira_url}/browse/{issue['key']})",
                                "Resumo": fields.get('summary', 'N/A'),
                                "Status": fields.get('status', {}).get('name', 'N/A'),
                                "Criado": datetime.strptime(fields.get('created', ''), "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.timezone('America/Sao_Paulo')),
                                "Responsável": fields.get('assignee', {}).get('displayName', 'Não atribuído')
                            })
                        
                        df = pd.DataFrame(dados_tabela)
                        st.dataframe(
                            df,
                            column_config={
                                "Chave": st.column_config.LinkColumn("Chave"),
                                "Criado": st.column_config.DatetimeColumn("Criado", format="DD/MM/YYYY HH:mm")
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.info("Nenhum chamado encontrado com os filtros atuais.")
                else:
                    st.error(f"Erro ao buscar detalhes: {response_detalhes.status_code}")
            else:
                st.info("Nenhum chamado criado no período selecionado.")

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
            
            jql_created = 'created >= startOfMonth() AND project = JSM AND created <= endOfMonth() ORDER BY created DESC'
            jql_resolved = 'resolutiondate >= startOfMonth() AND project = JSM AND resolutiondate <= endOfMonth() ORDER BY resolutiondate DESC'
            
            response_created = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql_created)
            if response_created.status_code == 200:
                data_created = response_created.json()
                total_created = data_created.get('total', 0)
                issues_created = data_created.get('issues', [])
            else:
                st.error(f"Erro ao buscar issues criadas: {response_created.status_code} - {response_created.text}")
                total_created = 0
                issues_created = []

            response_resolved = buscar_jira(st.session_state.jira_url, st.session_state.email, st.session_state.api_token, jql_resolved)
            if response_resolved.status_code == 200:
                data_resolved = response_resolved.json()
                total_resolved = data_resolved.get('total', 0)
            else:
                st.error(f"Erro ao buscar issues resolvidas: {response_resolved.status_code} - {response_resolved.text}")
                total_resolved = 0

            labels = ['Criadas', 'Resolvidas']
            values = [total_created, total_resolved]
            fig_pie = px.pie(
                names=labels,
                values=values,
                title="Issues Criadas vs Resolvidas no Mês",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            if issues_created:
                assignee_count = {}
                for issue in issues_created:
                    assignee = issue['fields'].get('assignee')
                    if assignee:
                        assignee_name = assignee.get('displayName', 'Não Atribuído')
                    else:
                        assignee_name = 'Não Atribuído'
                    if assignee_name in assignee_count:
                        assignee_count[assignee_name] += 1
                    else:
                        assignee_count[assignee_name] = 1

                assignees = list(assignee_count.keys())
                counts = list(assignee_count.values())

                fig_bar = px.bar(
                    x=assignees,
                    y=counts,
                    labels={'x': 'Assignee', 'y': 'Número de Issues'},
                    title="Issues por Assignee no Mês",
                    text=counts,
                    color=assignees,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_bar.update_traces(textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("Nenhuma issue criada encontrada para exibir o gráfico de assignees.")

    elif menu_option == "User List":
        try:
            from import_user_jira import main
            main(
                jira_url=st.session_state.jira_url,
                email=st.session_state.email,
                api_token=st.session_state.api_token
            )
        except ModuleNotFoundError:
            st.error("Módulo import_user_jira não encontrado!")
            st.code("Verifique se o arquivo import_user_jira.py está no mesmo diretório")

    elif menu_option == "Controle de licenças":
        try:
            from Dash_User import main
            main(
                jira_url=st.session_state.jira_url,
                email=st.session_state.email,
                api_token=st.session_state.api_token
            )
        except ModuleNotFoundError as e:
            st.error(f"Erro ao carregar o módulo Dash_User: {str(e)}")
            st.markdown("""
            **Solução:**
            1. Verifique se o arquivo `Dash_User.py` está na mesma pasta
            2. Confira se o nome do arquivo está exatamente como `Dash_User.py`
            3. Se estiver no Streamlit Cloud, certifique-se de que o arquivo foi enviado
            """)
            
            st.write("Arquivos no diretório atual:")
            st.write(os.listdir())

    # Rodapé
    current_time = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(
        f"""
        <div style="position: fixed; bottom: 0; right: 20px; font-size: 12px;">
           ✅ - Desenvolvido por Degan - 🌐 - Versão 1.1  - 🛂 - Usuário logado: {st.session_state.email} | Data e Hora: {current_time}
        </div>
        """,
        unsafe_allow_html=True
    )
