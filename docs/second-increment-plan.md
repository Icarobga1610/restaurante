# Plano do Segundo Incremento — Sistema de Gestão para Restaurantes
**Contexto:** modernização para produção com stack atual: FastAPI 2.0.23, SQLAlchemy 2.0, Pydantic v2, React 18, Vite 5, Tailwind CSS v3, PostgreSQL, JWT + bcrypt.  
**Referência de pesquisa:** 2026 best practices para POS/restaurantes, PostgreSQL, autenticação/autorização, FastAPI, React, payments, testing e CI/CD.

---

## 1. Visão geral do incremento
Objetivo transformar o projeto atual em um sistema **produção-ready**, escalável, seguro e observável, mantendo viabilidade de operação no Brasil.

Entregas principais:
- Persistência performática e resiliente
- Auth hardening e RBAC refinada
- Backends mais rápidos e confiáveis
- Frontend com UX/admin mais fluida
- Integração de pagamentos robusta
- Cobertura de testes profissional
- Deploy automatizado e reversível

---

## 2. Prioridades e ordem sugerida
| Ordem | Tema | Motivo |
|---|---|---|
| 1 | Observabilidade + Proteção | Segurança e operação vêm primeiro |
| 2 | PostgreSQL + Performance | Base para escala |
| 3 | Auth evoluída | Controle de acesso mais fino |
| 4 | Pagamentos | Receita e confiabilidade |
| 5 | Frontend performance | Produtividade operacional |
| 6 | Testes | Reduzir regressão |
| 7 | CI/CD + Deploy | Entregar com qualidade e velocidade |

---

## 3. PostgreSQL: performance, resiliência e escala

### 3.1 Indexação e schema
- Criar índices por padrões de acesso reais, não por “adivinhação”.
- Usar `EXAIN ANALYZE` para decisões.
- Foco: `orders`, `order_items`, `payments`, `inventory_movements`, `users`.
- Tipos recomendados: B-tree para filtros comuns; GIST/GIN para busca textual/JSONB quando houver filtros profundos.

Regra prática:
- Em tabelas transacionais grandes, evitar `SELECT *`.
- Prefixos/texto longo → criarem índices parciais/expressivos quando o filtro for sempre em estado ou período.

### 3.2 Connection pooling
- Usar PgBouncer em modo transaction pooling para reduzir custo de conexão.
- Configurar SQLAlchemy com pool menor e overflow controlado.
- Em deploy com réplicas, criar engines separados para read/write quando fizer sentido.

### 3.3 Réplicas de leitura
- Mover relatórios, dashboards e analytics para réplica read-only.
- Evitar consistência eventual em fluxos críticos de caixa/pedido.
- Alternativas mais simples primeiro: aplicar cache em nível de query antes de réplicas.

### 3.4 Manutenção
- Autovacuum ajustado ao perfil transacional (restaurante tem picos).
- Particionamento por data em tabelas que crescem rápido: `orders`, `payments`, `inventory_movements`.
- Backup automatizado com PITR (Point-in-Time Recovery) em produção.

Bibliotecas/comandos relevantes:
- `pgbouncer`
- `sqlalchemy` pool config + `NullPool` local conforme ambiente
- `pg_stat_statements` para detectar queries custosas
- `pg_partman` para particionamento quando necessário

---

## 4. Autenticação, autorização e sessão

### 4.1 Padrões recomendados
- Manter JWT mas endurecer validações: issuer, audience, algoritmo fixo, expiração curta para access token.
- Refresh token com rotação e detecção de reuso (revogação por familia).
- Sessão-like: considerar session server-side em Redis para casos admin sensíveis e para revogação imediata.

### 4.2 RBAC com granularidade útil para restaurante
- Implementar papéis alinhados à operação real: `admin`, `manager`, `cashier`, `kitchen`, `waiter`, `accountant`.
- Camadas de checagem:
  1) middleware/dependency de autenticação
  2) checagem de permissão por ação
  3) checagem por recurso específico quando necessário

