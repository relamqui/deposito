# TOOLS DO N8N — Copiar e Colar no Execute Query

Cada seção abaixo é **uma tool**. No n8n:
1. Crie um node **PostgreSQL** → Operation: **Execute Query**
2. Cole a query no campo **Query**
3. Conecte como **Tool** do AI Agent
4. Preencha o **Name** e **Description** exatamente como abaixo

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TOOL 1 — buscar_cliente
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Name:** `buscar_cliente`

**Description:**
```
Busca um cliente pelo número de telefone no banco de dados. Use sempre que precisar verificar se o cliente já está cadastrado. O parâmetro telefone deve ser apenas números, exemplo: 5511999999999
```

**Query (cole no Execute Query):**
```sql
SELECT id, telefone, nome
FROM "CLIENTES"
WHERE telefone = '{{ $fromAI("telefone") }}';
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TOOL 2 — criar_cliente
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Name:** `criar_cliente`

**Description:**
```
Cadastra um novo cliente ou atualiza o nome se já existir. Parâmetros: telefone (apenas números, ex: 5511999999999) e nome (nome completo do cliente).
```

**Query (cole no Execute Query):**
```sql
INSERT INTO "CLIENTES" (telefone, nome)
VALUES ('{{ $fromAI("telefone") }}', '{{ $fromAI("nome") }}')
ON CONFLICT (telefone)
DO UPDATE SET nome = EXCLUDED.nome, atualizado_em = now()
RETURNING id, telefone, nome;
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TOOL 3 — buscar_produto
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Name:** `buscar_produto`

**Description:**
```
Busca produtos no estoque pelo nome ou descrição. Funciona mesmo com erros de digitação. Retorna os 5 produtos mais parecidos com nome, preço, estoque e unidade. Parâmetro: query (texto que o cliente digitou, exemplo: brarama 600).
```

**Query (cole no Execute Query):**
```sql
SELECT
    id,
    nome,
    descricao,
    preco_venda,
    estoque,
    unidade,
    GREATEST(similarity(nome, '{{ $fromAI("query") }}'), similarity(descricao, '{{ $fromAI("query") }}')) AS score
FROM "DEPOSITO_JOEL"
WHERE ativo = true
  AND (
    similarity(nome, '{{ $fromAI("query") }}') > 0.08
    OR similarity(descricao, '{{ $fromAI("query") }}') > 0.08
    OR nome ILIKE '%' || '{{ $fromAI("query") }}' || '%'
    OR descricao ILIKE '%' || '{{ $fromAI("query") }}' || '%'
  )
ORDER BY score DESC
LIMIT 5;
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TOOL 4 — criar_carrinho
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Name:** `criar_carrinho`

**Description:**
```
Cria um novo carrinho de compras vazio para o cliente. Use o cliente_id retornado pela tool buscar_cliente ou criar_cliente. NUNCA invente um cliente_id. Parâmetro: cliente_id (número inteiro retornado por buscar_cliente ou criar_cliente).
```

**Query (cole no Execute Query):**
```sql
INSERT INTO "CARRINHOS" (cliente_id, status)
VALUES (
    COALESCE(CAST(CASE WHEN '{{ $fromAI("cliente_id") }}' ~ '^\d+$' THEN '{{ $fromAI("cliente_id") }}' ELSE NULL END AS integer), -1),
    'aberto'
)
RETURNING id;
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TOOL 5 — adicionar_item_carrinho
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Name:** `adicionar_item_carrinho`

**Description:**
```
Adiciona um produto ao carrinho do cliente. Parâmetros: cliente_id (ID do cliente guardado anteriormente — NUNCA invente), produto_id (ID do produto retornado por buscar_produto — NUNCA invente), produto_nome (nome exato do produto retornado pela busca), preco_unitario (preço de venda retornado pela busca, apenas número como 8.50), quantidade (quantas unidades o cliente quer, apenas número inteiro como 3). O sistema criará ou usará o carrinho correto automaticamente.
```

