"""
Ponto de entrada da aplicação Financeiro.

Execute com:
    python run.py

Acesso pelo celular (mesma rede Wi-Fi):
    http://<ip-do-seu-pc>:5000
    Para descobrir o IP: rode 'ipconfig' no CMD e procure 'Endereço IPv4'
"""
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env antes de criar o app
load_dotenv()

from app import criar_app

app = criar_app()

if __name__ == "__main__":
    # host="0.0.0.0" permite acesso pelo celular na mesma rede Wi-Fi
    app.run(
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        host="0.0.0.0",
        port=5000,
    )
