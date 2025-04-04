# dashboard_gestao.py

import streamlit as st
from datetime import datetime
import pytz
import pandas as pd
import plotly.express as px

def mostrar_dashboard_gestao(jira_url, email, api_token, buscar_jira):
    st.title("Dashboard de Gestão")

    # Configuração dos filtros de data
    col1, col2 = st.columns(2)
    with col1:
        # Filtro para data de criação (padrão: primeiro dia do mês atual)
        data_inicio_criacao = st.date_input(
            "Data de início (criação)",
            value=datetime.now().replace(day=1),  # Primeiro dia do mês atual
            format="DD/MM/YYYY"
        )
    with col2:
        # Filtro para data final de criação (padrão: hoje)
        data_fim_criacao = st.date_input(
            "Data de fim (criação)",
            value=datetime.now(),  # Hoje
            format="DD/MM/YYYY"
        )

    # Adicionar filtros para data de resolução
    st.subheader("Filtros para Chamados Resolvidos")
    col3, col4 = st.columns(2)
    with col3:
        usar_filtro_resolucao = st.checkbox("Usar filtro para data de resolução", value=False)
    with col4:
        if usar_filtro_resolucao:
            data_inicio_resolucao = st.date_input(
                "Data de início (resolução)",
                value=datetime.now().replace(day=1),  # Primeiro dia do mês atual
                format="DD/MM/YYYY"
            )
            data_fim_resolucao = st.date_input(
                "Data de fim (resolução)",
                value=datetime.now(),  # Hoje
                format="DD/MM/YYYY"
            )

    # Botão para aplicar filtros
    aplicar_filtros = st.button("Aplicar Filtros")

    # Construir as JQLs com base nos filtros
    jql_criados = f'project = JSM AND created >= "{data_inicio_criacao}" AND created <= "{data_fim_criacao}"  AND "sistema[dropdown]" = Jira AND status != Cancelado'
    if usar_filtro_resolucao:
        jql_resolvidos = f'project = JSM AND resolutiondate >= "{data_inicio_resolucao}" AND resolutiondate <= "{data_fim_resolucao}"  AND "sistema[dropdown]" = Jira AND status != Cancelado'
    else:
        jql_resolvidos = f'project = JSM AND resolutiondate >= "{data_inicio_criacao}" AND resolutiondate <= "{data_fim_criacao}" AND resolutiondate is not EMPTY  AND "sistema[dropdown]" = Jira AND status != Cancelado'

    # Buscar dados
    with st.spinner("Buscando dados do Jira..."):
        # Buscar chamados criados
        response_criados = buscar_jira(jira_url, email, api_token, jql_criados)
        total_criados = response_criados.json().get('total', 0) if response_criados.status_code == 200 else 0

        # Buscar chamados resolvidos
        response_resolvidos = buscar_jira(jira_url, email, api_token, jql_resolvidos)
        total_resolvidos = response_resolvidos.json().get('total', 0) if response_resolvidos.status_code == 200 else 0

    # Exibir métricas
    st.subheader("Métricas Gerais")
    col_met1, col_met2, col_met3 = st.columns(3)
    with col_met1:
        st.metric("Chamados Criados", total_criados)
    with col_met2:
        st.metric("Chamados Resolvidos", total_resolvidos)
    with col_met3:
        diferenca = total_criados - total_resolvidos
        st.metric("Diferença", diferenca, delta_color="inverse")

    # Gráfico de pizza
    st.subheader("Chamados Criados vs Resolvidos")
    if total_criados > 0 or total_resolvidos > 0:
        fig = px.pie(
            names=['Criados', 'Resolvidos'],
            values=[total_criados, total_resolvidos],
            color=['Criados', 'Resolvidos'],
            color_discrete_map={'Criados': '#FF7F0E', 'Resolvidos': '#1F77B4'},
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

    # Gráfico de barras: Chamados por Assignee
    st.subheader("Distribuição de Chamados por Responsável")
    if total_criados > 0:
        # Buscar issues criadas com detalhes
        jql_detalhes = f'{jql_criados} ORDER BY created DESC'
        response_detalhes = buscar_jira(jira_url, email, api_token, jql_detalhes)
        if response_detalhes.status_code == 200:
            issues = response_detalhes.json().get('issues', [])
            if issues:
                dados_tabela = []
                for issue in issues:
                    fields = issue.get('fields', {})
                    # Correção para evitar AttributeError
                    assignee = fields.get('assignee')
                    assignee_name = assignee.get('displayName', 'Não atribuído') if assignee else 'Não atribuído'
                    dados_tabela.append({
                        "Chave": issue['key'],
                        "Resumo": fields.get('summary', 'N/A'),
                        "Status": fields.get('status', {}).get('name', 'N/A'),
                        "Criado": datetime.strptime(fields.get('created', ''), "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.timezone('America/Sao_Paulo')),
                        "Responsável": assignee_name
                    })
                df = pd.DataFrame(dados_tabela)

                # Agrupar chamados por responsável
                chamados_por_assignee = df.groupby("Responsável").size().reset_index(name="Quantidade")

                # Criar o gráfico de barras
                fig_barras = px.bar(
                    chamados_por_assignee,
                    x="Responsável",
                    y="Quantidade",
                    title="Chamados por Responsável",
                    labels={"Responsável": "Responsável", "Quantidade": "Número de Chamados"},
                    color="Quantidade",
                    color_continuous_scale=px.colors.sequential.Blues,
                    text="Quantidade"  # Adiciona o texto (quantidade) nas barras
                )
                fig_barras.update_traces(
                    textposition='outside'  # Posiciona o texto fora das barras
                )
                fig_barras.update_layout(
                    xaxis_title="Responsável",
                    yaxis_title="Número de Chamados",
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=False  # Oculta a legenda, se necessário
                )
                st.plotly_chart(fig_barras, use_container_width=True)
            else:
                st.info("Nenhum chamado encontrado com os filtros atuais.")
        else:
            st.error(f"Erro ao buscar detalhes: {response_detalhes.status_code}")
    else:
        st.info("Nenhum chamado criado no período selecionado.")

    # Tabela com detalhes dos chamados (opcional)
    expander = st.expander("Ver detalhes dos chamados")
    with expander:
        if total_criados > 0:
            # Buscar issues criadas com detalhes
            jql_detalhes = f'{jql_criados} ORDER BY created DESC'
            response_detalhes = buscar_jira(jira_url, email, api_token, jql_detalhes)
            if response_detalhes.status_code == 200:
                issues = response_detalhes.json().get('issues', [])
                if issues:
                    dados_tabela = []
                    for issue in issues:
                        fields = issue.get('fields', {})
                        # Correção para evitar AttributeError
                        assignee = fields.get('assignee')
                        assignee_name = assignee.get('displayName', 'Não atribuído') if assignee else 'Não atribuído'
                        dados_tabela.append({
                            "Chave": f"[{issue['key']}]({jira_url}/browse/{issue['key']})",
                            "Resumo": fields.get('summary', 'N/A'),
                            "Status": fields.get('status', {}).get('name', 'N/A'),
                            "Criado": datetime.strptime(fields.get('created', ''), "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.timezone('America/Sao_Paulo')),
                            "Responsável": assignee_name
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
