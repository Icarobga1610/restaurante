# 🍽️ Restaurante Conta Mensal

Sistema web completo para gestão de restaurante/lanchonete com controle de **conta mensal para clientes** que pagam apenas no fechamento do mês.

## Funcionalidades

- **Clientes**: Cadastro com CPF/CNPJ, telefone, empresa, limite mensal
- **Produtos**: Cardápio com categorias, preços, sazonalidade
- **Pedidos**: Lançamento rápido vinculado ao cliente
- **Conta Mensal**: Acompanhamento, fechamento, assinatura digital, pagamento
- **Assinatura Digital**: Assinatura eletrônica simples desenhada na tela (mouse/touch/caneta)
- **Dashboard**: Indicadores, gráficos, faturamento
- **Insights Inteligentes**: Análise de sazonalidade, tendências, alertas
- **Auditoria**: Logs completos de todas as ações
- **Biometria**: WebAuthn/Passkey para verificação de identidade
- **Perfis**: Administrador, Atendente, Financeiro
- **Responsivo**: Desktop, tablet e celular

## Stack

- **Backend**: Python FastAPI + SQLAlchemy + Pydantic v2
- **Frontend**: React + Vite + Tailwind CSS + Recharts
- **Banco**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Autenticação**: JWT com refresh token
- **Validação**: CPF, CNPJ, telefone, email

## Estrutura

```
restaurante/
├── backend/
│   ├── app/
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── routes/       # API endpoints
│   │   ├── services/     # Business logic (audit, insights, cache, sentry)
│   │   ├── auth/         # Authentication
│   │   ├── utils/        # Validators, helpers
│   │   ├── tests/        # Automated tests
│   │   ├── main.py       # FastAPI app
│   │   ├── config.py     # Pydantic Settings
│   │   └── database.py   # Database setup
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/   # Layout, shared components
│   │   ├── pages/        # All application pages
│   │   ├── services/     # API client
│   │   ├── hooks/        # Auth context
│   │   └── utils/        # Helpers
│   └── vite.config.js
├── scripts/
│   ├── seed_db.py        # Database seeder
│   └── backup_db.py      # Backup script
├── docs/
│   ├── arquitetura.md
│   ├── regras_negocio.md
│   └── roadmap.md
└── README.md
```

## Instalação

### Pré-requisitos

- Python 3.10+
- Node.js 18+
- npm ou yarn
- Redis (opcional - para cache)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
cp .env.example .env

# Editar .env com suas configurações
# - SECRET_KEY: uma chave aleatória segura
# - DATABASE_URL: URL do banco de dados

# Opcional: popular dados fake
cd ..
python scripts/seed_db.py

# Iniciar servidor
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8030
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:5173

## Banco de Dados

O projeto usa **SQLite** por padrão (arquivo `backend/restaurante.db`, sem instalação).
Para usar **PostgreSQL**, um cluster dedicado deste projeto já está configurado
na porta **5433** (cluster `16/restaurante`).

### Usando PostgreSQL (porta 5433)

1. O cluster já existe e está online. Para recriar/restaurar manualmente:

```bash
# Criar e iniciar o cluster na porta 5433 (Debian/Ubuntu)
pg_createcluster 16 restaurante --port 5433
pg_ctlcluster 16 restaurante start

# Criar role e banco
sudo -u postgres psql -p 5433 -c "CREATE ROLE restaurante WITH LOGIN PASSWORD 'restaurante' CREATEDB;"
sudo -u postgres psql -p 5433 -c "CREATE DATABASE restaurante OWNER restaurante;"
```

2. No `backend/.env`, aponte para Postgres:

```env
DATABASE_URL=postgresql+psycopg://restaurante:restaurante@localhost:5433/restaurante
```

3. O driver `psycopg[binary]` já está em `requirements.txt`. Suba o backend
normalmente — as tabelas e os dados iniciais (roles, usuários, formas de
pagamento) são criados automaticamente no primeiro startup.

> Nota: o código é compatível com SQLite e PostgreSQL. O dashboard usa
> `to_char` no Postgres e `strftime` no SQLite automaticamente. Os testes
> automatizados usam SQLite por padrão; para rodá-los em Postgres defina
> `USE_POSTGRES_TESTS=true` e `TEST_DATABASE_URL` apontando para um banco
> de teste dedicado (ex.: `restaurante_test`).

## Usuários Padrão

| Usuário | Senha | Perfil |
|---------|-------|--------|
| admin | admin123 | Administrador |
| atendente | atendente123 | Atendente |
| financeiro | financeiro123 | Financeiro |

## API

Documentação interativa: http://localhost:8030/docs

### Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /api/auth/login | Login |
| POST | /api/auth/refresh | Refresh token |
| GET/POST | /api/clients | Listar/Criar cliente |
| GET/PUT/DELETE | /api/clients/{id} | Gerenciar cliente |
| GET/POST | /api/products | Listar/Criar produto |
| GET/PUT/DELETE | /api/products/{id} | Gerenciar produto |
| GET/POST | /api/orders | Listar/Criar pedido |
| GET/PUT | /api/orders/{id} | Gerenciar pedido |
| GET/POST | /api/monthly-accounts | Listar/Criar conta mensal |
| POST | /api/monthly-accounts/{id}/close | Fechar conta |
| POST | /api/monthly-accounts/{id}/biometric-verify | Confirmar conta por biometria (digital) |
| POST | /api/monthly-accounts/{id}/pay | Pagar conta (registra assinatura digital) |
| POST | /api/biometrics/webauthn/enroll/options | Opções de enrollment WebAuthn |
| POST | /api/biometrics/webauthn/enroll/complete | Completar enrollment WebAuthn |
| POST | /api/biometrics/webauthn/verify/options | Opções de verificação WebAuthn |
| POST | /api/biometrics/webauthn/verify/complete | Completar verificação WebAuthn |
| GET | /api/dashboard | Dashboard |
| GET | /api/insights/active | Insights ativos |
| GET | /api/audit | Logs de auditoria |

