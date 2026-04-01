"""
Rotas para gerenciamento de categorias.
Permite adicionar e excluir categorias diretamente pela interface.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Categoria, Transacao

categorias_bp = Blueprint("categorias", __name__)


@categorias_bp.route("/")
def listar():
    """Lista todas as categorias com contagem de uso."""
    categorias = Categoria.query.order_by(Categoria.nome).all()

    # Conta quantas transações cada categoria tem (para exibir e bloquear exclusão)
    uso = {
        c.id: Transacao.query.filter_by(categoria_id=c.id).count()
        for c in categorias
    }

    return render_template("categorias/lista.html", categorias=categorias, uso=uso)


@categorias_bp.route("/adicionar", methods=["POST"])
def adicionar():
    """Adiciona uma nova categoria."""
    nome = request.form.get("nome", "").strip()
    cor = request.form.get("cor", "#95a5a6").strip()
    icone = request.form.get("icone", "bi-tag-fill").strip()
    eh_cartao = request.form.get("eh_cartao_credito") == "on"

    if not nome:
        flash("O nome da categoria é obrigatório.", "erro")
        return redirect(url_for("categorias.listar"))

    if Categoria.query.filter_by(nome=nome).first():
        flash(f'Já existe uma categoria com o nome "{nome}".', "erro")
        return redirect(url_for("categorias.listar"))

    # Garante que o ícone começa com "bi-"
    if not icone.startswith("bi-"):
        icone = "bi-tag-fill"

    categoria = Categoria(nome=nome, cor=cor, icone=icone, eh_cartao_credito=eh_cartao)
    db.session.add(categoria)
    db.session.commit()

    flash(f'Categoria "{nome}" criada com sucesso!', "sucesso")
    return redirect(url_for("categorias.listar"))


@categorias_bp.route("/<int:id>/excluir", methods=["POST"])
def excluir(id: int):
    """Exclui uma categoria, impedindo exclusão se houver transações vinculadas."""
    categoria = Categoria.query.get_or_404(id)

    total_uso = Transacao.query.filter_by(categoria_id=id).count()
    if total_uso > 0:
        flash(
            f'Não é possível excluir "{categoria.nome}": '
            f'há {total_uso} transação(ões) vinculada(s). '
            f'Reatribua-as antes de excluir.',
            "erro"
        )
        return redirect(url_for("categorias.listar"))

    nome = categoria.nome
    db.session.delete(categoria)
    db.session.commit()

    flash(f'Categoria "{nome}" excluída.', "sucesso")
    return redirect(url_for("categorias.listar"))
