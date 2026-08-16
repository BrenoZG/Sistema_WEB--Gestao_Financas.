"""
Factory da aplicação Flask.

Por que usar uma factory (criar_app)?
- Permite criar múltiplas instâncias do app (útil para testes)
- Evita importações circulares
- Centraliza toda a configuração em um lugar só
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Instância do banco — criada aqui, inicializada dentro do criar_app
db = SQLAlchemy()


def criar_app() -> Flask:
    """Cria e configura a aplicação Flask.

    Returns:
        Flask: Instância configurada da aplicação.
    """
    app = Flask(__name__)

    # --- Configurações ---
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-inseguro-mude-em-producao")
    app.config["SQLALCHEMY_DATABASE_URI"] = _resolver_url_banco()
    # Desativa rastreamento de modificações (economiza memória)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Inicializa extensões ---
    db.init_app(app)

    # --- Registra blueprints (grupos de rotas) ---
    from app.routes.dashboard import dashboard_bp
    from app.routes.transacoes import transacoes_bp
    from app.routes.receitas import receitas_bp
    from app.routes.cartao import cartao_bp
    from app.routes.orcamento import orcamento_bp
    from app.routes.categorias import categorias_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transacoes_bp, url_prefix="/transacoes")
    app.register_blueprint(receitas_bp, url_prefix="/receitas")
    app.register_blueprint(cartao_bp, url_prefix="/cartao")
    app.register_blueprint(orcamento_bp, url_prefix="/configurar")
    app.register_blueprint(categorias_bp, url_prefix="/categorias")

    # --- Filtro de formatação de moeda (usado nos templates) ---
    @app.template_filter("moeda")
    def filtro_moeda(valor: float) -> str:
        """Formata um número como moeda brasileira. Ex: 1234.56 → R$ 1.234,56"""
        if valor is None:
            return "R$ 0,00"
        formatado = f"{valor:,.2f}"
        # Converte separadores: 1,234.56 → 1.234,56
        return "R$ " + formatado.replace(",", "X").replace(".", ",").replace("X", ".")

    # --- Cria tabelas e popula categorias padrão ---
    with app.app_context():
        from app.models import OrcamentoMensal, Categoria, Transacao, FonteReceita
        db.create_all()
        _popular_categorias_padrao()

    return app


def _resolver_url_banco() -> str:
    """Resolve a URL do banco a partir do ambiente, com SQLite como padrao.

    Sem esta funcao, `DATABASE_URL` era documentada no `.env.example` e nunca
    lida: a URI ficava fixa em SQLite. Em hospedagem com disco efemero isso
    significa perder o banco inteiro a cada novo deploy, sem nenhum erro no log
    - o app sobe, cria as tabelas vazias e segue como se estivesse tudo certo.

    O ajuste de esquema tambem e necessario: Railway e Heroku entregam a URL
    comecando com `postgres://`, um alias que o SQLAlchemy 2.x nao reconhece
    mais. Sem a troca, a conexao falha na inicializacao.

    Returns:
        str: URI de conexao pronta para o SQLAlchemy.
    """
    url = os.getenv("DATABASE_URL", "").strip()

    if not url:
        return "sqlite:///financeiro.db"

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


def _popular_categorias_padrao() -> None:
    """Insere as categorias padrão se a tabela estiver vazia.

    Executado uma única vez na primeira inicialização do app.
    """
    from app.models import Categoria

    if Categoria.query.count() > 0:
        return  # Já populado, não faz nada

    categorias_padrao = [
        Categoria(nome="Aluguel",           icone="bi-house-fill",        cor="#e74c3c", eh_cartao_credito=False),
        Categoria(nome="Cartão Santander",  icone="bi-credit-card-fill",  cor="#e67e22", eh_cartao_credito=True),
        Categoria(nome="Alimentação",       icone="bi-cart-fill",         cor="#2ecc71", eh_cartao_credito=False),
        Categoria(nome="Transporte",        icone="bi-car-front-fill",    cor="#3498db", eh_cartao_credito=False),
        Categoria(nome="Saúde",             icone="bi-heart-pulse-fill",  cor="#9b59b6", eh_cartao_credito=False),
        Categoria(nome="Lazer",             icone="bi-controller",        cor="#1abc9c", eh_cartao_credito=False),
        Categoria(nome="Educação",          icone="bi-book-fill",         cor="#f39c12", eh_cartao_credito=False),
        Categoria(nome="Outros",            icone="bi-three-dots",        cor="#95a5a6", eh_cartao_credito=False),
    ]

    db.session.add_all(categorias_padrao)
    db.session.commit()
