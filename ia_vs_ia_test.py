"""
🤖 IA vs IA — Cliente GPT conversa com o Vendedor Joel IA
O GPT-4 simula um cliente real e conversa com o agente do n8n.
O script monitora cada turno e gera um relatório detalhado.
"""
import requests
import json
import time
import uuid
from datetime import datetime
from openai import OpenAI

# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════
OPENAI_API_KEY = "SUA_API_KEY_AQUI"
CHAT_URL = "https://n8n-n8n.ioms5g.easypanel.host/webhook/86ea94a3-ba6c-4f18-94c3-43c771c99827/chat"
SESSION_ID = f"ia-vs-ia-{uuid.uuid4().hex[:8]}"
MAX_TURNOS = 20  # Limite de segurança para não ficar em loop infinito

# Instruções para o GPT (o "Cliente Simulado")
SYSTEM_PROMPT_CLIENTE = """Você é um CLIENTE chamado Carlos que está comprando pelo WhatsApp no Depósito Joel (uma distribuidora de bebidas e conveniências).

## SEU OBJETIVO:
Fazer uma compra completa para um churrasco de aniversário no sábado.

## O QUE VOCÊ QUER COMPRAR:
1. Cervejas (qualquer marca disponível) — 6 unidades
2. Coca-Cola lata — 4 unidades
3. Suco de laranja — 2 unidades
4. Água mineral — 6 unidades
5. Linguiça toscana — 3 unidades
6. Amendoim torrado — 2 unidades

## REGRAS DE COMPORTAMENTO:
- Fale como um cliente REAL e informal do WhatsApp (abreviações, emojis, etc.)
- Quando o vendedor perguntar seu nome, diga "Carlos"
- Quando perguntar seu telefone, diga "5521988887777"
- Se o vendedor sugerir um produto alternativo, ACEITE a sugestão
- Depois de adicionar tudo, peça para VER O CARRINHO
- Se estiver tudo ok, peça para FINALIZAR O PEDIDO
- Diga que vai pagar no PIX e que quer ENTREGA na Rua do Churrasco, 42
- Quando o vendedor confirmar que o pedido foi finalizado, responda com um agradecimento e diga "tchau"

## REGRA CRÍTICA:
- Responda APENAS como cliente. Nunca quebre o personagem.
- Sempre responda com UMA mensagem curta por vez (máximo 2 frases).
- Quando o pedido estiver finalizado e você se despedir, escreva exatamente "[FIM DA CONVERSA]" na sua mensagem final.
"""


