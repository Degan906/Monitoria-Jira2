import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
import streamlit as st
from jira import JIRA

# ==============================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================
st.set_page_config(
    page_title="Painel de Licenças e Usuários Jira",
    layout="wide",
    page_icon="📊"
)

# ==============================================
# FUNÇÃO DE LOGIN
# ==============================================
def login():
    # Credenciais válidas
    valid_credentials = {
        "henrique.degan": "12345",
        "vinicius.herrera": "12345",
        "dante.labate": "12345"
    }
    # Tela de login
    st.markdown("""
    <div style="text-align: center; margin-top: 50px;">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCx0Ywq0Bhihr0RLdHbBrqyuCsRLoV2KLs2g&s" 
             width="150" height="150">
        <h1 style="font-size: 24px; margin-top: 20px;">Login</h1>
    </div>
    """, unsafe_allow_html=True)
    # Campos de entrada
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    # Botão de login
    if st.button("Entrar"):
        if username in valid_credentials and password == valid_credentials[username]:
            st.session_state.logged_in = True
            st.success("Login bem-sucedido!")
            st.rerun()  # Recarrega a página para acessar o conteúdo principal
        else:
            st.error("Usuário ou senha inválidos. Tente novamente.")

# ==============================================
# VERIFICAR SE O USUÁRIO ESTÁ LOGADO
# ==============================================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    login()
else:
    # ==============================================
    # CONFIGURAÇÃO DE AUTENTICAÇÃO JIRA
    # ==============================================
    JIRA_EMAIL = "henrique.degan@oatsolutions.com.br"
    JIRA_API_KEY = "b4mAs0sXJCx3101YvgkhBD3F"
    JIRA_SERVER = "https://carboncars.atlassian.net"

    # Configuração do cliente JIRA
    jira = JIRA(
        server=JIRA_SERVER,
        basic_auth=(JIRA_EMAIL, JIRA_API_KEY)
    )

    # ==============================================
    # FUNÇÕES AUXILIARES
    # ==============================================
    def obter_membros_grupo(nome_grupo):
        membros = []
        start_at = 0
        max_results = 50
        while True:
            try:
                response = requests.get(
                    f"{JIRA_SERVER}/rest/api/2/group/member",
                    params={
                        'groupname': nome_grupo,
                        'startAt': start_at,
                        'maxResults': max_results
                    },
                    auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_KEY),
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                # Filtra apenas usuários com accountType = 'atlassian' e ativos
                membros.extend([
                    m for m in data['values'] 
                    if m.get('active', False) and 
                    str(m.get('accountType', '')).lower() == 'atlassian'
                ])
                if data['isLast']:
                    break
                start_at += max_results
            except Exception as e:
                st.error(f"Erro ao buscar membros do grupo {nome_grupo}: {str(e)}")
                break
        return membros

    def contar_usuarios_grupo(nome_grupo):
        try:
            return len(obter_membros_grupo(nome_grupo))
        except Exception as e:
            st.error(f"Erro ao contar usuários: {str(e)}")
            return 0

    def contar_chamados_pendentes(jql):
        try:
            issues = jira.search_issues(jql, maxResults=0, validate_query=False)
            return issues.total
        except Exception as e:
            st.error(f"Erro ao contar chamados: {str(e)}")
            return "Erro"

    def criar_card_licenca(titulo, total, usadas, grupo, chamados_pendentes):
        # Cálculos
        livres = total - usadas
        em_chamado = chamados_pendentes  # Chamados pendentes representam as licenças em processo de solicitação
        critico = livres < 50  # Define se a situação é crítica (menos de 50 licenças livres)

        with st.container():
            st.markdown(
                f"""
                <style>
                    .card {{
                        border: 1px solid #e0e0e0;
                        border-radius: 10px;
                        padding: 15px;
                        margin: 10px 0;
                        background-color: #f9f9f9;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    }}
                    .card h3 {{
                        text-align: center;
                        margin: 0 0 15px 0;
                        font-size: 20px;
                        color: #333;
                    }}
                    .card p {{
                        font-size: 18px;
                        margin-bottom: 8px;
                        text-align: center;
                    }}
                    .critical {{
                        border: 2px solid #ff4444;
                        animation: pulse 1.5s infinite;
                    }}
                    @keyframes pulse {{
                        0% {{ box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.4); }}
                        70% {{ box-shadow: 0 0 0 10px rgba(255, 68, 68, 0); }}
                        100% {{ box-shadow: 0 0 0 0 rgba(255, 68, 68, 0); }}
                    }}
                </style>
                <div class="card{' critical' if critico else ''}">
                    <h3>{titulo}</h3>
                    <p><strong>Total:</strong> {total}</p>
                    <p><strong>Usadas:</strong> {usadas}</p>
                    <p><strong>Livres:</strong> <span style='color: {'red' if critico else 'green'}; font-weight: bold;'>{livres}</span></p>
                    <p><strong>Em Chamado:</strong> <span style='color: {'orange' if em_chamado > 0 else 'green'}; font-weight: bold;'>{em_chamado}</span></p>
                    <p><strong>Chamados Pendentes:</strong> <span style='color: {'orange' if isinstance(chamados_pendentes, int) and chamados_pendentes > 0 else 'green'}; font-weight: bold;'>{chamados_pendentes}</span></p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.progress(min(100, int((usadas / total) * 100)))  # Barra de progresso

            # Botão "Ver Usuários"
            if st.button(f"Ver Usuários ({grupo})", key=f"btn_{grupo}"):
                st.session_state.mostrar_usuarios_grupo = grupo  # Armazena o grupo no session_state

            if critico:
                st.error("⚠️ **ATENÇÃO:** Licenças críticas! Verifique imediatamente.")

    # ==============================================
    # QUERIES JQL
    # ==============================================
    JQL_JIRA_SOFTWARE = """
    project = "JSM" AND issuetype = "Service request" AND resolution = Unresolved
    AND "Sistema" = "Jira" AND "Tipo de Solicitação" = "Solicitação de Acesso Jira (JSM)"
    AND "Produto Jira" IN ("JSW - Jira Software")
    """

    JQL_SERVICE_MANAGEMENT = """
    project = "JSM" AND issuetype = "Service request" AND resolution = Unresolved
    AND "Sistema" = "Jira" AND "Tipo de Solicitação" = "Solicitação de Acesso Jira (JSM)"
    AND "Produto Jira" IN ("JSM - Jira Service Management")
    """

    # ==============================================
    # PÁGINA PRINCIPAL
    # ==============================================
    st.title("📊 Painel de Licenças e Usuários Jira")

    # Botão de Atualizar
    if st.button("🔄 Atualizar Dados"):
        st.session_state.refresh_data = True
        st.rerun()

    # Se o botão de atualização foi pressionado, recarregue os dados
    if "refresh_data" in st.session_state and st.session_state.refresh_data:
        st.session_state.refresh_data = False
        st.success("Dados atualizados com sucesso!")

    tab1, tab2 = st.tabs(["Licenças", "Todos os Usuários"])

    with tab1:
        col1, col2 = st.columns(2)

        # Card Jira Software
        with col1:
            criar_card_licenca(
                titulo="Licenças Jira Software",
                total=500,
                usadas=contar_usuarios_grupo("jira-software-users"),
                grupo="jira-software-users",
                chamados_pendentes=contar_chamados_pendentes(JQL_JIRA_SOFTWARE)
            )

        # Card Service Management
        with col2:
            criar_card_licenca(
                titulo="Licenças Service Management",
                total=200,
                usadas=contar_usuarios_grupo("jira-servicemanagement-users"),
                grupo="jira-servicemanagement-users",
                chamados_pendentes=contar_chamados_pendentes(JQL_SERVICE_MANAGEMENT)
            )

        # Detalhes de usuários
        if "mostrar_usuarios_grupo" in st.session_state:
            grupo = st.session_state.mostrar_usuarios_grupo
            st.subheader(f"👥 Usuários do grupo: {grupo} (Filtrado: accountType = Atlassian)")
            try:
                usuarios = obter_membros_grupo(grupo)
                if usuarios:
                    st.success(f"✅ {len(usuarios)} usuários ativos encontrados")
                    dados = []
                    for user in usuarios:
                        produtos = []
                        if 'groups' in user and 'items' in user['groups']:
                            if 'jira-software-users' in user['groups']['items']:
                                produtos.append("Jira Software")
                            if 'jira-servicemanagement-users' in user['groups']['items']:
                                produtos.append("Service Management")
                        dados.append({
                            "Nome": user.get("displayName", "N/A"),
                            "Email": user.get("emailAddress", "N/A"),
                            "Tipo de Conta": user.get("accountType", "N/A"),
                            "Produto": ", ".join(produtos) if produtos else "Nenhum",
                            "Status": "Ativo" if user.get("active", False) else "Inativo"
                        })
                    st.dataframe(
                        pd.DataFrame(dados),
                        use_container_width=True,
                        column_config={
                            "Tipo de Conta": st.column_config.TextColumn(
                                "Tipo de Conta",
                                help="Tipo de conta do usuário"
                            )
                        }
                    )
                else:
                    st.warning("Nenhum usuário ativo com accountType = Atlassian encontrado neste grupo.")
            except Exception as e:
                st.error(f"Erro ao carregar usuários: {str(e)}")

    with tab2:
        st.title("Todos os Usuários do Jira")
        # Busca todos os usuários
        users = fetch_users()
        if users:
            df = pd.DataFrame(users)
            # Adiciona coluna de Produto
            def determinar_produto(user):
                produtos = []
                if 'groups' in user and 'items' in user['groups']:
                    if 'jira-software-users' in user['groups']['items']:
                        produtos.append("Jira Software")
                    if 'jira-servicemanagement-users' in user['groups']['items']:
                        produtos.append("Service Management")
                return ", ".join(produtos) if produtos else "Nenhum"

            df['Produto'] = df.apply(determinar_produto, axis=1)

            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                # Filtro por Status
                if 'active' in df.columns:
                    status_options = ['Todos'] + list(df['active'].unique())
                    status_filter = st.selectbox('Status', options=status_options)
                else:
                    status_filter = 'Todos'
                    st.warning("Coluna 'active' não encontrada")

            with col2:
                # Filtro por Tipo de Conta
                if 'accountType' in df.columns:
                    account_type_options = ['Todos'] + list(df['accountType'].unique())
                    account_type_filter = st.selectbox('Tipo de Conta', options=account_type_options)
                else:
                    account_type_filter = 'Todos'
                    st.warning("Coluna 'accountType' não encontrada")

            with col3:
                # Filtro por Produto
                produto_options = ['Todos'] + sorted(df['Produto'].unique().tolist())
                produto_filter = st.selectbox('Produto', options=produto_options)

            # Aplicando filtros
            if status_filter != 'Todos' and 'active' in df.columns:
                df = df[df['active'] == status_filter]
            if account_type_filter != 'Todos' and 'accountType' in df.columns:
                df = df[df['accountType'] == account_type_filter]
            if produto_filter != 'Todos':
                df = df[df['Produto'].str.contains(produto_filter, na=False)]

            # Exibição dos dados
            st.write(f"Total de Usuários: {len(df)}")

            # Seleciona colunas para exibir
            cols_to_show = ['displayName', 'emailAddress', 'accountType', 'Produto']
            if 'active' in df.columns:
                cols_to_show.append('active')

            # Renomeia colunas para exibição
            df_display = df[cols_to_show].rename(columns={
                'displayName': 'Nome',
                'emailAddress': 'Email',
                'accountType': 'Tipo de Conta',
                'active': 'Ativo'
            })

            st.dataframe(
                df_display,
                use_container_width=True,
                height=600
            )

            # CSS para melhorar a exibição
            st.markdown("""
            <style>
                div[data-testid='stDataFrame'] {
                    width: 100% !important;
                }
                .stDataFrame {
                    font-size: 14px;
                }
            </style>
            """, unsafe_allow_html=True)
        else:
            st.error("Não foi possível carregar os usuários. Verifique os logs de erro.")
