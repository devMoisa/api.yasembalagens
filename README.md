# Yas Embalagens API

Backend do catalogo da Yas Embalagens. A vitrine exibe banners, categorias e blocos
ordenados de produtos. O visitante monta uma lista e a API gera a mensagem e o link do
WhatsApp; nao existe pagamento ou checkout no backend.

## Stack

- Python 3.12 e `uv`
- FastAPI + Pydantic
- SQLAlchemy 2 (o ORM que voce lembrou como “Alchemy”)
- SQLite no desenvolvimento
- Alembic para migracoes
- JWT e Argon2 para a area administrativa

## Primeiros passos

```bash
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run yas-seed
uv run yas-create-admin
uv run fastapi dev src/yas_api/main.py
```

A API fica em `http://127.0.0.1:8000`, e a documentacao interativa em
`http://127.0.0.1:8000/docs`. No login OAuth2 da documentacao, use o e-mail do admin no
campo `username`.

## Fluxo administrativo sugerido

1. Autenticar em `POST /api/v1/admin/auth/token`.
2. Enviar imagens em `POST /api/v1/admin/media`.
3. Criar categorias e produtos usando os IDs das imagens.
4. Criar blocos como “Mais vendidos” e “Linhas especiais”, passando `product_ids` na
   ordem desejada.
5. Criar banners para `hero`, `middle` ou `footer`.
6. Configurar telefone e modelo da mensagem em `PATCH /api/v1/admin/settings`.

`GET /api/v1/public/storefront` entrega toda a composicao inicial da home em uma unica
resposta. `POST /api/v1/public/quote` valida quantidades minimas e devolve a URL
`wa.me` pronta para o frontend abrir.

`uv run yas-seed` importa de forma idempotente o conteúdo aprovado da vitrine: 13
categorias, 28 produtos sem duplicações, 5 blocos ordenados e o banner hero atual.

## Organizacao

```text
src/yas_api/
├── api/          # rotas publicas, admin e dependencias HTTP
├── core/         # configuracao e seguranca
├── db/           # engine, sessao e base SQLAlchemy
├── models/       # tabelas do dominio
├── schemas/      # contratos de entrada e saida
├── services/     # regras sem dependencia de HTTP
├── cli.py        # criacao segura do primeiro admin
└── main.py       # fabrica da aplicacao
migrations/       # historico versionado do banco
tests/            # testes de integracao da API
uploads/          # arquivos locais (nao versionados)
```

## Comandos

```bash
make dev                         # servidor com reload
make migrate                     # aplica migracoes
make revision m="novo campo"     # cria uma migracao
make admin                       # cria outro administrador
make format                      # formata o codigo
make check                       # lint + testes
```

O armazenamento local de imagens e o SQLite sao adequados para iniciar. Quando houver
mais de uma instancia da API, troque `YAS_DATABASE_URL` por PostgreSQL e o upload local
por um storage como S3/R2; os IDs e contratos da API podem permanecer os mesmos.
# api.yasembalagens
