"""
Rotas para gerenciamento de transações (gastos e receitas avulsas).

Funcionalidades:
- Listar transações com filtros
- Adicionar nova transação (formulário completo)
- Quick-add via HTMX (sem reload de página — ideal para celular)
- Excluir transação
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import OrcamentoMensal, Transacao, Categoria

transacoes_bp = Blueprint("transacoes", __name__)


def _obter_ou_criar_orcamento(ano: int, mes: int) -> OrcamentoMensal:
    """Retorna o orçamento do mês, criando um vazio se não existir.

    Isso evita erro ao lançar uma transação sem orçamento configurado.
    O usuário pode configurar o orçamento depois.
    """
    orcamento = OrcamentoMensal.query.filter_by(ano=ano, mes=mes).first()
    if not orcamento:
        orcamento = OrcamentoMensal(ano=ano, mes=mes, receita_prevista=0.0)
        db.session.add(orcamento)
        db.session.commit()
    return orcamento


@transacoes_bp.route("/")
def listar():
    """Lista todas as transações com filtros opcionais."""
    hoje = date.today()
    # Filtros via query string (?mes=3&ano=2026&categoria_id=2)
    mes = int(request.args.get("mes", hoje.month))
    ano = int(request.args.get("ano", hoje.year))
    categoria_id = request.args.get("categoria_id", type=int)
    tipo = request.args.get("tipo", "")  # "gasto", "receita" ou "" (todos)

    orcamento = OrcamentoMensal.query.filter_by(ano=ano, mes=mes).first()

    query = Transacao.query
    if orcamento:
        query = query.filter_by(orcamento_id=orcamento.id)
    else:
        # Sem orçamento = sem transações neste mês
        query = query.filter_by(id=-1)

    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    if tipo:
        query = query.filter_by(tipo=tipo)

    transacoes = query.order_by(
        Transacao.data_transacao.desc(),
        Transacao.criado_em.desc()
    ).all()

    categorias = Categoria.query.order_by(Categoria.nome).all()

    return render_template(
        "transacoes/lista.html",
        transacoes=transacoes,
        categorias=categorias,
        mes=mes,
        ano=ano,
        categoria_id_filtro=categoria_id,
        tipo_filtro=tipo,
        orcamento=orcamento,
    )


@transacoes_bp.route("/adicionar", methods=["GET", "POST"])
def adicionar():
    """Formulário completo para adicionar nova transação."""
    hoje = date.today()
    categorias = Categoria.query.order_by(Categoria.nome).all()

    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()
        valor_str = request.form.get("valor", "0").replace(",", ".")
        tipo = request.form.get("tipo", "gasto")
        categoria_id = int(request.form.get("categoria_id"))
        data_str = request.form.get("data_transacao", str(hoje))
        eh_cartao = request.form.get("eh_cartao_credito") == "on"
        observacoes = request.form.get("observacoes", "").strip()

        # Validações básicas
        if not descricao:
            flash("A descrição é obrigatória.", "erro")
            return render_template("transacoes/form.html", categorias=categorias, hoje=hoje)

        try:
            valor = float(valor_str)
            if valor <= 0:
                raise ValueError
        except ValueError:
            flash("Informe um valor válido maior que zero.", "erro")
            return render_template("transacoes/form.html", categorias=categorias, hoje=hoje)

        data = date.fromisoformat(data_str)
        orcamento = _obter_ou_criar_orcamento(data.year, data.month)

        # Verifica se a categoria selecionada é de cartão de crédito
        categoria = Categoria.query.get(categoria_id)
        if categoria and categoria.eh_cartao_credito:
            eh_cartao = True

        transacao = Transacao(
            orcamento_id=orcamento.id,
            categoria_id=categoria_id,
            descricao=descricao,
            valor=valor,
            data_transacao=data,
            tipo=tipo,
            eh_cartao_credito=eh_cartao,
            observacoes=observacoes or None,
        )
        db.session.add(transacao)
        db.session.commit()

        flash(f"{'Gasto' if tipo == 'gasto' else 'Receita'} \"{descricao}\" adicionado com sucesso!", "sucesso")
        return redirect(url_for("dashboard.dashboard", ano=data.year, mes=data.month))

    return render_template("transacoes/form.html", categorias=categorias, hoje=hoje)


@transacoes_bp.route("/rapido", methods=["POST"])
def rapido():
    """Quick-add via HTMX: adiciona transação e retorna HTML parcial.

    Este endpoint é chamado pelo formulário rápido no dashboard.
    Em vez de retornar uma página inteira, retorna apenas a linha
    da nova transação — o HTMX insere ela na lista sem recarregar.

    Se o HTMX não estiver disponível (ex: JavaScript desabilitado),
    redireciona para o dashboard normalmente.
    """
    hoje = date.today()
    descricao = request.form.get("descricao", "").strip() or "Gasto rápido"
    valor_str = request.form.get("valor", "0").replace(",", ".")
    categoria_id = int(request.form.get("categoria_id", 1))

    try:
        valor = float(valor_str)
        if valor <= 0:
            valor = 0.01
    except ValueError:
        valor = 0.01

    orcamento = _obter_ou_criar_orcamento(hoje.year, hoje.month)
    categoria = Categoria.query.get(categoria_id)

    transacao = Transacao(
        orcamento_id=orcamento.id,
        categoria_id=categoria_id,
        descricao=descricao,
        valor=valor,
        data_transacao=hoje,
        tipo="gasto",
        eh_cartao_credito=categoria.eh_cartao_credito if categoria else False,
    )
    db.session.add(transacao)
    db.session.commit()

    # Verifica se a requisição veio do HTMX
    if request.headers.get("HX-Request"):
        return render_template("transacoes/_linha.html", transacao=transacao)

    # Fallback: redireciona normalmente
    return redirect(url_for("dashboard.dashboard", ano=hoje.year, mes=hoje.month))


@transacoes_bp.route("/<int:id>/excluir", methods=["POST"])
def excluir(id: int):
    """Exclui uma transação pelo ID."""
    transacao = Transacao.query.get_or_404(id)
    descricao = transacao.descricao
    ano = transacao.data_transacao.year
    mes = transacao.data_transacao.month

    db.session.delete(transacao)
    db.session.commit()

    flash(f'"{descricao}" removido com sucesso.', "sucesso")

    # Retorna para a página de origem (dashboard ou lista)
    origem = request.form.get("origem", "dashboard")
    if origem == "lista":
        return redirect(url_for("transacoes.listar", ano=ano, mes=mes))
    return redirect(url_for("dashboard.dashboard", ano=ano, mes=mes))
