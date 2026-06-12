"""
Simulação de Conversa Completa com o Agente IA — Depósito Joel
Envia mensagens como se fosse um cliente no WhatsApp e registra
toda a conversa (ida e volta) em um relatório Markdown.
"""
import requests
import json
import time
import uuid
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════
CHAT_URL = "https://n8n-n8n.ioms5g.easypanel.host/webhook/86ea94a3-ba6c-4f18-94c3-43c771c99827/chat"
SESSION_ID = f"teste-compra-{uuid.uuid4().hex[:8]}"

# Roteiro da conversa (simula um cliente real comprando para churrasco)
# Usa produtos que EXISTEM no banco + testa marcas que NÃO existem
# para validar a sugestão inteligente de alternativas
ROTEIRO = [
    {
        "etapa": "Saudação",
        "mensagem": "Oi, boa tarde! Meu nome é Lucas. Quero fazer um pedido pro churrasco de sábado."
    },
    {
        "etapa": "Pedir Cerveja (marca que não existe — teste de sugestão)",
        "mensagem": "Vocês tem Heineken? Quero umas cervejas pro churrasco."
    },
    {
        "etapa": "Aceitar sugestão e adicionar cerveja",
        "mensagem": "Pode ser a Pilsen mesmo, coloca 6 unidades."
    },
    {
        "etapa": "Pedir Refrigerante (produto real)",
        "mensagem": "Coloca também 4 Coca-Cola lata e 2 suco de laranja."
    },
    {
        "etapa": "Pedir Linguiça e Carvão (testar item de churrasco)",
        "mensagem": "Vocês tem linguiça toscana? E amendoim torrado?"
    },
    {
        "etapa": "Adicionar linguiça e amendoim",
        "mensagem": "Manda 3 linguiça toscana e 2 amendoim torrado."
    },
    {
        "etapa": "Pedir Água e Energético",
        "mensagem": "Quase esqueci, manda 6 água mineral e 4 energético."
    },
    {
        "etapa": "Ver Carrinho",
        "mensagem": "Deixa eu ver como ficou o carrinho todo."
    },
    {
        "etapa": "Alterar Quantidade (reduzir cerveja)",
        "mensagem": "Diminui a cerveja pra 4 unidades ao invés de 6."
    },
    {
        "etapa": "Remover Item (tirar energético)",
        "mensagem": "Tira o energético, mudei de ideia."
    },
    {
        "etapa": "Carrinho Final",
        "mensagem": "Me mostra o carrinho atualizado com o total final."
    },
    {
        "etapa": "Finalizar Pedido",
        "mensagem": "Tá ótimo! Fecha o pedido. Vou pagar no Pix, entrega na Rua Marechal Rondon, 456."
    },
]


def enviar_mensagem(mensagem, session_id):
    """Envia uma mensagem para o AI Agent via Chat Trigger do n8n."""
    payload = {
        "action": "sendMessage",
        "sessionId": session_id,
        "chatInput": mensagem
    }
    
    try:
        resp = requests.post(CHAT_URL, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        
        # O n8n Chat Trigger retorna a resposta do agente no campo "output"
        if isinstance(data, dict):
            return data.get("output", data.get("text", json.dumps(data, ensure_ascii=False)))
        elif isinstance(data, list) and len(data) > 0:
            return data[0].get("output", data[0].get("text", json.dumps(data[0], ensure_ascii=False)))
        else:
            return str(data)
    except requests.exceptions.Timeout:
        return "⚠️ TIMEOUT: O agente demorou mais de 90 segundos para responder."
    except requests.exceptions.RequestException as e:
        return f"⚠️ ERRO DE REDE: {str(e)}"
    except Exception as e:
        return f"⚠️ ERRO: {str(e)}"


def main():
    print("=" * 60)
    print("  SIMULAÇÃO DE CONVERSA COM O AGENTE IA")
    print("  Depósito Joel — Teste End-to-End Conversacional")
    print("=" * 60)
    print(f"\n  Session ID: {SESSION_ID}")
    print(f"  Chat URL:   {CHAT_URL}")
    print(f"  Início:     {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)

    conversa_log = []
    inicio_total = time.time()

    for i, passo in enumerate(ROTEIRO, 1):
        etapa = passo["etapa"]
        msg = passo["mensagem"]
        
        print(f"\n{'─' * 50}")
        print(f"  📍 Etapa {i}/{len(ROTEIRO)}: {etapa}")
        print(f"{'─' * 50}")
        print(f"  🧑 Cliente: {msg}")

        inicio = time.time()
        resposta = enviar_mensagem(msg, SESSION_ID)
        tempo = time.time() - inicio

        # Limitar preview no terminal
        preview = resposta[:200] + "..." if len(resposta) > 200 else resposta
        print(f"  🤖 Agente:  {preview}")
        print(f"  ⏱️  Tempo:   {tempo:.1f}s")

        conversa_log.append({
            "etapa": i,
            "titulo": etapa,
            "cliente": msg,
            "agente": resposta,
            "tempo": round(tempo, 2),
            "sucesso": "⚠️" not in resposta
        })

        # Pausa de 2 segundos entre mensagens (simula digitação humana)
        if i < len(ROTEIRO):
            time.sleep(2)

    tempo_total = time.time() - inicio_total
    sucessos = sum(1 for c in conversa_log if c["sucesso"])

    # ══════════════════════════════════════════════════════════
    # GERAR RELATÓRIO MARKDOWN
    # ══════════════════════════════════════════════════════════
    md = f"""# 💬 Relatório: Simulação de Conversa com o Agente IA

**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
**Session ID:** `{SESSION_ID}`  
**Tempo Total:** {tempo_total:.1f}s  
**Etapas Executadas:** {len(conversa_log)}  
**Respostas OK:** {sucessos}/{len(conversa_log)} ({(sucessos/len(conversa_log)*100):.0f}%)

---

## 🎯 Cenário do Teste

O script simula um cliente chamado **Lucas** preparando um **churrasco de sábado**.  
O roteiro inclui:
- Pedido de marca que **NÃO existe** no estoque (Heineken) → espera-se sugestão da Pilsen
- Pedido de produtos que **existem** no estoque (Coca-Cola, Suco, Linguiça, etc.)
- **Alteração de quantidade** (reduzir cerveja de 6 para 4)
- **Remoção de item** (tirar energético)
- **Finalização** com endereço de entrega e forma de pagamento

---

## Transcrição Completa da Conversa

"""

    for c in conversa_log:
        status = "✅" if c["sucesso"] else "❌"
        md += f"""### {status} Etapa {c['etapa']}: {c['titulo']} ({c['tempo']}s)

> **🧑 Cliente:** {c['cliente']}

**🤖 Agente:**
{c['agente']}

---

"""

    # Resumo final
    md += f"""## 📊 Resumo de Performance

| Métrica | Valor |
|---------|-------|
| Etapas Totais | {len(conversa_log)} |
| Respostas OK | {sucessos} |
| Falhas | {len(conversa_log) - sucessos} |
| Taxa de Sucesso | {(sucessos/len(conversa_log)*100):.0f}% |
| Tempo Total | {tempo_total:.1f}s |
| Tempo Médio/Resposta | {(tempo_total/len(conversa_log)):.1f}s |
"""

    report_path = "conversa_ia_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\n{'=' * 60}")
    print(f"  ✅ SIMULAÇÃO CONCLUÍDA!")
    print(f"  📄 Relatório salvo em: {report_path}")
    print(f"  ⏱️  Tempo total: {tempo_total:.1f}s")
    print(f"  📊 Taxa de sucesso: {sucessos}/{len(conversa_log)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