### 4.3 Segurança
- Cookies de sessão com `HttpOnly`, `Secure` em produção e `SameSite=Lax`.
- Bloqueio progressivo após falhas de login.
- Headers: CORS restrito, `Content-Security-Policy` no front quando aplicável.

Bibliotecas:
- `python-jose[cryptography]` ou `pyjwt` + `passlib[bcrypt]`
- `redis` para sessão/refresh/blacklist/limite por IP
- `slowapi` como rate limiter com Redis storage

---

## 5. FastAPI: produção, desempenho e resiliência

### 5.1 Performance
- Rodar com múltiplos workers em produção.
- Usar `uvicorn` com workers > 1 em runtime containerizado.
- Avaliar `uvloop` e `httptools` no container Linux.
- Resposta padrão `ORJSONResponse` para payloads grandes.
- Manter async verdadeiro no I/O; sync apenas para CPU-heavy isolado.

### 5.2 Middleware
- Middlewares leves e compostos: logging estruturado, request id, medição de latência, CORS restrito, rate limit global/local.
- Evitar middleware gigante; preferir composição por endpoint/dependência.

### 5.3 Cache e tarefas de fundo
- Cachear consultas caras ou leituras repetidas: catálogo, cardápio, relatórios lentos.
- Tarefas não bloqueantes ao usuário: emissão/validação de recibos, atualização de cache, notificações.
- Para tarefas com garantia ou retry: fila com workers/consumidores dedicados.

Bibliotecas:
- `slowapi[redis]`
- `orjson`
- `prometheus-fastapi-instrumentator`
- `aioredis` ou `redis.asyncio`
- `python-json-logger` ou `structlog`

---

## 6. Frontend: performance e experiência administrativa

### 6.1 Code splitting e lazy loading
- Dividir por rotas e por módulos pesados: relatórios, PDV, gráficos, KDS.
- Usar `React.lazy` + `Suspense` em pontos de entrada pesados.
- Adiar bibliotecas pesadas para carregamento dinâmico.

### 6.2 Estado e re-renderizações
- Local state primeiro; global state para dados compartilhados e estáveis.
- Aplicar `React.memo`, `useCallback` e `useMemo` de forma guiada por medição.
- Evitar contextos muito amplos; criar slices por domínio.
- Para formulários grandes: biblioteca de formulários com validaçãoperformática.

Bibliotecas recomendadas:
- `react-router` com route-based code splitting
- `zustand` ou `@reduxjs/toolkit` para estado global leve
- `react-query` ou `tanstack-query` para cache/request state
- `@tanstack/react-table` para tabelas pesadas
- `react-virtuoso` ou `react-window` para listas longas

---

## 7. Pagamentos: fluxo, conformidade e integração

### 7.1 Padrões de integração
- Abstrair gateway de pagamento para trocar provedor sem alterar domínio.
- Fluxo preferido: authorização + captura para evitar chargebacks e permitir ajuste de pedido.
- Registrar estado do pagamento com idempotência e transações atômicas no banco.

### 7.2 RESTAURANTE vs ONLINE
- Para presencial: integrar terminal/PDV via provedor quando disponível; senão manter QR/PIX e cartão tokenizado.
- Para iFood/rappis: webhooks para status e reconciliar em lotes/agendamento.
- Regras fiscais: emitir nota/cancelamento com estado consistente no pagamento.

Bibliotecas/serviços:
- `stripe` ou adquirente brasileiro via SDK/HTTP oficial
- PIX com validação de webhook assinado
- Idempotency keys em todo fluxo de pagamento

---

## 8. Testes: estratégia moderna para fullstack

### 8.1 Pirâmide ajustada
- Mais testes unitários serviços, schemas, auth, regras de negócio.
- Testes de integração cobrando endpoints e banco.
- Testes E2E para jornadas críticas: login, PDV, pagamento, relatório, cancelamento.

