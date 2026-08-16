# Gestão de Finanças

Aplicação web em Flask para controle de orçamento pessoal: define quanto entra no
mês, separa a poupança antes dos gastos e acompanha o que sobra em tempo real.

**Stack:** Python 3.10+ · Flask 3 · SQLAlchemy · Jinja2 · SQLite/PostgreSQL
**Dependências:** 4 pacotes para rodar, nenhum framework de front-end

---

## O problema

Planilha de controle financeiro morre no terceiro mês. Não por falta de
disciplina — por atrito: abrir o arquivo, achar a aba do mês, inserir a linha
no lugar certo, conferir se a fórmula pegou. Cada passo é uma chance de desistir,
e o gasto de R$ 12 no almoço nunca compensa o esforço de registrar.

O objetivo aqui foi remover o atrito do lançamento e fazer a pergunta que importa
— *quanto ainda posso gastar este mês?* — ser respondida sem nenhum clique.

---

## Decisões de projeto

### O mês é a âncora do modelo

`OrcamentoMensal` não é uma tabela de apoio: é a entidade da qual tudo depende.
Transações e fontes de receita pertencem a um mês, nunca soltas no banco.

A alternativa seria guardar transações com uma data e agrupar por mês na
consulta. Funciona, e perde a informação que interessa: um mês **existe** mesmo
sem nenhum lançamento, porque o orçamento previsto e o percentual de poupança
foram definidos antes do primeiro gasto. Sem a entidade, não há onde guardar a
intenção — só o histórico.

### Valor calculado, nunca armazenado

Saldo restante, total gasto, percentual utilizado e valor da poupança são
`@property` no modelo. Não existe coluna para nenhum deles.

Guardar um total no banco cria a classe de bug mais difícil de rastrear em
sistema financeiro: o valor derivado que ficou defasado. Alguém edita uma
transação por um caminho que esqueceu de atualizar o total, e a partir daí o
número exibido está errado — sem erro, sem log, sem sintoma até alguém conferir
na mão.

O custo é recalcular a cada exibição. Para o volume de um orçamento pessoal
— dezenas de linhas por mês — isso é irrelevante perto de exibir um saldo errado.

### Poupança sai antes, não sobra depois

`disponivel_para_gastos = receita_prevista − valor_poupanca`.

O saldo que a tela mostra já desconta a poupança. Não é detalhe de fórmula, é o
comportamento que o sistema quer induzir: poupar o que sobra no fim do mês
quase nunca funciona, porque o que sobra é definido pelo gasto. Invertendo a
ordem, o gasto é que passa a ser limitado pelo que já foi reservado.

### Blueprints por domínio, não um arquivo só

Seis blueprints — `dashboard`, `transacoes`, `receitas`, `cartao`, `orcamento`,
`categorias` — cada um com prefixo de URL próprio. Um `app.py` único com todas as
rotas é mais rápido de começar e vira ilegível por volta da rota quinze.

### Configuração por ambiente

`DATABASE_URL` define o banco: ausente, usa SQLite local; presente, usa o que
vier. O código também converte `postgres://` para `postgresql://`, porque Railway
e Heroku ainda entregam a URL no alias antigo que o SQLAlchemy 2.x não aceita.

Nenhuma credencial no código. `SECRET_KEY` vem do ambiente, com um valor de
desenvolvimento explicitamente marcado como inseguro.

---

## Estrutura

```
.
├─ run.py                    Ponto de entrada local
├─ Procfile                  Comando de produção (gunicorn)
├─ requirements.txt
├─ .env.example              Variáveis necessárias — copie para .env
│
├─ app/
│  ├─ __init__.py            Factory, config, blueprints, filtro de moeda
│  ├─ models.py              OrcamentoMensal, Transacao, FonteReceita, Categoria
│  ├─ routes/                Um blueprint por domínio
│  │  ├─ dashboard.py        Cálculos do mês e navegação entre meses
│  │  ├─ transacoes.py       Lançamento de gastos, incluindo o modo rápido
│  │  ├─ receitas.py         Fontes de receita do mês
│  │  ├─ cartao.py           Visão consolidada de cartão de crédito
│  │  ├─ orcamento.py        Configuração do mês
│  │  └─ categorias.py       Cadastro de categorias
│  ├─ templates/             Jinja2, com base compartilhada
│  └─ static/                CSS e JS próprios
│
└─ scripts/                  Utilitários avulsos de manutenção
```