## Validações

O sistema inclui validações robustas para:

- **CPF**: Validação de dígitos verificadores
- **CNPJ**: Validação de dígitos verificadores
- **Telefone**: Validação de DDD e formato
- **Email**: Validação de formato básico

## Configuração

### Variáveis de Ambiente

```env
# Database — SQLite (desenvolvimento padrão, zero configuração)
DATABASE_URL=sqlite:///./restaurante.db

# Database — PostgreSQL (produção / dev com Postgres)
# Cluster dedicado deste projeto roda na porta 5433.
# Crie o banco antes de usar (veja "Banco de Dados" abaixo).
# DATABASE_URL=postgresql+psycopg://restaurante:restaurante@localhost:5433/restaurante

# Auth
SECRET_KEY=sua-chave-secreta-aqui
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Refresh token (revogável, armazenado no Redis)
# TTL em segundos (padrão 7 dias). Expira sozinho; logout o revoga antes.
REFRESH_TOKEN_TTL_SECONDS=604800

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:8002

# Redis — NECESSÁRIO para refresh tokens revogáveis (logout/revogação global).
# Sem Redis o backend sobe em modo degradado (refresh não revogável, em memória).
REDIS_URL=redis://localhost:6379/0

# Sentry (opcional)
SENTRY_DSN=https://sua-dsn@sentry.io/projeto

# Server
HOST=0.0.0.0
PORT=8030
DEBUG=false
```

## Testes

```bash
cd backend
source venv/bin/activate
python -m pytest app/tests/ -v
```

## Assinatura Digital

⚠️ **Importante**: A assinatura digital deste sistema é uma **assinatura eletrônica simples** para confirmação de consumo mensal. **Não é uma assinatura digital certificada ICP-Brasil**. A assinatura é capturada via canvas HTML, salva como imagem base64/PNG e vinculada ao fechamento mensal com hash de verificação.

## Segurança

- **Access token (JWT) de curta duração** — assinado com `SECRET_KEY`, `exp` + `iat` + `jti` único. Stateless.
- **Refresh token revogável (server-side, Redis)**:
  - Emitido no login junto com o access token; é um valor opaco (JTI) armazenado no Redis com TTL (`REFRESH_TOKEN_TTL_SECONDS`, padrão 7 dias).
  - `POST /api/auth/refresh` troca um refresh válido por um novo par access+refresh (**rotação**: o token usado é revogado na mesma chamada).
  - `POST /api/auth/logout` revoga o refresh token no servidor (via índice reverso `jti -> user_id`), mesmo se o access token já tiver expirado. Se o usuário autenticado também é informado, revoga **todas** as sessões (`revoke_all`).
  - Sem Redis o backend sobe em modo degradado (refresh em memória, não sobrevive a restart e não revogável) — suficiente para dev/local, mas produção exige Redis.
  - O frontend (`useAuth` + interceptor do `api.js`) faz refresh transparente: num 401 ele renova o access token e refaz a requisição original, sem logar o usuário para fora.
- CORS configurado para origens específicas
- Headers de segurança (X-Frame-Options, X-Content-Type-Options, etc.)
- Rate limiting em endpoints de autenticação
- Auditoria completa de ações
- **Mass-assignment protection**: schemas de entrada (`ClientCreate`, `ProductCreate`, `OrderCreate`, etc.) usam `ConfigDict(extra="forbid")`, rejeitando campos não declarados
- **Docs ocultos em produção**: `/docs` e `/openapi.json` ficam desabilitados quando `DEBUG=false`
- **Limite de crédito**: ao fechar uma conta mensal, o total é comparado com `client.monthly_limit`; se excedido, a conta é marcada `over_limit=true` e o evento é registrado na auditoria

## CI / Supply-chain Security

- GitHub Actions (`.github/workflows/ci.yml`) roda em `push`/`PR` para `main` e `develop`:
  - **Backend**: instala dependências, roda `pytest` (SQLite) e **`pip-audit`** (scanner de vulnerabilidades CVE em pacotes Python).
  - **Frontend**: `npm ci` + `npm run build`.
  - **Trivy**: varredura de vulnerabilidades no filesystem (`trivy fs`) reportando CRITICAL/HIGH.
- `pip-audit` e `trivy` são configurados como *report-only* (`|| true` / `exit-code: 0`) para não quebrar o build em CVEs recém-divulgados, mas sempre sinalizam o time.
- Dependências foram atualizadas para versões sem CVEs conhecidos (fastapi 0.115.6, starlette 0.41.3, cryptography 44, python-multipart 0.0.30, etc.). `aiocache` foi removido (não utilizado e com build quebrado).

## Validações de Domínio

- **Limite de crédito (conta mensal)**: pedidos de clientes `is_account_client` consomem o limite mensal; o fechamento sinaliza estouro de limite (`over_limit`)

## Licença

Projeto de código aberto para fins educacionais e comerciais.