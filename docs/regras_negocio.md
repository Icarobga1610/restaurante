# Regras de Negócio

## 1. Clientes
- Cliente pode ser Pessoa Física ou Jurídica
- Cliente pode ter limite mensal opcional
- Cliente inativo não pode fazer pedidos
- Cliente pode ter observações

## 2. Produtos
- Produtos podem ter sazonalidade (época, dias específicos, promoção)
- Produto inativo não aparece nos lançamentos
- Custo estimado é opcional

## 3. Pedidos
- Pedido só pode ser lançado para cliente ativo
- Pedido confirmado pode ser cancelado
- Pedido faturado não pode mais ser alterado
- Total do pedido é calculado automaticamente

## 4. Conta Mensal
- Cada cliente pode ter uma conta por mês
- A conta inclui todos pedidos confirmados do período
- Fluxo: Aberta → Fechada → Assinada → Paga
- Conta vencida: fechada de mês anterior não paga

## 5. Assinatura
- Assinatura eletrônica simples (não ICP-Brasil)
- Deve ser desenhada em canvas HTML
- Vinculada ao fechamento mensal
- Gera hash de verificação para auditoria

## 6. Perfis
- **Admin**: Acesso total
- **Atendente**: Apenas lançar pedidos e consultar
- **Financeiro**: Fechar conta, assinar, pagar

## 7. Insights (Regras Analíticas)
- Produtos mais vendidos por dia da semana
- Horários de pico
- Comparativo mês atual vs anterior
- Alertas de limite próximo do cliente
- Queda ou aumento de demanda de produtos
- Contas vencidas ou sem assinatura
