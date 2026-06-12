"""
Simulação de Compra Completa — Integração End-to-End
"""
import json
import sys
import time

MCP_URL = "https://n8n-n8n.ioms5g.easypanel.host/mcp/f9f72e5c-3832-4e8c-a6bf-e05f87e29d1b"

try:
    from test_mcp_tools import MCPClient
except ImportError:
    print("Erro: Precisa do test_mcp_tools.py na mesma pasta.")
    sys.exit(1)

def extrair_dados(response, chaves=["id"]):
    try:
        content = response["result"]["content"][0]["text"]
        data = json.loads(content)
        if len(data) > 0:
            if len(chaves) == 1: return data[0].get(chaves[0])
            return [data[0].get(k) for k in chaves]
    except Exception: pass
    return None

def extrair_lista(response):
    try:
        content = response["result"]["content"][0]["text"]
        return json.loads(content)
    except Exception: return []

def main():
    client = MCPClient(MCP_URL)
    client.connect(timeout=15)
    
    # Usa um telefone unico por run baseado no timestamp
    tel = "55119999" + str(int(time.time()))[-4:]
    nome = "Cliente Simulação"
    resp = client.call_tool("criar_cliente1", {"telefone": tel, "nome": nome})
    cliente_id = extrair_dados(resp, ["id"])
    
    termos = ["coca lata", "pilsen", "agua mineral", "suco", "energetico", "leite", "cafe", "mussarela", "iogurte", "manteiga"]
    produtos = []
    for termo in termos:
        resp = client.call_tool("buscar_produto1", {"query": termo})
        lista = extrair_lista(resp)
        if lista:
            p = lista[0]
            if p["id"] not in [x["id"] for x in produtos]: produtos.append(p)
        if len(produtos) == 10: break

    resp = client.call_tool("criar_carrinho1", {"cliente_id": str(cliente_id)})
    carrinho_id = extrair_dados(resp, ["id"])

    # Adicionar 10
    itens_iniciais_log = []
    for p in produtos:
        client.call_tool("adicionar_item_carrinho1", {"carrinho_id": str(carrinho_id), "produto_id": str(p["id"]), "produto_nome": p["nome"], "preco_unitario": str(p["preco_venda"]), "quantidade": "1"})
        itens_iniciais_log.append(f"- **{p['nome']}** (1 un. a R$ {p['preco_venda']})")

    # Ver carrinho para pegar IDs
    resp = client.call_tool("ver_carrinho1", {"cliente_id": str(cliente_id)})
    carrinho_itens = extrair_lista(resp)

    # Alterar 3 (removendo e adicionando 3 un)
    itens_alterados_log = []
    for i in range(3):
        item = carrinho_itens[i]
        client.call_tool("remover_item_carrinho1", {"item_id": str(item["item_id"])})
        prod_ref = produtos[i]
        client.call_tool("adicionar_item_carrinho1", {"carrinho_id": str(carrinho_id), "produto_id": str(prod_ref["id"]), "produto_nome": prod_ref["nome"], "preco_unitario": str(prod_ref["preco_venda"]), "quantidade": "3"})
        itens_alterados_log.append(f"- **{prod_ref['nome']}** alterado para **3 unidades**")

    # Recarregar carrinho para atualizar os IDs que sobraram
    resp = client.call_tool("ver_carrinho1", {"cliente_id": str(cliente_id)})
    carrinho_atualizado = extrair_lista(resp)
    
    # Remover 5 para sobrar 5 (pois 10 - 5 = 5)
    itens_removidos_log = []
    # Remover do final para nao afetar os primeiros que acabamos de alterar
    para_remover = carrinho_atualizado[-5:]
    for item in para_remover:
        client.call_tool("remover_item_carrinho1", {"item_id": str(item["item_id"])})
        itens_removidos_log.append(f"- **{item['produto_nome']}** foi excluído do carrinho")

    # Ver carrinho final
    resp = client.call_tool("ver_carrinho1", {"cliente_id": str(cliente_id)})
    carrinho_final = extrair_lista(resp)
    total_compra = sum(float(item["subtotal"]) for item in carrinho_final)
    
    client.call_tool("finalizar_carrinho1", {"cliente_id": str(cliente_id)})
    client.disconnect()

    md = f"""# Relatório: Simulação de Compra Completa (Fluxo Realista)

Neste cenário de integração End-to-End, o Agente cadastrou um cliente novo, inseriu 10 produtos no carrinho, processou a mudança de quantidade de 3 produtos e lidou com a desistência de 5 itens (para assim sobrar 5 itens finais, garantindo o teste de matemática e exclusão).

### 🛒 1. Itens Inseridos Inicialmente ({len(itens_iniciais_log)} produtos)
""" + "\n".join(itens_iniciais_log) + f"\n\n### 🔄 2. Itens Alterados (Quantidade Modificada)\n" + "\n".join(itens_alterados_log) + f"\n\n### ❌ 3. Itens Retirados (Desistência)\n" + "\n".join(itens_removidos_log) + f"\n\n### ✅ 4. Resumo Final da Compra ({len(carrinho_final)} produtos restantes)\n| Produto | Quant. | Preço Unit. | Subtotal |\n|---------|--------|-------------|----------|\n"
    for item in carrinho_final:
        md += f"| {item['produto_nome']} | {item['quantidade']} | R$ {float(item['preco_unitario']):.2f} | R$ {float(item['subtotal']):.2f} |\n"
    md += f"\n**💰 VALOR TOTAL DA COMPRA: R$ {total_compra:.2f}**\n"

    with open("simulacao_compra_report.md", "w", encoding="utf-8") as f: f.write(md)

if __name__ == "__main__": main()