### 8.2 Ferramentas
- Backend: `pytest` + `httpx.AsyncClient` + factories de fixture (`pytest-factoryboy`, `faker`).
- Frontend: `vitest` para unit + integração; `playwright` para E2E quando necessário.
- Cobertura de qualidade, não número por número: foco em regras financeiras e operacionais.

Bibliotecas:
- `pytest`, `pytest-asyncio`, `pytest-cov`
- `testcontainers` ou banco dedicado de teste
- `vitest`, `@playwright/test`

---

## 9. CI/CD e deploy

### 9.1 Pipelines
- CI em PR: lint, testes unitários/integração, build do frontend.
- CD automatizado em merge para main: build e push de imagens, deploy com rollout/rollback.
- Imutabilidade: images por digest/tag semântica.

### 9.2 Infra e operação
- Containerizar backend e frontend separadamente.
- Usar Nginx/Caddy como proxy/reverse para app ou servir dist do Vite.
- Segredos em vault/CI secrets; nunca no repositório.
- Healthchecks/readiness/liveness no backend.
- Banco provisionado via IaC, com migrações automatizadas e bloqueio em caso de falha.

Ferramenas:
- `docker`, `docker-compose`
- GitHub Actions ou GitLab CI
- Terraform ou Pulumi quando houver provisionamento cloud
- `Sentry`/`OpenTelemetry` para observabilidade

---

## 10. Sugestão de pacote/setup incremental

### Backend
```bash
pip install slowapi redis orjson prometheus-fastapi-instrumentator python-json-logger
```

### Frontend
```bash
npm install zustand @tanstack/react-query react-router-dom react-virtuoso
npm install -D vitest @playwright/test
```

### Infra/observabilidade
- `docker-compose` com: api, web, nginx/caddy, postgres, redis, pgbouncer opcional.
- Coletar logs estruturados em JSON e métricas em formato Prometheus.

---

## 11. Sequência de implementação detalhada

1. **Auth & segurança**
   - migrar refresh token com rotação e blacklist
   - configurar CORS, request id, logging básico
   - criar RBAC com dependências por papel/module

2. **Backend hardening**
   - adicionar ORJSONResponse, workers e rate limit com SlowAPI
   - adicionar cache Redis para consultas quentes
   - implementar background tasks para jobs leves

3. **Banco e dados**
   - revisar e criar índices em fluxos críticos
   - configurar pool e parâmetros de conexão
   - padronizar consultas evitando N+1

4. **Payments**
   - criar camada de abstração/gateway
   - implementar webhook seguro e reconciliação
   - garantir idempotência e status atômico por pedido/pagamento

5. **Frontend performance**
   - adotar code splitting por rotas
   - migrar estado global para solução mais leve
   - aplicar memoização guiada em listas/admin

6. **Testes**
   - constituir suite de backend com pytest
   - criar testes E2E para jornadas críticas
   - integrar cobertura no pipeline

7. **CI/CD + deploy**
   - dockerizar backend e frontend
   - automatizar deploy com healthcheck
   - configurar monitoramento e alertas básicos

---

## 12. Notas para contexto brasileiro
- PIX deve ser cidadão de primeiro nível no fluxo de pagamento.
- NFC-e/NF-e/sat: estado fiscal deve refletir status de pagamento e cancelamento.
- Integração com iFood/Rappi deve reconciliar webhook em job seguro, não no request principal.
- Para pequenos locais, o desempenho offline/local pode valer um estudo de sincronização futura, mas não obrigatório no segundo incremento.

---

## 13. Critérios de conclusão do incremento
- Backend deployável com 3 comandos em staging.
- Auth com RBAC funcionando e token renovação segura.
- Endpoints de pedido/pagamento com middleware de segurança e rate limit.
- Dashboard admin carregando rotas grandes sob demanda.
- Testes automatizados bloqueando merge para main.
- Pipeline CI/CD com checklist rápido e deploy reversível.
