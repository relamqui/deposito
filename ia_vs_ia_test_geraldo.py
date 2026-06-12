"""
🤖 IA vs IA — Cliente GPT (Seu Geraldo) conversa com o Vendedor Joel IA
O GPT-4 simula um cliente idoso confuso e conversa com o agente do n8n.
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
MAX_TURNOS = 30  # Aumentado para 30 porque Seu Geraldo fala devagar

# Instruções para o GPT (o "Cliente Simulado")
SYSTEM_PROMPT_CLIENTE = """Você é o **Seu Geraldo**, um senhor de 72 anos que está comprando pelo WhatsApp no Depósito Joel. Você é simpático mas BEM confuso com tecnologia e nomes de produtos.

## SUA PERSONALIDADE:
- Você NÃO sabe o nome exato dos produtos. Você DESCREVE eles vagamente.
- Você fala devagar, repete as coisas, se perde no meio da frase.
- Você manda mensagens curtas, como se estivesse digitando com dificuldade.
- Você usa expressões de idoso: "meu filho", "minha filha", "rapaz", "credo", "eita", "ah sim sim"
- Você às vezes confunde marcas e nomes
- Você é educado mas teimoso

## O QUE VOCÊ QUER COMPRAR (mas NÃO sabe os nomes):
1. Cerveja — Você diz: "aquela bebida gelada que vem na garrafa marrom, sabe? aquela de bar"
2. Coca-Cola — Você diz: "aquele refrigerante pretinho que borbulha, como é mesmo o nome..."
3. Suco de laranja — Você diz: "suco daquela fruta alaranjada, redonda..."
4. Água mineral — Você sabe pedir: "água" (mas pergunta se é da torneira ou não)
5. Linguiça toscana — Você diz: "aquela carne de porco embalada, tipo salsicha grande, sabe?"
6. Amendoim torrado — Você diz: "aquele trem que a gente come no bar vendo jogo, crocante, vem num saquinho"

## REGRAS DE COMPORTAMENTO:
- NUNCA diga o nome exato do produto, sempre descreva vagamente
- Quando o vendedor sugerir o produto correto, fique aliviado: "isso mesmo meu filho!! era isso que eu queria"
- Quando perguntar nome, diga "Geraldo da Silva"
- Quando perguntar telefone, demore uma mensagem: "eita... pera que vou ver aqui... minha neta que configurou esse trem"
- Depois diga o telefone: "5531999998888"
- Pergunte o preço de TUDO antes de aceitar
- Reclame que tá caro pelo menos UMA vez: "credo, tá caro hein meu filho? no meu tempo..."
- Depois aceite mesmo assim
- No final peça entrega: "manda pra cá meu filho, Rua das Flores, 88, perto da padaria do Zé"
- Pagamento: "pode ser naquele negócio do celular... como chama? Pix! isso, Pix."
- Quando terminar, agradeça bastante e diga tchau com "[FIM DA CONVERSA]"
- Se o Joel perguntar algo que você não entende, peça pra ele repetir

## REGRA CRÍTICA:
- Responda APENAS como Seu Geraldo. Nunca quebre o personagem.
- Máximo de 2 frases por mensagem, digitação lenta de idoso.
- Quando o pedido estiver finalizado e você se despedir, inclua "[FIM DA CONVERSA]".
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
            temperature=0.8 # Um pouco mais alto para mais criatividade
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ ERRO GPT: {str(e)}"


def main():
    print("=" * 65)
    print("  🤖 IA vs IA — Seu Geraldo vs Vendedor Joel IA")
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
    msg_cliente = "Ô de casa! Tem alguém aí meu filho? Queria ver uns trem pra comprar"
    
    for turno in range(1, MAX_TURNOS + 1):
        print(f"\n{'━' * 60}")
        print(f"  TURNO {turno}")
        print(f"{'━' * 60}")

        # ── Cliente (GPT) fala ──
        print(f"  🧑 Seu Geraldo (GPT): {msg_cliente[:120]}{'...' if len(msg_cliente) > 120 else ''}")
        
        # ── Joel IA responde ──
        inicio = time.time()
        resp_joel = enviar_para_joel(msg_cliente, SESSION_ID)
        tempo_joel = time.time() - inicio
        
        preview_joel = resp_joel[:150] + "..." if len(resp_joel) > 150 else resp_joel
        print(f"  🤖 Joel IA:           {preview_joel}")
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
            print(f"\n  🏁 CONVERSA FINALIZADA pelo Seu Geraldo!")
            conversa_log.append({
                "turno": turno + 1,
                "cliente": msg_cliente,
                "vendedor": "(conversa encerrada)",
                "tempo_joel": 0,
                "erro_joel": False
            })
            break

        # Pausa entre turnos
        time.sleep(1.5)

    tempo_total = time.time() - inicio_total
    total_turnos = len(conversa_log)
    erros_joel = sum(1 for c in conversa_log if c["erro_joel"])

    # ══════════════════════════════════════════════════════════
    # GERAR RELATÓRIO MARKDOWN
    # ══════════════════════════════════════════════════════════
    md = f"""# 🤖 Relatório: IA vs IA — Seu Geraldo vs Vendedor Joel IA

**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
**Session ID:** `{SESSION_ID}`  
**Modelo GPT:** gpt-4o-mini (Seu Geraldo simulado)  
**Modelo Joel IA:** n8n AI Agent (vendedor)  
**Tempo Total:** {tempo_total:.1f}s  
**Turnos:** {total_turnos}  
**Erros do Joel IA:** {erros_joel}/{total_turnos} ({(erros_joel/max(total_turnos,1)*100):.0f}%)

---

## 🎯 Cenário do Teste

O GPT-4 simula um cliente chamado **Seu Geraldo**, um idoso confuso de 72 anos.  
Lista de compras programada: cerveja, coca, suco, água, linguiça e amendoim (descritos vagamente, sem nomes certos).  
O teste visa avaliar a capacidade do Joel IA de entender contexto, ter paciência e guiar a venda.
A conversa é **100% autônoma**.

---

## 💬 Transcrição Completa

"""

    for c in conversa_log:
        status = "❌" if c["erro_joel"] else "✅"
        md += f"""### {status} Turno {c['turno']} ({c['tempo_joel']}s)

> **🧑 Seu Geraldo (GPT):** {c['cliente']}

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

    report_path = "ia_vs_ia_report_geraldo.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\n{'=' * 65}")
    print(f"  ✅ RELATÓRIO SALVO: {report_path}")
    print(f"  ⏱️  Tempo total: {tempo_total:.1f}s")
    print(f"  📊 Turnos: {total_turnos} | Erros Joel: {erros_joel}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
