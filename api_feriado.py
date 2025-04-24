from flask import Flask, request, jsonify

app = Flask(__name__)

# Armazenamento temporário dos dados recebidos (em memória)
dados_recebidos = []

# Rota para receber os dados do Jira via Webhook
@app.route('/receber-dados', methods=['POST'])
def receber_dados():
    try:
        # Obtém os dados do corpo da requisição
        data = request.json
        
        # Adiciona os dados à lista de dados recebidos
        dados_recebidos.append(data)
        
        # Retorna uma resposta de sucesso
        return jsonify({"mensagem": "Dados recebidos com sucesso!"}), 200
    
    except Exception as e:
        # Trata erros inesperados
        return jsonify({"erro": str(e)}), 500

# Rota para consultar os dados recebidos
@app.route('/consultar-dados', methods=['GET'])
def consultar_dados():
    try:
        # Retorna os dados armazenados
        return jsonify(dados_recebidos), 200
    
    except Exception as e:
        # Trata erros inesperados
        return jsonify({"erro": str(e)}), 500

# Executa a aplicação
if __name__ == '__main__':
    app.run(debug=True, port=5000)