-- ============================================================
-- MIGRAÇÃO: Tabelas para o Agente IA do n8n
-- Depósito Joel — Orçamentos + Carrinho de Compras
-- ============================================================
-- Rode este script no seu PostgreSQL (mesmo banco do DEPOSITO_JOEL)
-- ============================================================

-- 1. CLIENTES (identificados pelo WhatsApp)
CREATE TABLE IF NOT EXISTS "public"."CLIENTES" (
    "id"         SERIAL PRIMARY KEY,
    "telefone"   VARCHAR(20) NOT NULL UNIQUE,  -- número WhatsApp (ex: 5511999999999)
    "nome"       VARCHAR(200),
    "criado_em"  TIMESTAMP DEFAULT now(),
    "atualizado_em" TIMESTAMP DEFAULT now()
);

-- Índice para busca rápida por telefone
CREATE INDEX IF NOT EXISTS idx_clientes_telefone ON "public"."CLIENTES" ("telefone");

-- ============================================================
-- 2. ORÇAMENTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS "public"."ORCAMENTOS" (
    "id"                SERIAL PRIMARY KEY,
    "cliente_id"        INTEGER NOT NULL REFERENCES "public"."CLIENTES"("id"),
    "tipo_evento"       VARCHAR(100),          -- festa, churrasco, casamento...
    "data_evento"       DATE,
    "hora_inicio"       VARCHAR(10),           -- ex: "18:00"
    "hora_fim"          VARCHAR(10),           -- ex: "23:00"
    "num_convidados"    INTEGER,
    "publico"           VARCHAR(50),           -- adulto, infantil, misto
    "bebidas"           TEXT,                  -- lista de bebidas desejadas
    "preferencia_marca" TEXT,                  -- marca preferida ou "aceita sugestão"
    "gelo"              VARCHAR(200),          -- sim/não + quantidade
    "comidas_petiscos"  TEXT,                  -- salgados, carvão, descartáveis...
    "produtos_gelados"  VARCHAR(100),          -- "gelados" ou "gela por conta"
    "tipo_entrega"      VARCHAR(20),           -- 'entrega' ou 'retirada'
    "endereco_entrega"  TEXT,                  -- endereço completo (se entrega)
    "horario_entrega"   VARCHAR(100),          -- horário preferido
    "forma_pagamento"   VARCHAR(100),          -- Pix, cartão, dinheiro, prazo
    "nota_fiscal"       BOOLEAN DEFAULT false,
    "limite_valor"      NUMERIC(10,2),         -- NULL = sem limite definido
    "resumo"            TEXT,                  -- resumo formatado enviado ao cliente
    "status"            VARCHAR(30) DEFAULT 'pendente',  -- pendente, respondido, fechado, cancelado
    "criado_em"         TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orcamentos_cliente ON "public"."ORCAMENTOS" ("cliente_id");
CREATE INDEX IF NOT EXISTS idx_orcamentos_status ON "public"."ORCAMENTOS" ("status");

-- ============================================================
-- 3. CARRINHOS (sessão de compra)
-- ============================================================
CREATE TABLE IF NOT EXISTS "public"."CARRINHOS" (
    "id"            SERIAL PRIMARY KEY,
    "cliente_id"    INTEGER NOT NULL REFERENCES "public"."CLIENTES"("id"),
    "status"        VARCHAR(20) DEFAULT 'aberto',  -- aberto, finalizado, cancelado
    "criado_em"     TIMESTAMP DEFAULT now(),
    "atualizado_em" TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_carrinhos_cliente ON "public"."CARRINHOS" ("cliente_id");
CREATE INDEX IF NOT EXISTS idx_carrinhos_status ON "public"."CARRINHOS" ("status");

-- ============================================================
-- 4. ITENS DO CARRINHO
-- ============================================================
CREATE TABLE IF NOT EXISTS "public"."CARRINHO_ITENS" (
    "id"            SERIAL PRIMARY KEY,
    "carrinho_id"   INTEGER NOT NULL REFERENCES "public"."CARRINHOS"("id") ON DELETE CASCADE,
    "produto_id"    INTEGER NOT NULL REFERENCES "public"."DEPOSITO_JOEL"("id"),
    "produto_nome"  VARCHAR(300),              -- snapshot do nome no momento da adição
    "preco_unitario" NUMERIC(10,2),            -- snapshot do preço no momento da adição
    "quantidade"    INTEGER NOT NULL DEFAULT 1,
    "criado_em"     TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_carrinho_itens_carrinho ON "public"."CARRINHO_ITENS" ("carrinho_id");

-- ============================================================
-- 5. EXTENSÃO PARA BUSCA FUZZY (pg_trgm)
-- ============================================================
-- Permite o n8n buscar produtos mesmo com erro de digitação
-- usando similarity() e o operador %
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Índice trigram no nome dos produtos para busca fuzzy rápida
CREATE INDEX IF NOT EXISTS idx_deposito_joel_nome_trgm
ON "public"."DEPOSITO_JOEL" USING gin ("nome" gin_trgm_ops);

-- ============================================================
-- QUERIES ÚTEIS PARA O N8N (referência)
-- ============================================================

-- 🔍 BUSCAR PRODUTO COM FUZZY (usar no n8n como tool)
-- Substitua $1 pelo texto digitado pelo cliente
-- SELECT id, nome, preco_venda, estoque, unidade,
--        similarity(nome, $1) AS score
-- FROM "DEPOSITO_JOEL"
-- WHERE ativo = true
--   AND similarity(nome, $1) > 0.15
-- ORDER BY score DESC
-- LIMIT 5;

-- 🛒 VER CARRINHO ATIVO DO CLIENTE
-- SELECT ci.produto_nome, ci.quantidade, ci.preco_unitario,
--        (ci.quantidade * ci.preco_unitario) AS subtotal
-- FROM "CARRINHO_ITENS" ci
-- JOIN "CARRINHOS" c ON c.id = ci.carrinho_id
-- JOIN "CLIENTES" cl ON cl.id = c.cliente_id
-- WHERE cl.telefone = $1
--   AND c.status = 'aberto';

-- 💰 TOTAL DO CARRINHO
-- SELECT SUM(ci.quantidade * ci.preco_unitario) AS total
-- FROM "CARRINHO_ITENS" ci
-- JOIN "CARRINHOS" c ON c.id = ci.carrinho_id
-- JOIN "CLIENTES" cl ON cl.id = c.cliente_id
-- WHERE cl.telefone = $1
--   AND c.status = 'aberto';
