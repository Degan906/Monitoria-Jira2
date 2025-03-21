import streamlit as st
from jira import JIRA
import pandas as pd
import requests  # Para fazer chamadas HTTP

# Configuração da página
st.set_page_config(page_title="Controle de Estoque e Orçamentos", layout="wide")

# Função para buscar membros de um grupo no Jira (apenas usuários ativos)
def get_group_members(jira_client, group_name):
    members = []
    start_at = 0
    max_results = 50  # Número máximo de resultados por página

    while True:
        # Faz a chamada à API para obter os membros do grupo
        response = jira_client._get_json(
            'group/member',
            params={'groupname': group_name, 'startAt': start_at, 'maxResults': max_results}
        )
        
        # Filtra apenas os usuários ativos
        active_members = [member for member in response['values'] if member.get('active', False)]
        members.extend(active_members)
        
        # Verifica se há mais páginas de resultados
        if response['isLast']:
            break
        
        # Atualiza o índice para a próxima página
        start_at += max_results

    return members

# Função para contar usuários em um grupo específico (apenas ativos)
def count_users_in_group(jira_client, group_name):
    try:
        # Busca os membros do grupo (apenas ativos)
        members = get_group_members(jira_client, group_name)
        return len(members)  # Retorna a quantidade de membros ativos
    except Exception as e:
        st.error(f"Erro ao buscar membros do grupo: {str(e)}")
        return 0

