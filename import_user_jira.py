# import_user_jira.py
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

def importar_usuarios_jira(jira_url, email, api_token):
    headers = {
        "Accept": "application/json"
    }
    response = requests.get(
        f"{jira_url}/rest/api/2/users",
        headers=headers,
        auth=HTTPBasicAuth(email, api_token)
    )
    return response

def main(jira_url, email, api_token):
    st.title("Importar Usuários do Jira")
    if st.button("Importar Usuários"):
        response = importar_usuarios_jira(jira_url, email, api_token)
        if response.status_code == 200:
            usuarios = response.json()
            st.write("Usuários importados com sucesso!")
            st.write(usuarios)
        else:
            st.error(f"Erro ao importar usuários: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main(
        jira_url="https://carboncars.atlassian.net",
        email="henrique.degan@oatsolutions.com.br",
        api_token="b4mAs0sXJCx3101YvgkhBD3F"
    )
