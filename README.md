# 🍽️ Restaurante Conta Mensal

Sistema web completo para gestão de restaurante/lanchonete com controle de **conta mensal para clientes** que pagam apenas no fechamento do mês.

## Funcionalidades

- **Clientes**: Cadastro com CPF, telefone, empresa, limite mensal
- **Produtos**: Cardápio com categorias, preços, sazonalidade
- **Pedidos**: Lançamento rápido vinculado ao cliente
- **Conta Mensal**: Acompanhamento, fechamento, assinatura digital, pagamento
- **Assinatura Digital**: Assinatura eletrônica simples desenhada na tela (mouse/touch/caneta)
- **Dashboard**: Indicadores, gráficos, faturamento
- **Insights Inteligentes**: Análise de sazonalidade, tendências, alertas
- **Auditoria**: Logs completos de todas as ações
- **Perfis**: Administrador, Atendente, Financeiro
- **Responsivo**: Desktop, tablet e celular

## Stack

- **Backend**: Python FastAPI + SQLAlchemy
- **Frontend**: React + Vite + Tailwind CSS + Recharts
- **Banco**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Autenticação**: JWT simplificado (hash SHA256)

## Estrutura

```
restaurante/
├── backend/
│   ├── app/
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── routes/       # API endpoints
│   │   ├── services/     # Business logic (audit, insights)
│   │   ├── auth/         # Authentication
│   │   ├── logs/         # Log directory
│   │   ├── tests/        # Automated tests
│   │   ├── main.py       # FastAPI app
│   │   └── database.py   # Database setup
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/   # Layout, shared components
│   │   ├── pages/        # All application pages
│   │   ├── services/     # API client
│   │   ├── hooks/        # Auth context
│   │   └── utils/        # Helpers
│   └── package.json
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

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
cp .env.example .env

# Opcional: popular dados fake
cd ..
python scripts/seed_db.py

# Iniciar servidor
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:5173

## Usuários Padrão

| Usuário | Senha | Perfil |
|---------|-------|--------|
| admin | admin123 | Administrador |
| atendente | atendente123 | Atendente |
| financeiro | financeiro123 | Financeiro |

## API

Documentação interativa: http://localhost:8000/docs

### Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /api/auth/login | Login |
| GET/POST | /api/clients | Listar/Criar cliente |
| GET/POST | /api/products | Listar/Criar produto |
| GET/POST | /api/orders | Listar/Criar pedido |
| GET/POST | /api/monthly-accounts | Listar/Criar conta mensal |
| POST | /api/monthly-accounts/{id}/close | Fechar conta |
| POST | /api/monthly-accounts/{id}/sign | Assinar conta |
| POST | /api/monthly-accounts/{id}/pay | Pagar conta |
| GET | /api/dashboard | Dashboard |
| GET | /api/insights/active | Insights ativos |
| GET | /api/audit | Logs de auditoria |

## Assinatura Digital

⚠️ **Importante**: A assinatura digital deste sistema é uma **assinatura eletrônica simples** para confirmação de consumo mensal. **Não é uma assinatura digital certificada ICP-Brasil**. A assinatura é capturada via canvas HTML, salva como imagem base64/PNG e vinculada ao fechamento mensal com hash de verificação.

## Licença

Projeto de código aberto para fins educacionais e comerciais.