### Modelo de dados

```
OrcamentoMensal  (mes, ano, receita_prevista, percentual_poupanca)
    ├── FonteReceita   salário, freelance, outros
    └── Transacao      cada gasto do mês
                            │
Categoria  ────────────────┘   Aluguel, Mercado, Transporte…
```

`cascade="all, delete-orphan"` nos relacionamentos: apagar um mês apaga as
transações e receitas dele, sem deixar registro órfão apontando para um pai que
não existe mais.

---

## Como rodar

Requer Python 3.10 ou superior.

```powershell
git clone https://github.com/BrenoZG/gestao-financas.git
cd gestao-financas

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

Copy-Item .env.example .env
# gere uma SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"

python run.py
```

Abre em `http://localhost:5000`. O banco SQLite e as categorias padrão são
criados na primeira execução.

O servidor sobe em `0.0.0.0`, então o app também abre no celular pela mesma rede
Wi-Fi — útil, porque lançar um gasto é algo que se faz na rua, não no
computador.

---

## Deploy

O `Procfile` usa gunicorn. Em qualquer host que injete `DATABASE_URL`
(Railway, Render, Heroku), o app usa o banco fornecido automaticamente.

**Defina o comando de instalação como `pip install -r requirements-prod.txt`.**

São dois arquivos de dependência, e a separação é deliberada:

| Arquivo | Contém | Para quê |
|---|---|---|
| `requirements.txt` | flask, flask-sqlalchemy, python-dotenv, gunicorn | Rodar local, em SQLite |
| `requirements-prod.txt` | os acima + `psycopg[binary]` | Deploy com Postgres |

O driver de Postgres é a dependência mais frágil do projeto: precisa de wheel
compilado para a versão exata do Python, e interpretadores recém-lançados ficam
meses sem wheel publicado. Mantê-lo fora do arquivo principal significa que uma
limitação de empacotamento de terceiro não bloqueia quem só quer clonar e rodar.

| Variável | Obrigatória | Função |
|---|---|---|
| `SECRET_KEY` | Sim, em produção | Assinatura de sessão do Flask |
| `DATABASE_URL` | Não | Sem ela, cai em SQLite local |
| `FLASK_DEBUG` | Não | `1` liga o modo debug — **nunca em produção** |

> **SQLite em produção não serve.** Hospedagem com disco efêmero recria o
> sistema de arquivos a cada deploy, e o banco inteiro some — sem erro no log.
> Defina `DATABASE_URL` apontando para um Postgres gerenciado.

---

## Limitações conhecidas

Registradas porque limitação escrita é decisão; limitação omitida é surpresa.

1. **Sem autenticação.** A aplicação assume um único usuário. Publicar na
   internet aberta significa expor os dados a qualquer visitante. Uso previsto é
   local ou atrás de rede privada.

2. **Sem migrações de banco.** `db.create_all()` cria tabelas que não existem,
   mas não altera as existentes. Mudança de coluna exige recriar o banco ou
   aplicar o ALTER na mão. Alembic é o próximo passo quando o modelo estabilizar.

3. **Sem testes automatizados.** Os cálculos financeiros são propriedades puras
   e fáceis de testar — é a lacuna mais barata de fechar e a de maior retorno.

4. **Cartão de crédito é uma flag, não uma entidade.** `eh_cartao_credito` na
   categoria resolve a visão consolidada, mas não modela fatura, ciclo de
   fechamento nem parcelamento.
