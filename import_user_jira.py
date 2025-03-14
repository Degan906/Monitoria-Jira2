import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
import streamlit as st

# Função para buscar usuários
def fetch_users(jira_url, email, api_token):
    all_users = []
    start_at = 0
    max_results = 50

    while True:
        response = requests.request(
            "GET",
            f"{jira_url}/rest/api/2/users/search?startAt={start_at}&maxResults={max_results}",
            headers={"Accept": "application/json"},
            auth=HTTPBasicAuth(email, api_token)
        )
        
        data = json.loads(response.text)

        # Se a lista estiver vazia, saia do loop
        if not data:
            break

        # Adiciona os usuários à lista de todos os usuários
        all_users.extend(data)

        # Atualiza o deslocamento
        start_at += max_results

    return all_users

# Função principal que será chamada no código principal
def main(jira_url, email, api_token):
    # Título da aplicação
    st.title("Users Jira")

    # Chama a função para buscar usuários
    users = fetch_users(jira_url, email, api_token)
    df = pd.DataFrame(users)

    # Exibe a quantidade total de usuários antes do filtro
    total_users = len(df)
    st.write(f"Total de Usuários: {total_users}")

    # Criação de colunas para o layout horizontal
    col1, col2 = st.columns(2)

    # Seletor para filtrar usuários por status na coluna 1
    with col1:
        status_options = df['active'].unique()  # Assume que 'active' é a chave que indica o status
        status_filter = st.selectbox('Selecione o Status', options=['Todos'] + list(status_options))

    # Filtrando usuários conforme o status selecionado
    if status_filter != 'Todos':
        df = df[df['active'] == status_filter]

    # Exibe a quantidade total de usuários filtrados
    filtered_users_count = len(df)
    st.write(f"Total de Usuários Filtrados: {filtered_users_count}")

    # Exibição do DataFrame em grid na versão cheia da tela
    st.subheader("Usuários Filtrados") 
    st.dataframe(df, use_container_width=True)

    # Ajustando a largura do grid para preencher toda a tela
    st.markdown("""
    <style>
        div[data-testid='stDataFrame'] {
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Execução local (opcional)
if __name__ == "__main__":
    main(
        jira_url="https://carboncars.atlassian.net",
        email="henrique.degan@oatsolutions.com.br",
        api_token="b4mAs0sXJCx3101YvgkhBD3F"
    )
