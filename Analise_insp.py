import pandas as pd
import dash
from dash import html, dcc, dash_table, Input, Output

external_stylesheets = ["https://fonts.googleapis.com/css2?family=Roboto&display=swap"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Caminho para o arquivo Excel
arquivo = "C:/Users/vinicius.souza/OneDrive - CARBON CARS/Dados/PUBLICO/1 - Controle Retorno Assistência Técnica/analise_insp.xlsx"

# Carregando os dados para cada período
df_30 = pd.read_excel(arquivo, sheet_name="30D")
df_60 = pd.read_excel(arquivo, sheet_name="60D")
df_90 = pd.read_excel(arquivo, sheet_name="90D")

# Padronizar nomes de colunas e transformar percentual para float
for df in [df_30, df_60, df_90]:
    df.columns = df.columns.str.strip()
    df["TAXA DE RETORNO"] = pd.to_numeric(df["TAXA DE RETORNO"].astype(str).str.replace('%','').str.replace(',','.'), errors='coerce').fillna(0)
    df["TOTAL DE OS"] = pd.to_numeric(df["TOTAL DE OS"], errors='coerce').fillna(0)
    df["RETORNOS"] = pd.to_numeric(df["RETORNOS"], errors='coerce').fillna(0)

# Criar colunas combinadas para cada tabela
for df in [df_30, df_60, df_90]:
    df["TAXA TEXTO"] = df["TAXA DE RETORNO"].map(lambda x: f"{x:.1f}%")
    df["EXIBICAO"] = (
        "Total de OS: " + df["TOTAL DE OS"].astype(int).astype(str) +
        "\nRetornos: " + df["RETORNOS"].astype(int).astype(str) +
        "\n" + df["TAXA TEXTO"]
    )
    df["COR"] = df["TAXA DE RETORNO"].apply(lambda x: '#d6f5d6' if x <= 3.5 else '#fffac8' if x <= 5 else '#f4cccc')

# Ranking por setor com critérios: menor taxa, maior TOTAL DE OS, menor RETORNOS (baseado apenas nos 30D)
rankings_dict = {}
medalhas = {1: "🥇", 2: "🥈", 3: "🥉"}
for setor in df_30["SETOR"].unique():
    subset = df_30[df_30["SETOR"] == setor].copy()
    subset = subset.sort_values(
        by=["TAXA DE RETORNO", "TOTAL DE OS", "RETORNOS"], ascending=[True, False, True]
    ).reset_index(drop=True)
    subset["Posição"] = subset.index + 1
    subset["INSPETOR"] = subset.apply(lambda row: f"{medalhas.get(row['Posição'], '')} {row['INSPETOR']}", axis=1)
    rankings_dict[setor] = subset.head(3)[["SETOR", "Posição", "INSPETOR"]]

# Juntar para exibição
merged = df_30[['INSPETOR', 'SETOR', 'EXIBICAO', 'COR']].rename(columns={'EXIBICAO': '30D', 'COR': 'COR_30'})
merged = merged.merge(df_60[['INSPETOR', 'EXIBICAO', 'COR']].rename(columns={'EXIBICAO': '60D', 'COR': 'COR_60'}), on='INSPETOR')
merged = merged.merge(df_90[['INSPETOR', 'EXIBICAO', 'COR']].rename(columns={'EXIBICAO': '90D', 'COR': 'COR_90'}), on='INSPETOR')
merged = merged.drop_duplicates(subset='INSPETOR')

# Layout
app.layout = html.Div([
    html.H1("Dashboard de Retorno por Inspetor", style={"textAlign": "center", "backgroundColor": "#2C3E50", "color": "white", "padding": "10px", "borderRadius": "10px", "fontFamily": "Roboto, sans-serif"}),

    dcc.Dropdown(
        id='setor-dropdown',
        options=[{"label": setor, "value": setor} for setor in sorted(merged["SETOR"].unique())] + [{"label": "Todos", "value": "Todos"}],
        value="Todos",
        placeholder="Filtrar por setor",
        style={"width": "300px", "margin": "10px auto", "fontFamily": "Roboto, sans-serif"}
    ),

    html.Hr(style={"borderTop": "4px solid #2C3E50"}),

    html.Div(id='dashboard-content', style={"padding": "20px", "fontFamily": "Roboto, sans-serif"})
])

@app.callback(
    Output('dashboard-content', 'children'),
    Input('setor-dropdown', 'value')
)
def atualizar_tabela(setor_selecionado):
    if setor_selecionado and setor_selecionado != "Todos":
        df_view = merged[merged["SETOR"] == setor_selecionado].copy()
    else:
        df_view = merged.sort_values(by=["SETOR", "INSPETOR"]).copy()

    setor_changes = df_view["SETOR"].ne(df_view["SETOR"].shift())
    borders = ["4px solid #2C3E50" if change else "" for change in setor_changes]

    tabela = dash_table.DataTable(
        columns=[
            {"name": "SETOR", "id": "SETOR"},
            {"name": "INSPETOR", "id": "INSPETOR"},
            {"name": "30D", "id": "30D"},
            {"name": "60D", "id": "60D"},
            {"name": "90D", "id": "90D"},
        ],
        data=df_view.to_dict("records"),
        style_data_conditional=[
            *[
                {"if": {"row_index": i, "column_id": col}, "borderTop": borders[i]}
                for i in range(len(df_view)) for col in ["SETOR", "INSPETOR", "30D", "60D", "90D"]
            ],
            *[
                {"if": {"row_index": i, "column_id": "30D"}, "backgroundColor": df_view.iloc[i]['COR_30'], "color": "black", "whiteSpace": "pre-line"}
                for i in range(len(df_view))
            ],
            *[
                {"if": {"row_index": i, "column_id": "60D"}, "backgroundColor": df_view.iloc[i]['COR_60'], "color": "black", "whiteSpace": "pre-line"}
                for i in range(len(df_view))
            ],
            *[
                {"if": {"row_index": i, "column_id": "90D"}, "backgroundColor": df_view.iloc[i]['COR_90'], "color": "black", "whiteSpace": "pre-line"}
                for i in range(len(df_view))
            ],
            {"if": {"column_id": "SETOR"}, "backgroundColor": "#2C3E50", "color": "white"},
            {"if": {"column_id": "INSPETOR"}, "backgroundColor": "#2C3E50", "color": "white"}
        ],
        style_cell={"textAlign": "center", "whiteSpace": "pre-line", "height": "auto", "fontFamily": "Roboto, sans-serif"},
        style_cell_conditional=[
            {"if": {"column_id": "INSPETOR"}, "width": "120px"},
            {"if": {"column_id": "SETOR"}, "width": "80px"}
        ],
        style_table={"overflowX": "auto", "borderRadius": "10px", "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)"},
        style_header={"position": "sticky", "top": 0, "zIndex": 1, "backgroundColor": "#2C3E50", "color": "white", "fontWeight": "bold"}
    )

    if setor_selecionado != "Todos" and setor_selecionado in rankings_dict:
        ranking = html.Div([
            html.H3(f"Ranking TOP 3 - Setor {setor_selecionado}"),
            dash_table.DataTable(
                columns=[
                    {"name": "Posição", "id": "Posição"},
                    {"name": "INSPETOR", "id": "INSPETOR"}
                ],
                data=rankings_dict[setor_selecionado][["Posição", "INSPETOR"]].to_dict("records"),
                style_cell={"textAlign": "center", "whiteSpace": "normal", "fontFamily": "Roboto, sans-serif"},
                style_header={"fontWeight": "bold", "backgroundColor": "#2C3E50", "color": "white"},
                style_table={"width": "100%", "marginBottom": "10px", "borderRadius": "10px", "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)"}
            )
        ])
    else:
        ranking = html.Div([
            html.H3("Ranking TOP 3 por Setor (30D)"),
            *[html.Div([
                html.H4(f"Setor {setor}"),
                dash_table.DataTable(
                    columns=[
                        {"name": "Posição", "id": "Posição"},
                        {"name": "INSPETOR", "id": "INSPETOR"}
                    ],
                    data=ranking[["Posição", "INSPETOR"]].to_dict("records"),
                    style_cell={"textAlign": "center", "whiteSpace": "normal", "fontFamily": "Roboto, sans-serif"},
                    style_header={"fontWeight": "bold", "backgroundColor": "#2C3E50", "color": "white"},
                    style_table={"width": "100%", "marginBottom": "10px", "borderRadius": "10px", "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)"}
                )
            ]) for setor, ranking in rankings_dict.items()]
        ])

    return html.Div([
        html.Div(tabela, style={"width": "75%", "display": "inline-block", "verticalAlign": "top"}),
        html.Div(ranking, style={"width": "24%", "display": "inline-block", "paddingLeft": "10px"})
    ])

if __name__ == '__main__':
     app.run(debug=True)