# Função para criar um card personalizado com informações de licenças
def create_license_card(title, total_licenses, used_licenses, width=200, height=150):
    free_licenses = total_licenses - used_licenses  # Calcula as licenças livres
    card_style = f"""
        <style>
            .card {{
                width: {width}px;
                height: {height}px;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 10px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
                text-align: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                background-color: #f9f9f9;
            }}
            .card h3 {{
                margin: 0;
                font-size: 14px;
                color: #333;
            }}
            .card h1 {{
                margin: 0;
                font-size: 24px;
                color: #000;
            }}
            .card p {{
                margin: 5px 0;
                font-size: 12px;
                color: #555;
            }}
        </style>
    """
    st.markdown(card_style, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="card">
            <h3>{title}</h3>
            <p>Total: {total_licenses}</p>
            <p>Usadas: {used_licenses}</p>
            <p>Livres: {free_licenses}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Função para buscar a última data de ativação usando a nova API
def get_last_active_date(org_id, account_id, access_token):
    url = f"https://api.atlassian.com/v1/orgs/{org_id}/directory/users/{account_id}/last-active-dates"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lança exceção se houver erro HTTP
        data = response.json()
        return data.get("lastActiveDate", "N/A")  # Retorna a última data de ativação ou "N/A"
    except Exception as e:
        st.error(f"Erro ao buscar última data de ativação: {str(e)}")
        return "N/A"

# Tela de Login
def login():
    st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
    st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCx0Ywq0Bhihr0RLdHbBrqyuCsRLoV2KLs2g&s", width=150)
    st.markdown('</div>', unsafe_allow_html=True)

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Login"):
        if (username == "henrique.degan" and password == "12345") or (username == "admin" and password == "admin"):
            st.session_state.logged_in = True
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# Verifica se o usuário está logado
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Inicializa 'member_data' se não estiver presente
if "member_data" not in st.session_state:
    st.session_state.member_data = []

if not st.session_state.logged_in:
    login()
else:
    
    # Menu lateral
    menu_option = st.sidebar.selectbox("Menu", ["Dash", "Usuários", "Busca Grupos/Users"])

    if menu_option == "Dash":
        st.title("Dashboard")

        # Configuração do cliente Jira
        jira = JIRA(
            server="https://carboncars.atlassian.net",
            basic_auth=("henrique.degan@oatsolutions.com.br", "b4mAs0sXJCx3101YvgkhBD3F")
        )

        # Cria duas colunas para os cards
        col1, col2 = st.columns(2)

        # Card 1: Licenças para "jira-software-users"
        with col1:
            group_name_software = "jira-software-users"
            total_licenses_software = 500  # Total de licenças disponíveis
            used_licenses_software = count_users_in_group(jira, group_name_software)  # Licenças usadas (apenas ativos)
            create_license_card(
                title=f"Licenças {group_name_software}",
                total_licenses=total_licenses_software,
                used_licenses=used_licenses_software,
                width=200,
                height=150
            )

        # Card 2: Licenças para "jira-servicemanagement-users"
        with col2:
            group_name_service = "jira-servicemanagement-users"
            total_licenses_service = 200  # Total de licenças disponíveis
            used_licenses_service = count_users_in_group(jira, group_name_service)  # Licenças usadas (apenas ativos)
            create_license_card(
                title=f"Licenças {group_name_service}",
                total_licenses=total_licenses_service,
                used_licenses=used_licenses_service,
                width=200,
                height=150
            )

    elif menu_option == "Usuários":
        st.title("Usuários")

        # Configuração do cliente Jira
        jira = JIRA(
            server="https://carboncars.atlassian.net",
            basic_auth=("henrique.degan@oatsolutions.com.br", "b4mAs0sXJCx3101YvgkhBD3F")
        )

        # Filtros
        filter_active = st.checkbox("Mostrar apenas usuários ativos", value=True)
        name_filter = st.text_input("Buscar por nome", placeholder="Ex: João")

        # Botão para buscar usuários
        if st.button("Buscar Usuários"):
            try:
                # Busca os usuários com base nos filtros
                users = jira.search_users(query=name_filter, maxResults=1000)  # Usa 'query' em vez de 'username'

                # Filtra os usuários com base nos critérios
                filtered_users = []
                for user in users:
                    if not filter_active or user.active:
                        # Busca a última data de ativação usando a nova API
                        last_active_date = get_last_active_date(
                            org_id="seu_org_id",  # Substitua pelo ID da sua organização
                            account_id=user.accountId,
                            access_token="seu_token_de_acesso"  # Substitua pelo token de acesso válido
                        )
                        filtered_users.append({
                            "ID": user.accountId,  # Adiciona o ID do usuário
                            "Nome": user.displayName,
                            "Email": user.emailAddress,  # Corrigido para usar emailAddress
                            "Última Ativação": last_active_date,
                            "Status": "Ativo" if user.active else "Inativo"
                        })

                if filtered_users:
                    st.success(f"Encontrados {len(filtered_users)} usuários:")
                    
                    # Exibe os usuários em formato responsivo
                    df_users = pd.DataFrame(filtered_users)
                    st.dataframe(df_users)  # Exibe a tabela dos usuários

                    # Armazena os dados na sessão para exportação
                    st.session_state.user_data = filtered_users

                else:
                    st.warning("Nenhum usuário encontrado com os filtros aplicados.")
            except Exception as e:
                st.error(f"Erro ao acessar o Jira: {str(e)}")

    elif menu_option == "Busca Grupos/Users":
        st.title("Listar Membros de um Grupo no Jira")

        # Entrada do nome do grupo
        group_name = st.text_input("Nome do Grupo", placeholder="Ex: jira-administrators")

        if st.button("Buscar Membros"):
            try:
                # Configuração do cliente Jira
                jira = JIRA(
                    server="https://carboncars.atlassian.net",
                    basic_auth=("henrique.degan@oatsolutions.com.br", "b4mAs0sXJCx3101YvgkhBD3F")
                )

                # Busca os membros do grupo
                members = get_group_members(jira, group_name)

                if members:
                    st.success(f"Encontrados {len(members)} membros no grupo '{group_name}':")
                    
                    # Limpa os dados antigos antes de adicionar novos
                    st.session_state.member_data.clear()
                    for member in members:
                        # Busca a última data de ativação usando a nova API
                        last_active_date = get_last_active_date(
                            org_id="seu_org_id",  # Substitua pelo ID da sua organização
                            account_id=member.get("accountId", ""),
                            access_token="seu_token_de_acesso"  # Substitua pelo token de acesso válido
                        )
                        st.session_state.member_data.append({
                            "ID": member.get("accountId", "N/A"),  # Adiciona o ID do usuário
                            "Nome": member.get("displayName", "N/A"),
                            "Email": member.get("emailAddress", "N/A"),  # Corrigido para usar emailAddress
                            "Última Ativação": last_active_date,
                            "Status": "Ativo" if member.get("active", False) else "Inativo"
                        })
                    
                    # Exibe os membros em formato responsivo
                    df_members = pd.DataFrame(st.session_state.member_data)
                    st.dataframe(df_members)  # Exibe a tabela dos membros

                else:
                    st.warning(f"Nenhum membro encontrado no grupo '{group_name}'.")
            except Exception as e:
                st.error(f"Erro ao acessar o Jira: {str(e)}")