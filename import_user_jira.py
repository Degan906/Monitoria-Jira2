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
# CONFIGURAÇÃO DE AUTENTICAÇÃO
# ==============================================
JIRA_EMAIL = "jirabot@carbon.cars"
JIRA_API_KEY = "ATATT3xFfGF0jaBk9j7bnwYSBL39xNSfmYB1GmuL5Dc5dbZMRfG3sWrJ7Xk0iVAZXXoB7Bzd8v4Hwd3smZiHaZLM_b3URnXkGqRK1eH4PpoKsnk_GIod_Vae1Xa5NWgUPfe0AfptUQyiqvbjaHQNH9Qeuas1bYr6u5VlzU-_J0scHv1K4AGF0WU=4D512725"
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

def fetch_users():
    all_users = []
    start_at = 0
    max_results = 50
    while True:
        try:
            response = requests.get(
                f"{JIRA_SERVER}/rest/api/2/users/search",
                params={
                    'startAt': start_at,
                    'maxResults': max_results
                },
                headers={"Accept": "application/json"},
                auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_KEY)
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            all_users.extend(data)
            start_at += max_results
        except Exception as e:
            st.error(f"Erro ao buscar usuários: {str(e)}")
            break
    return all_users

def criar_card_licenca(titulo, total, usadas, grupo, chamados_pendentes):
    livres = total - usadas
    critico = livres < 50
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
                <p><strong>Usadas:</strong> <a href="?mostrar_usuarios={grupo}" style='text-decoration: none;'>{usadas}</a></p>
                <p><strong>Livres:</strong> <span style='color: {'red' if critico else 'green'}; font-weight: bold;'>{livres}</span></p>
                <p><strong>Chamados Pendentes:</strong> <span style='color: {'orange' if isinstance(chamados_pendentes, int) and chamados_pendentes > 0 else 'green'}; font-weight: bold;'>{chamados_pendentes}</span></p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.progress(min(100, int((usadas / total) * 100)))  # Parêntese corrigido aqui
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