def enviar_para_joel(mensagem, session_id):
    """Envia mensagem para o Joel IA (n8n Chat Trigger)."""
    payload = {
        "action": "sendMessage",
        "sessionId": session_id,
        "chatInput": mensagem
    }
    try:
        resp = requests.post(CHAT_URL, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return data.get("output", data.get("text", json.dumps(data, ensure_ascii=False)))
        elif isinstance(data, list) and len(data) > 0:
            return data[0].get("output", data[0].get("text", json.dumps(data[0], ensure_ascii=False)))
        return str(data)
    except requests.exceptions.Timeout:
        return "⚠️ TIMEOUT: Joel IA demorou mais de 90s para responder."
    except requests.exceptions.RequestException as e:
        return f"⚠️ ERRO DE REDE: {str(e)}"
    except Exception as e:
        return f"⚠️ ERRO: {str(e)}"


def gerar_resposta_cliente(client_openai, historico_conversa):
    """Usa GPT-4 para gerar a próxima mensagem do cliente."""
    try:
        response = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=historico_conversa,
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ ERRO GPT: {str(e)}"


def main():
    print("=" * 65)
    print("  🤖 IA vs IA — Cliente GPT vs Vendedor Joel IA")
    print("  Depósito Joel — Teste Conversacional Autônomo")
    print("=" * 65)
    print(f"\n  Session ID:  {SESSION_ID}")
    print(f"  Joel IA URL: {CHAT_URL}")
    print(f"  GPT Model:   gpt-4o-mini")
    print(f"  Max Turnos:  {MAX_TURNOS}")
    print(f"  Início:      {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 65)

    client_openai = OpenAI(api_key=OPENAI_API_KEY)

    # Histórico para o GPT (cliente)
    historico_gpt = [
        {"role": "system", "content": SYSTEM_PROMPT_CLIENTE}
    ]

    conversa_log = []
    inicio_total = time.time()

    # Primeira mensagem: o cliente inicia a conversa
    msg_cliente = "Oi, boa tarde! Tô querendo fazer um pedido pro churrasco de sábado 🍖"
    
    for turno in range(1, MAX_TURNOS + 1):
        print(f"\n{'━' * 60}")
        print(f"  TURNO {turno}")
        print(f"{'━' * 60}")

        # ── Cliente (GPT) fala ──
        print(f"  🧑 Carlos (GPT):  {msg_cliente[:120]}{'...' if len(msg_cliente) > 120 else ''}")
        
        # ── Joel IA responde ──
        inicio = time.time()
        resp_joel = enviar_para_joel(msg_cliente, SESSION_ID)
        tempo_joel = time.time() - inicio
        
        preview_joel = resp_joel[:150] + "..." if len(resp_joel) > 150 else resp_joel
        print(f"  🤖 Joel IA:       {preview_joel}")
        print(f"  ⏱️  Joel respondeu em {tempo_joel:.1f}s")

        # Guardar no log
        conversa_log.append({
            "turno": turno,
            "cliente": msg_cliente,
            "vendedor": resp_joel,
            "tempo_joel": round(tempo_joel, 2),
            "erro_joel": "⚠️" in resp_joel
        })

        # Adicionar ao histórico do GPT
        historico_gpt.append({"role": "user", "content": f"[Resposta do vendedor Joel IA]: {resp_joel}"})

        # Verificar se o Joel deu erro
        if "⚠️" in resp_joel:
            # GPT precisa saber que deu erro
            historico_gpt.append({"role": "user", "content": "[SISTEMA: O vendedor deu erro. Tente reformular seu pedido ou pergunte de outra forma.]"})

        # ── GPT gera próxima mensagem do cliente ──
        inicio_gpt = time.time()
        msg_cliente = gerar_resposta_cliente(client_openai, historico_gpt)
        tempo_gpt = time.time() - inicio_gpt

        print(f"  🧠 GPT pensou em {tempo_gpt:.1f}s")

        # Adicionar resposta do GPT ao histórico
        historico_gpt.append({"role": "assistant", "content": msg_cliente})

        # Verificar se a conversa terminou
        if "[FIM DA CONVERSA]" in msg_cliente:
            print(f"\n  🏁 CONVERSA FINALIZADA pelo cliente GPT!")
            conversa_log.append({
                "turno": turno + 1,
                "cliente": msg_cliente,
                "vendedor": "(conversa encerrada)",
                "tempo_joel": 0,
                "erro_joel": False
            })
            break

        # Pausa entre turnos (simula digitação)
        time.sleep(1.5)

    tempo_total = time.time() - inicio_total
    total_turnos = len(conversa_log)
    erros_joel = sum(1 for c in conversa_log if c["erro_joel"])

    # ══════════════════════════════════════════════════════════
    # GERAR RELATÓRIO MARKDOWN
    # ══════════════════════════════════════════════════════════
    md = f"""# 🤖 Relatório: IA vs IA — Cliente GPT vs Vendedor Joel IA

**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
**Session ID:** `{SESSION_ID}`  
**Modelo GPT:** gpt-4o-mini (cliente simulado)  
**Modelo Joel IA:** n8n AI Agent (vendedor)  
**Tempo Total:** {tempo_total:.1f}s  
**Turnos:** {total_turnos}  
**Erros do Joel IA:** {erros_joel}/{total_turnos} ({(erros_joel/max(total_turnos,1)*100):.0f}%)

---

## 🎯 Cenário do Teste

O GPT-4 simula um cliente chamado **Carlos** que quer comprar para um **churrasco de aniversário**.  
Lista de compras programada: 6 cervejas, 4 Coca-Cola lata, 2 sucos, 6 águas, 3 linguiças, 2 amendoins.  
A conversa é **100% autônoma** — nenhum humano interveio.

---

## 💬 Transcrição Completa

"""

    for c in conversa_log:
        status = "❌" if c["erro_joel"] else "✅"
        md += f"""### {status} Turno {c['turno']} ({c['tempo_joel']}s)

> **🧑 Carlos (GPT):** {c['cliente']}

**🤖 Joel IA:**
{c['vendedor']}

---

"""

    md += f"""## 📊 Resumo de Performance

| Métrica | Valor |
|---------|-------|
| Turnos Totais | {total_turnos} |
| Respostas OK do Joel | {total_turnos - erros_joel} |
| Erros do Joel | {erros_joel} |
| Taxa de Sucesso Joel | {((total_turnos - erros_joel)/max(total_turnos,1)*100):.0f}% |
| Tempo Total | {tempo_total:.1f}s |
| Tempo Médio Joel | {(sum(c['tempo_joel'] for c in conversa_log)/max(total_turnos,1)):.1f}s |

## 🔍 Análise de Erros

"""
    if erros_joel == 0:
        md += "Nenhum erro detectado! ✅\n"
    else:
        md += "| Turno | Mensagem do Cliente | Erro |\n|-------|--------------------|----- |\n"
        for c in conversa_log:
            if c["erro_joel"]:
                md += f"| {c['turno']} | {c['cliente'][:60]}... | {c['vendedor'][:80]}... |\n"

    report_path = "ia_vs_ia_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\n{'=' * 65}")
    print(f"  ✅ RELATÓRIO SALVO: {report_path}")
    print(f"  ⏱️  Tempo total: {tempo_total:.1f}s")
    print(f"  📊 Turnos: {total_turnos} | Erros Joel: {erros_joel}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
