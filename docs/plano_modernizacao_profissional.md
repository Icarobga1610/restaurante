# Plano de Modernização Profissional — Restaurante Conta Mensal

## Princípio
Aplicar mudanças incrementais, verificadas e de baixo risco primeiro; manter o domínio do restaurante intacto; priorizar profissionalismo sem rompimentos contratuais ou operacionais.

## FASE 1 — Segurança e robustez
### STATUS: concluída

**Entrega:**
- `app/auth/auth.py` refatorado com `python-jose` + `passlib`/`bcrypt`.
- Migração transparente: logins antigos continuam funcionando via hash legado, novos hashes usam bcrypt.
- JWT com payload padrão `sub`, `username`, `role_id`, `exp`.
- `bcrypt==4.0.1` fixado.
- `utcnow` timezone-aware.

**Verificado:**
- pytest: 43 passed, 6 skipped

## FASE 2 — Portabilidade e dados
### STATUS: em andamento (independente do Oraculo)
- Alembic inicializado; migração `init restaurante schema` gerada.
- Banco Postgres dedicado: `restaurante`.
- Testes configuráveis para Postgres via `USE_POSTGRES_TESTS=true`.
- `python-json-logger` adicionado.

## FASE 3 — Frontend / experiência
- Checklist profissional, estados loading/empty.
- Proteção de rotas.
- Fallback de idioma/env.

## Decisões
- Python backend.
- PostgreSQL dedicado para produção.
- Projeto totalmente independente; sem reaproveitamento do Oraculo.