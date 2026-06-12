# Guia de Configuração — n8n AI Agent (Depósito Joel)

## Pré-requisitos

- n8n rodando (self-hosted ou cloud)
- PostgreSQL com a tabela `DEPOSITO_JOEL` já funcionando
- Credencial PostgreSQL configurada no n8n
- Credencial de LLM configurada (OpenAI, Google Gemini, etc.)
- Integração WhatsApp configurada (Evolution API, Z-API, etc.)

---

## Passo 1: Rodar a Migração no PostgreSQL

Execute o arquivo `migrations.sql` no seu banco de dados PostgreSQL.  
Isso vai criar as tabelas: `CLIENTES`, `ORCAMENTOS`, `CARRINHOS`, `CARRINHO_ITENS` e a extensão `pg_trgm` para busca fuzzy.

```bash
psql -U postgres -d seu_banco -f migrations.sql
```

Ou cole o conteúdo do `migrations.sql` no pgAdmin / DBeaver e execute.

> ⚠️ **IMPORTANTE**: A extensão `pg_trgm` precisa de permissão de superuser. Se estiver em hosting compartilhado, peça ao suporte para habilitar.

---

## Passo 2: Estrutura do Workflow no n8n

O workflow tem esta estrutura:

```
[Trigger WhatsApp] → [AI Agent] → [Resposta WhatsApp]
                         ↓
                    [10 Tools PostgreSQL]
```

### Nodes necessários:

| Node | Tipo | Função |
|------|------|--------|
| Trigger | Webhook / Evolution API | Recebe mensagens do WhatsApp |
| AI Agent | @n8n/n8n-nodes-langchain.agent | Processamento de linguagem natural |
| LLM | OpenAI / Google Gemini | Modelo de linguagem |
| Tools 1-10 | PostgreSQL (Execute Query) | Operações no banco de dados |
| Responder | HTTP Request / Evolution API | Envia resposta pelo WhatsApp |

---

## Passo 3: Configurar o AI Agent

1. Adicione o node **AI Agent** ao workflow
2. Em **System Message**, cole o conteúdo da seção "PROMPT" do arquivo `prompt_agente_n8n.md`
3. Conecte seu LLM (OpenAI GPT-4, Gemini, etc.)
4. Configure a **memória** como `Window Buffer Memory` com `sessionKey` = número de telefone do cliente (assim cada cliente tem seu próprio contexto)

### Configuração da memória:
- **Session Key**: `{{ $json.telefone }}` (ou o campo que vem do seu trigger WhatsApp)
- **Context Window Length**: `20` mensagens (suficiente para uma conversa completa)

---

## Passo 4: Configurar as Tools

Para cada tool, crie um node **PostgreSQL** do tipo **Execute Query** e conecte como **Tool** do AI Agent.

### Como configurar cada Tool:

1. No AI Agent, clique em **+ Tool**
2. Selecione **PostgreSQL** (Call n8n Tool)
3. Configure:
   - **Name**: nome da tool (ex: `buscar_produto`)
   - **Description**: copie a descrição do arquivo `prompt_agente_n8n.md`
   - **Query**: copie a query SQL correspondente

### Lista das 10 Tools:

| # | Nome | Parâmetros de entrada |
|---|------|-----------------------|
| 1 | `buscar_cliente` | `telefone` (string) |
| 2 | `criar_cliente` | `telefone` (string), `nome` (string) |
| 3 | `buscar_produto` | `query` (string) — texto digitado pelo cliente |
| 4 | `criar_carrinho` | `cliente_id` (number) |
| 5 | `adicionar_item_carrinho` | `carrinho_id`, `produto_id`, `produto_nome`, `preco_unitario`, `quantidade` |
| 6 | `ver_carrinho` | `cliente_id` (number) |
| 7 | `remover_item_carrinho` | `item_id` (number) |
| 8 | `finalizar_carrinho` | `cliente_id` (number) |
| 9 | `salvar_orcamento` | todos os campos do orçamento |
| 10 | `obter_carrinho_ativo` | `cliente_id` (number) |

---

## Passo 5: Configurar o Trigger WhatsApp

Depende da sua integração. Exemplos comuns:

### Evolution API:
```
Trigger: Webhook
URL: https://seu-n8n.com/webhook/deposito-joel
Método: POST
```

O body da mensagem geralmente tem:
```json
{
  "data": {
    "key": {
      "remoteJid": "5511999999999@s.whatsapp.net"
    },
    "message": {
      "conversation": "texto da mensagem"
    }
  }
}
```

Extraia o telefone: `{{ $json.data.key.remoteJid.replace('@s.whatsapp.net', '') }}`

---

## Passo 6: Enviar a Resposta

Depois do AI Agent processar, pegue o output e envie de volta pelo WhatsApp usando HTTP Request ou o node da sua integração.

---

## Dicas e Troubleshooting

### 1. Busca fuzzy não funciona
- Verifique se a extensão `pg_trgm` está instalada: `SELECT * FROM pg_extension WHERE extname = 'pg_trgm';`
- Se não estiver, rode: `CREATE EXTENSION pg_trgm;`

### 2. Agente confuso com muitas tools
- Use descrições claras e específicas em cada tool
- Teste cada tool individualmente antes de conectar ao agente

### 3. Cliente enviando áudio
- Configure a transcrição de áudio ANTES do AI Agent (use Whisper ou Google Speech-to-Text)
- Passe o texto transcrito como input para o agente

### 4. Memória do contexto
- Use `Window Buffer Memory` com session key = telefone
- Isso garante que cada cliente tem sua própria conversa
- Se o cliente voltar depois de muito tempo, o contexto é mantido

### 5. SQL Injection
- **IMPORTANTE**: As queries usam interpolação de string (`{{ $json.campo }}`). Para produção, considere usar **parameterized queries** ou sanitizar os inputs no n8n usando um Code node antes das tools PostgreSQL.