**Query (cole no Execute Query):**
```sql
WITH cart AS (
    INSERT INTO "CARRINHOS" (cliente_id, status)
    SELECT COALESCE(CAST(CASE WHEN '{{ $fromAI("cliente_id") }}' ~ '^\d+$' THEN '{{ $fromAI("cliente_id") }}' ELSE NULL END AS integer), -1), 'aberto'
    WHERE EXISTS (SELECT 1 FROM "CLIENTES" WHERE id = COALESCE(CAST(CASE WHEN '{{ $fromAI("cliente_id") }}' ~ '^\d+$' THEN '{{ $fromAI("cliente_id") }}' ELSE NULL END AS integer), -1))
      AND NOT EXISTS (
        SELECT 1 FROM "CARRINHOS" 
        WHERE cliente_id = COALESCE(CAST(CASE WHEN '{{ $fromAI("cliente_id") }}' ~ '^\d+$' THEN '{{ $fromAI("cliente_id") }}' ELSE NULL END AS integer), -1)
          AND status = 'aberto'
    )
    RETURNING id
),
active_cart AS (
    SELECT id FROM cart
    UNION
    SELECT id FROM "CARRINHOS" 
    WHERE cliente_id = COALESCE(CAST(CASE WHEN '{{ $fromAI("cliente_id") }}' ~ '^\d+$' THEN '{{ $fromAI("cliente_id") }}' ELSE NULL END AS integer), -1)
      AND status = 'aberto'
    LIMIT 1
)
INSERT INTO "CARRINHO_ITENS" (carrinho_id, produto_id, produto_nome, preco_unitario, quantidade)
SELECT
    active_cart.id,
    CAST(CASE WHEN '{{ $fromAI("produto_id") }}' ~ '^\d+$' THEN '{{ $fromAI("produto_id") }}' ELSE NULL END AS integer),
    '{{ $fromAI("produto_nome") }}',
    CAST(CASE WHEN '{{ $fromAI("preco_unitario") }}' ~ '^\d+\.?\d*$' THEN '{{ $fromAI("preco_unitario") }}' ELSE '0' END AS numeric),
    CAST(CASE WHEN '{{ $fromAI("quantidade") }}' ~ '^\d+$' THEN '{{ $fromAI("quantidade") }}' ELSE '1' END AS integer)
FROM active_cart
RETURNING id, produto_nome, quantidade, preco_unitario;
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TOOL 6 — ver_carrinho
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Name:** `ver_carrinho`

**Description:**
```
Mostra todos os itens do carrinho ativo do cliente com nome, quantidade, preço unitário, subtotal de cada item e o total geral. Parâmetro: cliente_id (número inteiro do cliente).
```

**Query (cole no Execute Query):**
```sql
SELECT
    ci.id AS item_id,
    ci.produto_nome,
    ci.quantidade,
    ci.preco_unitario,
    (ci.quantidade * ci.preco_unitario) AS subtotal
FROM "CARRINHO_ITENS" ci
JOIN "CARRINHOS" c ON c.id = ci.carrinho_id
WHERE c.cliente_id = COALESCE(CAST(CASE WHEN '{{ $fromAI("cliente_id") }}' ~ '^\d+$' THEN '{{ $fromAI("cliente_id") }}' ELSE NULL END AS integer), -1)
  AND c.status = 'aberto'
ORDER BY ci.criado_em;
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TOOL 7 — remover_item_carrinho
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Name:** `remover_item_carrinho`

**Description:**
```
Remove um item específico do carrinho. Use o item_id retornado pela tool ver_carrinho. Parâmetro: item_id (número inteiro do item a remover).
```

**Query (cole no Execute Query):**
```sql
DELETE FROM "CARRINHO_ITENS"
WHERE id = CAST(CASE WHEN '{{ $fromAI("item_id") }}' ~ '^\d+$' THEN '{{ $fromAI("item_id") }}' ELSE NULL END AS integer)
RETURNING id;
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TOOL 8 — finalizar_carrinho
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Name:** `finalizar_carrinho`

**Description:**
```
Finaliza o carrinho ativo do cliente, marcando como em preparação. Use quando o cliente confirmar o pedido. Parâmetros: cliente_id (número inteiro do cliente), endereco_entrega (endereço completo ou 'Retirada no depósito'), forma_pagamento (Pix / Cartão / Dinheiro).
```

**Query (cole no Execute Query):**
```sql
UPDATE "CARRINHOS"
SET status = 'em_preparacao',
    endereco_entrega = '{{ $fromAI("endereco_entrega") }}',
    forma_pagamento = '{{ $fromAI("forma_pagamento") }}',
    atualizado_em = now()
WHERE cliente_id = COALESCE(CAST(CASE WHEN '{{ $fromAI("cliente_id") }}' ~ '^\d+$' THEN '{{ $fromAI("cliente_id") }}' ELSE NULL END AS integer), -1)
  AND status = 'aberto'
RETURNING id;
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TOOL 9 — salvar_orcamento
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Name:** `salvar_orcamento`

**Description:**
```
Salva todos os dados do orçamento no banco de dados. Use após coletar todas as informações do cliente. Parâmetros: cliente_id (inteiro), tipo_evento (texto), data_evento (formato YYYY-MM-DD), hora_inicio (formato HH:MM), hora_fim (formato HH:MM), num_convidados (inteiro), publico (adulto/infantil/misto), bebidas (texto com lista), preferencia_marca (texto), gelo (texto com sim/não e quantidade), comidas_petiscos (texto), produtos_gelados (gelados ou por conta), tipo_entrega (entrega ou retirada), endereco_entrega (endereço completo ou vazio), horario_entrega (horário preferido), forma_pagamento (pix/cartão/dinheiro/prazo), nota_fiscal (true ou false), limite_valor (número ou 0 se sem limite), resumo (texto do resumo formatado enviado ao cliente).
```

