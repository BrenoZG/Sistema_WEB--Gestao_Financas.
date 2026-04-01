"""
Script avulso para adicionar novas categorias ao banco existente.
Execute UMA VEZ com: python adicionar_categorias.py
Após rodar com sucesso, pode deletar este arquivo.
"""
from dotenv import load_dotenv
load_dotenv()

from app import criar_app, db
from app.models import Categoria

app = criar_app()

with app.app_context():
    novas = [
        Categoria(nome="Casa",     icone="bi-tools",          cor="#5d8aa8", eh_cartao_credito=False),
        Categoria(nome="Mercado",  icone="bi-bag-fill",       cor="#27ae60", eh_cartao_credito=False),
        Categoria(nome="Internet", icone="bi-wifi",           cor="#8e44ad", eh_cartao_credito=False),
    ]

    adicionadas = []
    for cat in novas:
        existe = Categoria.query.filter_by(nome=cat.nome).first()
        if existe:
            print(f"  [JÁ EXISTE] {cat.nome} — pulando")
        else:
            db.session.add(cat)
            adicionadas.append(cat.nome)

    db.session.commit()

    if adicionadas:
        print(f"\nCategorias adicionadas com sucesso: {', '.join(adicionadas)}")
    else:
        print("\nNenhuma categoria nova foi inserida.")

    print("\nCategorias atuais no banco:")
    for c in Categoria.query.order_by(Categoria.id).all():
        print(f"  {c.id:2}. {c.nome}")
