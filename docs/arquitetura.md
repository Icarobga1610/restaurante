# Arquitetura do Sistema

## Visão Geral

Sistema web para restaurante com foco em conta mensal para clientes. Arquitetura baseada em REST API com frontend SPA React.

## Componentes

### Backend (FastAPI)
- **API REST** documentada automaticamente via OpenAPI/Swagger
- **ORM**: SQLAlchemy com suporte a SQLite e PostgreSQL
- **Autenticação**: JWT simplificado com hash SHA256
- **Logs**: Estruturados em JSON

### Frontend (React + Vite)
- **Vite** como bundler
- **Tailwind CSS** para estilização responsiva
- **Recharts** para gráficos
- **React Router** para navegação SPA
- **Context API** para estado de autenticação

### Banco de Dados
- SQLite para desenvolvimento
- Preparado para PostgreSQL em produção (trocar DATABASE_URL)

## Fluxo de Dados

```
[Browser] --> React SPA --> REST API (FastAPI) --> SQLAlchemy ORM --> SQLite/PostgreSQL
```

## Principais Fluxos

### Cadastro e Pedidos
1. Admin cadastra clientes e produtos
2. Atendente lança pedidos para clientes
3. Pedidos ficam como "confirmados"

### Fechamento Mensal
1. Usuário financeiro seleciona cliente e mês
2. Sistema busca todos pedidos do período
3. Calcula total e fecha a conta (status: closed)
4. Cliente assina digitalmente (status: signed)
5. Financeiro registra pagamento (status: paid)

### Geração de Insights
1. Sistema analisa dados de pedidos, clientes e produtos
2. Calcula métricas de sazonalidade
3. Gera insights com regras Python simples
4. Exibe no dashboard e relatórios

## Segurança

- Senhas armazenadas com hash SHA256 + salt
- Tokens JWT com expiração
- Controle de acesso por perfil (RBAC)
- Logs de auditoria para ações críticas