**Query (cole no Execute Query):**
```sql
INSERT INTO "ORCAMENTOS" (
    cliente_id,
    tipo_evento,
    data_evento,
    hora_inicio,
    hora_fim,
    num_convidados,
    publico,
    bebidas,
    preferencia_marca,
    gelo,
    comidas_petiscos,
    produtos_gelados,
    tipo_entrega,
    endereco_entrega,
    horario_entrega,
    forma_pagamento,
    nota_fiscal,
    limite_valor,
    resumo
) VALUES (
    CAST(CASE WHEN '{{ $fromAI("cliente_id") }}' ~ '^\d+$' THEN '{{ $fromAI("cliente_id") }}' ELSE NULL END AS integer),
    '{{ $fromAI("tipo_evento") }}',
    CAST(CASE WHEN '{{ $fromAI("data_evento") }}' ~ '^\d{4}-\d{2}-\d{2}$' THEN '{{ $fromAI("data_evento") }}' ELSE NULL END AS date),
    NULLIF('{{ $fromAI("hora_inicio") }}', ''),
    NULLIF('{{ $fromAI("hora_fim") }}', ''),
    CAST(CASE WHEN '{{ $fromAI("num_convidados") }}' ~ '^\d+$' THEN '{{ $fromAI("num_convidados") }}' ELSE '0' END AS integer),
    NULLIF('{{ $fromAI("publico") }}', ''),
    '{{ $fromAI("bebidas") }}',
    NULLIF('{{ $fromAI("preferencia_marca") }}', ''),
    NULLIF('{{ $fromAI("gelo") }}', ''),
    NULLIF('{{ $fromAI("comidas_petiscos") }}', ''),
    NULLIF('{{ $fromAI("produtos_gelados") }}', ''),
    NULLIF('{{ $fromAI("tipo_entrega") }}', ''),
    NULLIF('{{ $fromAI("endereco_entrega") }}', ''),
    NULLIF('{{ $fromAI("horario_entrega") }}', ''),
    NULLIF('{{ $fromAI("forma_pagamento") }}', ''),
    CASE WHEN lower('{{ $fromAI("nota_fiscal") }}') IN ('true','sim','yes','1') THEN true ELSE false END,
    CAST(CASE WHEN '{{ $fromAI("limite_valor") }}' ~ '^\d+\.?\d*$' THEN '{{ $fromAI("limite_valor") }}' ELSE '0' END AS numeric),
    '{{ $fromAI("resumo") }}'
)
RETURNING id;
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## TOOL 10 — obter_carrinho_ativo
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Name:** `obter_carrinho_ativo`

**Description:**
```
Verifica se o cliente já tem um carrinho aberto. Se retornar vazio, significa que precisa criar um novo carrinho com a tool criar_carrinho. Parâmetro: cliente_id (número inteiro do cliente retornado por buscar_cliente ou criar_cliente — NUNCA invente um número).
```

**Query (cole no Execute Query):**
```sql
SELECT id
FROM "CARRINHOS"
WHERE cliente_id = COALESCE(CAST(CASE WHEN '{{ $fromAI("cliente_id") }}' ~ '^\d+$' THEN '{{ $fromAI("cliente_id") }}' ELSE NULL END AS integer), -1)
  AND status = 'aberto'
ORDER BY criado_em DESC
LIMIT 1;
```

---

## RESUMO RÁPIDO

| # | Tool | Ação | Parâmetros |
|---|------|------|------------|
| 1 | `buscar_cliente` | SELECT | telefone |
| 2 | `criar_cliente` | INSERT/UPDATE | telefone, nome |
| 3 | `buscar_produto` | SELECT (fuzzy) | query |
| 4 | `criar_carrinho` | INSERT | cliente_id |
| 5 | `adicionar_item_carrinho` | INSERT | cliente_id, produto_id, produto_nome, preco_unitario, quantidade |
| 6 | `ver_carrinho` | SELECT | cliente_id |
| 7 | `remover_item_carrinho` | DELETE | item_id |
| 8 | `finalizar_carrinho` | UPDATE | cliente_id, endereco_entrega, forma_pagamento |
| 9 | `salvar_orcamento` | INSERT | todos os campos do orçamento (19 params) |
| 10 | `obter_carrinho_ativo` | SELECT | cliente_id |
