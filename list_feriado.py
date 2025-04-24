import streamlit as st
from datetime import date
from workalendar.america import Brazil

# Dicionário com feriados personalizados (independentes do ano)
FERIADOS_PERSONALIZADOS = {
    "São Paulo": [
        ((1, 25), "Aniversário da Cidade de São Paulo")
    ],
    "Rio de Janeiro": [
        ((1, 20), "Dia de São Sebastião")
    ]
}

# Função para calcular a data final
def calcular_data_final(data_inicial: str, numero_dias: int, municipio: str = None) -> str:
    # Converte a data inicial para um objeto datetime.date
    data_inicial = date.fromisoformat(data_inicial)
    
    # Instancia o calendário federal do Brasil
    cal = Brazil()
    
    # Adiciona feriados personalizados ao calendário
    if municipio and municipio in FERIADOS_PERSONALIZADOS:
        for (mes, dia), nome in FERIADOS_PERSONALIZADOS[municipio]:
            cal.add_holiday(f"{dia}/{mes}", nome)
    
    # Calcula a data final adicionando o número de dias úteis
    data_final = cal.add_working_days(data_inicial, numero_dias)
    
    return data_final.isoformat()

# Função para listar os feriados usados no cálculo
def listar_feriados_usados(ano: int, municipio: str = None):
    # Instancia o calendário federal do Brasil
    cal = Brazil()
    
    # Adiciona feriados personalizados ao calendário
    if municipio and municipio in FERIADOS_PERSONALIZADOS:
        for (mes, dia), nome in FERIADOS_PERSONALIZADOS[municipio]:
            cal.add_holiday(f"{dia}/{mes}", nome)
    
    # Obtém os feriados para o ano especificado
    feriados = cal.holidays(ano)
    return feriados

# Interface Streamlit
st.title("Calculadora de Data Final com Calendário de Feriados")

# Entrada de dados pelo usuário
st.subheader("Insira os dados:")
issue_key = st.text_input("Issue Key:", value="PROJ-123")
summary = st.text_input("Summary:", value="Descrição do Ticket")
data_inicial = st.text_input("Data Inicial (YYYY-MM-DD):", value="2023-10-01")
numero_dias = st.number_input("Número de Dias Úteis:", min_value=1, value=5)
municipio = st.selectbox("Município (opcional):", ["Nenhum"] + list(FERIADOS_PERSONALIZADOS.keys()))

# Botão para calcular a data final
if st.button("Calcular Data Final"):
    try:
        # Calcula a data final
        data_final = calcular_data_final(data_inicial, numero_dias, municipio if municipio != "Nenhum" else None)
        
        # Exibe os resultados
        st.subheader("Resultado:")
        st.write(f"**Foi recebida a seguinte issue:**")
        st.write(f"- **Key:** {issue_key}")
        st.write(f"- **Summary:** {summary}")
        st.write(f"- **Data de Saída:** {data_inicial}")
        st.write(f"- **Prazo do Contrato (dias úteis):** {numero_dias}")
        st.write(f"- **Data do Contrato Baseado em Calendário:** {data_final}")
        
        # Lista os feriados usados no cálculo
        ano_corrente = date.fromisoformat(data_inicial).year
        feriados_usados = listar_feriados_usados(ano_corrente, municipio if municipio != "Nenhum" else None)
        
        st.subheader("Calendário de Feriados Usado:")
        for data, nome in feriados_usados:
            st.write(f"- {data.strftime('%d/%m/%Y')} - {nome}")
    
    except Exception as e:
        st.error(f"Ocorreu um erro: {str(e)}")