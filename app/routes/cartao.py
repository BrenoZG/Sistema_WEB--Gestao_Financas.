"""
Rota para visualização das transações do Cartão Santander.

Filtra apenas transações onde eh_cartao_credito=True,
dando uma visão focada do uso do cartão no mês.
"""
from datetime import date
from flask import Blueprint, render_template, request
from app.models import OrcamentoMensal, Transacao

cartao_bp = Blueprint("cartao", __name__)


@cartao_bp.route("/")
def listar():
    """Exibe as transações do Cartão Santander do mês atual."""
    hoje = date.today()
    mes = int(request.args.get("mes", hoje.month))
    ano = int(request.args.get("ano", hoje.year))

    orcamento = OrcamentoMensal.query.filter_by(ano=ano, mes=mes).first()
    transacoes_cartao = []
    total_cartao = 0.0

    if orcamento:
        transacoes_cartao = (
            Transacao.query
            .filter_by(orcamento_id=orcamento.id, eh_cartao_credito=True)
            .order_by(Transacao.data_transacao.desc())
            .all()
        )
        total_cartao = sum(t.valor for t in transacoes_cartao)

    # Navegação entre meses
    mes_anterior = mes - 1 if mes > 1 else 12
    ano_anterior = ano if mes > 1 else ano - 1
    proximo_mes = mes + 1 if mes < 12 else 1
    proximo_ano = ano if mes < 12 else ano + 1

    nomes_meses = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    return render_template(
        "cartao/lista.html",
        transacoes=transacoes_cartao,
        total_cartao=total_cartao,
        orcamento=orcamento,
        mes=mes,
        ano=ano,
        nome_mes=nomes_meses[mes],
        mes_anterior=mes_anterior,
        ano_anterior=ano_anterior,
        proximo_mes=proximo_mes,
        proximo_ano=proximo_ano,
    )
