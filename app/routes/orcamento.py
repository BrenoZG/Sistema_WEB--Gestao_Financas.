"""
Rotas para configuração do orçamento mensal.

O orçamento é o ponto de partida: antes de lançar gastos,
o usuário precisa configurar a receita prevista do mês.
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import OrcamentoMensal

orcamento_bp = Blueprint("orcamento", __name__)


@orcamento_bp.route("/<int:ano>/<int:mes>", methods=["GET", "POST"])
def configurar(ano: int, mes: int):
    """Exibe e processa o formulário de configuração do orçamento mensal.

    Args:
        ano: Ano do orçamento (ex: 2026)
        mes: Mês do orçamento (1 a 12)
    """
    orcamento = OrcamentoMensal.query.filter_by(ano=ano, mes=mes).first()

    if request.method == "POST":
        receita_prevista = float(request.form.get("receita_prevista", 0))
        percentual_poupanca = float(request.form.get("percentual_poupanca", 10.0))

        if orcamento:
            # Atualiza orçamento existente
            orcamento.receita_prevista = receita_prevista
            orcamento.percentual_poupanca = percentual_poupanca
        else:
            # Cria novo orçamento para este mês
            orcamento = OrcamentoMensal(
                ano=ano,
                mes=mes,
                receita_prevista=receita_prevista,
                percentual_poupanca=percentual_poupanca,
            )
            db.session.add(orcamento)

        db.session.commit()
        flash(f"Orçamento de {_nome_mes(mes)}/{ano} salvo com sucesso!", "sucesso")
        return redirect(url_for("dashboard.dashboard", ano=ano, mes=mes))

    nomes_meses = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    return render_template(
        "orcamento/form.html",
        orcamento=orcamento,
        ano=ano,
        mes=mes,
        nome_mes=nomes_meses[mes],
    )


def _nome_mes(mes: int) -> str:
    """Retorna o nome do mês em português."""
    nomes = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    return nomes[mes] if 1 <= mes <= 12 else str(mes)
