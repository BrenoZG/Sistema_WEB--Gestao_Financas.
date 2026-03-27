"""
Modelos do banco de dados (SQLAlchemy ORM).

O que é ORM?
- ORM = Object-Relational Mapper
- Permite trabalhar com tabelas do banco como se fossem classes Python
- Você não escreve SQL na mão — o SQLAlchemy gera o SQL automaticamente

Estrutura de entidades:
    OrcamentoMensal  →  1 por mês/ano (ancora os cálculos)
        ├── FonteReceita  →  receitas do mês (salário, freelance etc.)
        └── Transacao     →  todos os gastos do mês

    Categoria  →  tipos de gasto (Aluguel, Alimentação etc.)
        └── Transacao  →  cada gasto pertence a uma categoria
"""
from datetime import date, datetime
from app import db


class OrcamentoMensal(db.Model):
    """Orçamento configurado para um mês específico.

    É a âncora de todos os cálculos do dashboard.
    Sem um OrcamentoMensal, o dashboard não tem o que mostrar.

    Exemplo:
        orcamento = OrcamentoMensal(mes=3, ano=2026, receita_prevista=5000.0)
    """

    __tablename__ = "orcamento_mensal"

    id: int = db.Column(db.Integer, primary_key=True)
    mes: int = db.Column(db.Integer, nullable=False)        # 1 a 12
    ano: int = db.Column(db.Integer, nullable=False)        # ex: 2026
    receita_prevista: float = db.Column(db.Float, nullable=False, default=0.0)
    percentual_poupanca: float = db.Column(db.Float, nullable=False, default=10.0)
    criado_em: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos (Flask-SQLAlchemy conecta as tabelas automaticamente)
    # cascade="all, delete-orphan": ao deletar o orçamento, deleta os filhos
    transacoes = db.relationship(
        "Transacao", backref="orcamento", lazy=True, cascade="all, delete-orphan"
    )
    fontes_receita = db.relationship(
        "FonteReceita", backref="orcamento", lazy=True, cascade="all, delete-orphan"
    )

    # --- Propriedades calculadas (Python faz a conta, não o banco) ---

    @property
    def valor_poupanca(self) -> float:
        """Valor absoluto reservado para poupança. Ex: 10% de R$5.000 = R$500."""
        return self.receita_prevista * self.percentual_poupanca / 100

    @property
    def disponivel_para_gastos(self) -> float:
        """Receita disponível após separar a poupança. Ex: R$5.000 - R$500 = R$4.500."""
        return self.receita_prevista - self.valor_poupanca

    @property
    def total_gasto(self) -> float:
        """Soma de todos os gastos do mês até agora."""
        return sum(t.valor for t in self.transacoes if t.tipo == "gasto")

    @property
    def saldo_restante(self) -> float:
        """Quanto ainda dá para gastar. Negativo = estourou o orçamento."""
        return self.disponivel_para_gastos - self.total_gasto

    @property
    def percentual_utilizado(self) -> float:
        """Porcentagem do orçamento já utilizada. Ex: 42.5 (%)"""
        if self.disponivel_para_gastos <= 0:
            return 0.0
        return min((self.total_gasto / self.disponivel_para_gastos) * 100, 100.0)

    def __repr__(self) -> str:
        return f"<OrcamentoMensal {self.mes:02d}/{self.ano}>"


class Categoria(db.Model):
    """Categoria de gasto (Aluguel, Alimentação, Cartão Santander etc.).

    Populada automaticamente na primeira vez que o app roda.

    Atributos:
        nome: Nome exibido na interface. Ex: "Alimentação"
        icone: Nome do ícone Bootstrap Icons. Ex: "bi-cart-fill"
        cor: Cor hex para gráficos. Ex: "#2ecc71"
        eh_cartao_credito: True = esta categoria representa o cartão Santander
    """

    __tablename__ = "categoria"

    id: int = db.Column(db.Integer, primary_key=True)
    nome: str = db.Column(db.String(50), nullable=False, unique=True)
    icone: str = db.Column(db.String(50), nullable=False, default="bi-tag-fill")
    cor: str = db.Column(db.String(10), nullable=False, default="#95a5a6")
    eh_cartao_credito: bool = db.Column(db.Boolean, nullable=False, default=False)

    transacoes = db.relationship("Transacao", backref="categoria", lazy=True)

    def __repr__(self) -> str:
        return f"<Categoria {self.nome}>"


class Transacao(db.Model):
    """Um lançamento financeiro (gasto ou receita avulsa).

    Esta é a tabela mais importante do sistema.
    Cada compra no cartão, cada conta paga, entra aqui.

    Atributos:
        tipo: "gasto" ou "receita"
        eh_cartao_credito: True = foi uma compra no cartão Santander
        observacoes: Notas livres (opcional)
    """

    __tablename__ = "transacao"

    id: int = db.Column(db.Integer, primary_key=True)
    orcamento_id: int = db.Column(
        db.Integer, db.ForeignKey("orcamento_mensal.id"), nullable=False
    )
    categoria_id: int = db.Column(
        db.Integer, db.ForeignKey("categoria.id"), nullable=False
    )
    descricao: str = db.Column(db.String(200), nullable=False)
    valor: float = db.Column(db.Float, nullable=False)
    data_transacao: date = db.Column(db.Date, nullable=False, default=date.today)
    tipo: str = db.Column(db.String(10), nullable=False, default="gasto")  # "gasto" | "receita"
    eh_cartao_credito: bool = db.Column(db.Boolean, nullable=False, default=False)
    observacoes: str = db.Column(db.String(500), nullable=True)
    criado_em: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Transacao {self.descricao} R${self.valor:.2f}>"


class FonteReceita(db.Model):
    """Uma fonte de receita do mês (salário, freelance, bônus etc.).

    Diferente de Transacao (que pode ser gasto ou receita avulsa),
    FonteReceita é usado para planejar e registrar de onde vem o dinheiro.

    Atributos:
        recorrente: True = aparece todo mês (ex: salário fixo)
    """

    __tablename__ = "fonte_receita"

    id: int = db.Column(db.Integer, primary_key=True)
    orcamento_id: int = db.Column(
        db.Integer, db.ForeignKey("orcamento_mensal.id"), nullable=False
    )
    descricao: str = db.Column(db.String(100), nullable=False)
    valor: float = db.Column(db.Float, nullable=False)
    data_recebimento: date = db.Column(db.Date, nullable=True)
    recorrente: bool = db.Column(db.Boolean, nullable=False, default=False)
    criado_em: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<FonteReceita {self.descricao} R${self.valor:.2f}>"
