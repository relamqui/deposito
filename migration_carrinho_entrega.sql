-- ============================================================
-- MIGRAÇÃO: Adicionar endereco_entrega e forma_pagamento à CARRINHOS
-- Rode este script UMA VEZ no seu PostgreSQL
-- ============================================================

ALTER TABLE "public"."CARRINHOS"
    ADD COLUMN IF NOT EXISTS "endereco_entrega" TEXT,
    ADD COLUMN IF NOT EXISTS "forma_pagamento"  VARCHAR(100);
