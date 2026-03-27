"""
Rota do dashboard principal.

Aqui ficam todos os cálculos financeiros do mês:
receita prevista, gastos, saldo, poupança, etc.
Toda a lógica é feita em Python — o template apenas exibe os resultados.
"""
from datetime import date
from collections import defaultdict
from flask import Blueprint, render_template, redirect, url_for
from app.models import OrcamentoMensal, Transacao, Categoria


dashboard_bp = Blueprint("dashboard", __name__)

NOMES_MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


@dashboard_bp.route("/")
def index():
    """Redireciona para o dashboard do mês atual."""
    hoje = date.today()
    return redirect(url_for("dashboard.dashboard", ano=hoje.year, mes=hoje.month))


@dashboard_bp.route("/dashboard/<int:ano>/<int:mes>")
def dashboard(ano: int, mes: int):
    """Página principal do dashboard financeiro.

    Calcula todos os indicadores financeiros do mês e passa
    para o template renderizar os cards e gráficos.

    Args:
        ano: Ano a exibir
        mes: Mês a exibir (1-12)
    """
    orcamento = OrcamentoMensal.query.filter_by(ano=ano, mes=mes).first()

    # --- Navegação entre meses ---
    mes_anterior, ano_anterior = _mes_anterior(mes, ano)
    proximo_mes, proximo_ano = _proximo_mes(mes, ano)

    if not orcamento:
        # Mês sem orçamento configurado — mostra tela de configuração
        return render_template(
            "dashboard/sem_orcamento.html",
            ano=ano,
            mes=mes,
            nome_mes=NOMES_MESES[mes],
            mes_anterior=mes_anterior,
            ano_anterior=ano_anterior,
            proximo_mes=proximo_mes,
            proximo_ano=proximo_ano,
        )

    # --- Transações do mês ---
    transacoes = (
        Transacao.query
        .filter_by(orcamento_id=orcamento.id)
        .order_by(Transacao.data_transacao.desc(), Transacao.criado_em.desc())
        .all()
    )

    # --- Gastos por categoria (para o gráfico donut) ---
    gastos_por_categoria: dict[str, float] = defaultdict(float)
    cores_categorias: dict[str, str] = {}

    for transacao in transacoes:
        if transacao.tipo == "gasto":
            nome_cat = transacao.categoria.nome
            gastos_por_categoria[nome_cat] += transacao.valor
            cores_categorias[nome_cat] = transacao.categoria.cor

    # Ordena do maior para o menor (para o gráfico ficar mais legível)
    gastos_ordenados = sorted(gastos_por_categoria.items(), key=lambda x: x[1], reverse=True)

    # --- Dados para o gráfico de barras (evolução diária) ---
    gastos_diarios: dict[str, float] = defaultdict(float)
    for transacao in transacoes:
        if transacao.tipo == "gasto":
            dia = transacao.data_transacao.strftime("%d/%m")
            gastos_diarios[dia] += transacao.valor
    gastos_diarios_ordenados = sorted(gastos_diarios.items())

    # --- Últimas 10 transações para a lista no dashboard ---
    ultimas_transacoes = transacoes[:10]

    # --- Categorias para o formulário quick-add ---
    categorias_quick_add = Categoria.query.order_by(Categoria.nome).all()

    # Cor do saldo (verde = positivo, vermelho = negativo)
    cor_saldo = "success" if orcamento.saldo_restante >= 0 else "danger"

    # Cor da barra de progresso
    pct = orcamento.percentual_utilizado
    cor_barra = "success" if pct < 70 else "warning" if pct < 90 else "danger"

    return render_template(
        "dashboard/index.html",
        orcamento=orcamento,
        ano=ano,
        mes=mes,
        nome_mes=NOMES_MESES[mes],
        ultimas_transacoes=ultimas_transacoes,
        # Gráfico donut
        categorias_labels=[c[0] for c in gastos_ordenados],
        categorias_valores=[c[1] for c in gastos_ordenados],
        categorias_cores=[cores_categorias[c[0]] for c in gastos_ordenados],
        # Gráfico barras
        dias_labels=[d[0] for d in gastos_diarios_ordenados],
        dias_valores=[d[1] for d in gastos_diarios_ordenados],
        # Quick-add
        categorias_para_quick_add=categorias_quick_add,
        # Estética
        cor_saldo=cor_saldo,
        cor_barra=cor_barra,
        # Navegação
        mes_anterior=mes_anterior,
        ano_anterior=ano_anterior,
        proximo_mes=proximo_mes,
        proximo_ano=proximo_ano,
    )


def _mes_anterior(mes: int, ano: int) -> tuple[int, int]:
    """Retorna (mes, ano) do mês anterior."""
    if mes == 1:
        return 12, ano - 1
    return mes - 1, ano


def _proximo_mes(mes: int, ano: int) -> tuple[int, int]:
    """Retorna (mes, ano) do próximo mês."""
    if mes == 12:
        return 1, ano + 1
    return mes + 1, ano
