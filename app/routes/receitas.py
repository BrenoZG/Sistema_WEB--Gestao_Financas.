"""
Rotas para gerenciamento de receitas mensais.

Aqui o usuário registra de onde vem o dinheiro do mês:
salário, freelance, bônus, aluguel recebido etc.
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import OrcamentoMensal, FonteReceita

receitas_bp = Blueprint("receitas", __name__)


@receitas_bp.route("/")
def listar():
    """Lista as fontes de receita do mês atual."""
    hoje = date.today()
    mes = int(request.args.get("mes", hoje.month))
    ano = int(request.args.get("ano", hoje.year))

    orcamento = OrcamentoMensal.query.filter_by(ano=ano, mes=mes).first()
    receitas = []
    total_recebido = 0.0

    if orcamento:
        receitas = (
            FonteReceita.query
            .filter_by(orcamento_id=orcamento.id)
            .order_by(FonteReceita.data_recebimento.desc())
            .all()
        )
        total_recebido = sum(r.valor for r in receitas)

    return render_template(
        "receitas/lista.html",
        receitas=receitas,
        orcamento=orcamento,
        total_recebido=total_recebido,
        mes=mes,
        ano=ano,
    )


@receitas_bp.route("/adicionar", methods=["POST"])
def adicionar():
    """Adiciona uma nova fonte de receita."""
    hoje = date.today()
    descricao = request.form.get("descricao", "").strip()
    valor_str = request.form.get("valor", "0").replace(",", ".")
    data_str = request.form.get("data_recebimento", str(hoje))
    recorrente = request.form.get("recorrente") == "on"
    mes = int(request.form.get("mes", hoje.month))
    ano = int(request.form.get("ano", hoje.year))

    if not descricao:
        flash("A descrição é obrigatória.", "erro")
        return redirect(url_for("receitas.listar", mes=mes, ano=ano))

    try:
        valor = float(valor_str)
        if valor <= 0:
            raise ValueError
    except ValueError:
        flash("Informe um valor válido maior que zero.", "erro")
        return redirect(url_for("receitas.listar", mes=mes, ano=ano))

    # Garante que o orçamento existe
    orcamento = OrcamentoMensal.query.filter_by(ano=ano, mes=mes).first()
    if not orcamento:
        orcamento = OrcamentoMensal(ano=ano, mes=mes, receita_prevista=0.0)
        db.session.add(orcamento)
        db.session.flush()  # Gera o ID sem commitar ainda

    data = date.fromisoformat(data_str) if data_str else None

    receita = FonteReceita(
        orcamento_id=orcamento.id,
        descricao=descricao,
        valor=valor,
        data_recebimento=data,
        recorrente=recorrente,
    )
    db.session.add(receita)
    db.session.commit()

    flash(f'Receita "{descricao}" adicionada com sucesso!', "sucesso")
    return redirect(url_for("receitas.listar", mes=mes, ano=ano))


@receitas_bp.route("/<int:id>/excluir", methods=["POST"])
def excluir(id: int):
    """Exclui uma fonte de receita."""
    receita = FonteReceita.query.get_or_404(id)
    descricao = receita.descricao
    mes = receita.orcamento.mes
    ano = receita.orcamento.ano

    db.session.delete(receita)
    db.session.commit()

    flash(f'Receita "{descricao}" removida.', "sucesso")
    return redirect(url_for("receitas.listar", mes=mes, ano=ano))
