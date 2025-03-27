import streamlit as st
from jira import JIRA
import pandas as pd
import requests

# ==============================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================
st.set_page_config(
    page_title="Painel de Controle de Licenças Jira",
    layout="wide",
    page_icon="📊"
)

# ==============================================
# FUNÇÕES AUXILIARES
# ==============================================
def obter_data_ultima_atividade(org_id, account_id, access_token):
    url = f"https://api.atlassian.com/v1/orgs/{org_id}/directory/users/{account_id}/last-active-dates"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            return "N/A"
        response.raise_for_status()
        data = response.json()
        return data.get("lastActiveDate", "N/A")
    except Exception as e:
        st.error(f"Erro ao buscar última atividade: {str(e)}")
        return "N/A"

def obter_membros_grupo(jira_client, nome_grupo):
    membros = []
    start_at = 0
    max_results = 50
    while True:
        response = jira_client._get_json(
            'group/member',
            params={'groupname': nome_grupo, 'startAt': start_at, 'maxResults': max_results}
        )
        membros.extend([m for m in response['values'] if m.get('active', False)])
        if response['isLast']:
            break
        start_at += max_results
    return membros

def contar_usuarios_grupo(jira_client, nome_grupo):
    try:
        return len(obter_membros_grupo(jira_client, nome_grupo))
    except Exception as e:
        st.error(f"Erro ao contar usuários: {str(e)}")
        return 0

def contar_chamados_pendentes(jira_client, jql):
    try:
        # Desativa validação para evitar erros com campos personalizados
        issues = jira_client.search_issues(jql, maxResults=0, validate_query=False)
        return issues.total
    except Exception as e:
        st.error(f"Erro ao contar chamados: {str(e)}")
        return "Erro"

# ==============================================
# FUNÇÃO PARA CRIAR OS CARDS DE LICENÇAS
# ==============================================
def criar_card_licenca(titulo, total, usadas, grupo, chamados_pendentes):
    livres = total - usadas
    critico = livres < 50
    
    with st.container():
        # Container do card com CSS personalizado
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
        
        # Barra de progresso
        st.progress(min(100, int((usadas / total) * 100)))
        
        # Botão centralizado
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 10px;">
                <a href="?mostrar_usuarios={grupo}" 
                   style="display: inline-block; 
                          padding: 8px 16px; 
                          background-color: #3498db; 
                          color: white; 
                          text-decoration: none; 
                          border-radius: 5px;
                          font-size: 15px;">
                    Ver Usuários
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if critico:
            st.error("⚠️ **ATENÇÃO:** Licenças críticas! Verifique imediatamente.")

# ==============================================
# CONFIGURAÇÃO DO CLIENTE JIRA
# ==============================================
jira = JIRA(
    server="https://carboncars.atlassian.net",
    basic_auth=(
        "henrique.degan@carbon.cars", 
        "ATATT3xFfGF03Jo48WJdkOoxAA5H32mp6xaogLgo10JVX6zVLKqiljKtndWZo4neiJNPLo9z2DNV-01mAiEIL2p2vyIs9qetM2fM9OCwmieZyQHMVd5ZSMCV-UT1R5Qt4yz66H1epn9lQVsIXDhRPNi9V0sGPPaCDfPQtUWdsZQ7ng8BbQGe7co=EFE2C1D8"
    )
)

# ==============================================
# QUERIES JQL - ATUALIZE COM OS NOMES CORRETOS DOS CAMPOS!
# ==============================================
# IMPORTANTE: Substitua os nomes dos campos pelos que existem na sua instância
# Use o código abaixo para listar os campos disponíveis:

# st.subheader("Campos disponíveis no Jira:")
# fields = jira.fields()
# for field in fields:
#     st.write(f"Nome: {field['name']}, ID: {field['id']}, Key: {field.get('key')}")

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
st.title("📊 Painel de Licenças Jira")

# Layout em colunas
col1, col2 = st.columns(2)

# Card Jira Software
with col1:
    criar_card_licenca(
        titulo="Licenças Jira Software",
        total=500,
        usadas=max(contar_usuarios_grupo(jira, "jira-software-users") - 56, 0),
        grupo="jira-software-users",
        chamados_pendentes=contar_chamados_pendentes(jira, JQL_JIRA_SOFTWARE)
    )

# Card Service Management
with col2:
    criar_card_licenca(
        titulo="Licenças Service Management",
        total=200,
        usadas=max(contar_usuarios_grupo(jira, "jira-servicemanagement-users") - 54, 0),
        grupo="jira-servicemanagement-users",
        chamados_pendentes=contar_chamados_pendentes(jira, JQL_SERVICE_MANAGEMENT)
    )

# ==============================================
# FUNCIONALIDADE DE DETALHES DE USUÁRIOS
# ==============================================
if "mostrar_usuarios" in st.query_params:
    grupo = st.query_params["mostrar_usuarios"]
    st.subheader(f"👥 Usuários do grupo: {grupo}")
    
    try:
        usuarios = obter_membros_grupo(jira, grupo)
        if usuarios:
            st.success(f"✅ {len(usuarios)} usuários ativos encontrados")
            
            dados = []
            for user in usuarios:
                dados.append({
                    "Nome": user.get("displayName", "N/A"),
                    "Email": user.get("emailAddress", "N/A"),
                    "Última Atividade": obter_data_ultima_atividade(
                        org_id="SEU_ORG_ID",
                        account_id=user.get("accountId"),
                        access_token="SEU_TOKEN_ACESSO"
                    ),
                    "Status": "Ativo" if user.get("active", False) else "Inativo"
                })
            
            st.dataframe(pd.DataFrame(dados), use_container_width=True)
        else:
            st.warning("Nenhum usuário ativo encontrado neste grupo.")
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {str(e)}")