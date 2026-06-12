"""
Script de Geração de Relatório — Teste de Stress MCP (Busca Fuzzy)
Executa 150 cenários de busca focados em erros humanos, coloquialismos e ambiguidades.
"""

import requests
import requests
import json
import time
import sys
import io

MCP_URL = "https://n8n-n8n.ioms5g.easypanel.host/mcp/f9f72e5c-3832-4e8c-a6bf-e05f87e29d1b"

# Importa o client do script anterior para reaproveitar a conexão SSE
try:
    from test_mcp_tools import MCPClient
except ImportError:
    print("Erro: Precisa do test_mcp_tools.py na mesma pasta.")
    sys.exit(1)

# 150 Cenários Variados Mapeados aos Produtos Reais
CENARIOS = [
    # Categoria: Água / Refrigerantes / Energético
    ("Sem acento e letra errada", "agua menaral", "Água Mineral 500ml"),
    ("Abreviação coloquial", "uma coca", "Coca-Cola 350ml lata"),
    ("Omissão grande", "coca cola", "Coca-Cola 350ml lata"),
    ("Descrição coloquial", "refri de lata preto", "Coca-Cola 350ml lata"),
    ("Falta espaço", "cocacola", "Coca-Cola 350ml lata"),
    ("Palavra incompleta", "suco de laran", "Suco de Laranja 1L"),
    ("Sem acento", "suco de laranja integral", "Suco de Laranja 1L"),
    ("Descrição de embalagem", "cerveja long neck", "Cerveja Pilsen 600ml"),
    ("Foco no sabor/tipo", "pilsen retornavel", "Cerveja Pilsen 600ml"),
    ("Erro de gramática", "cerveja pilsim", "Cerveja Pilsen 600ml"),
    ("Gíria", "uma breja 600", "Cerveja Pilsen 600ml"),
    ("Nome parcial", "energetico lata", "Energético 250ml"),
    ("Troca de letras", "inergetico", "Energético 250ml"),
    ("Gíria/Sinônimo", "redbull (teste erro intencional que pega categoria)", "Energético 250ml"),

    # Categoria: Laticínios
    ("Falta de espaço/acento", "leite uht", "Leite Integral 1L"),
    ("Palavra invertida", "integral leite", "Leite Integral 1L"),
    ("Erro comum", "cafe soluvel", "Café Solúvel 100g"),
    ("Descrição do café", "cafe em pote", "Café Solúvel 100g"),
    ("Erro de plural", "queijos mussarelas", "Queijo Mussarela 200g"),
    ("Erro ortográfico", "mussarela fatiada", "Queijo Mussarela 200g"),
    ("Erro grave", "musarela", "Queijo Mussarela 200g"),
    ("Fonética errada", "iogurti", "Iogurte Natural 170g"),
    ("Busca por embalagem", "iogurte pote", "Iogurte Natural 170g"),
    ("Erro digitação", "manteiga com sal", "Manteiga 200g"),
    ("Gíria idoso", "margarina tablete", "Manteiga 200g"),
    ("Erro ortográfico", "requeijao", "Requeijão Cremoso 200g"),
    ("Descrição do requeijão", "requeijao de copinho", "Requeijão Cremoso 200g"),
    ("Abreviação", "creme de leite", "Creme de Leite 200ml"),
    ("Descrição de embalagem", "creme caixinha", "Creme de Leite 200ml"),

    # Categoria: Padaria / Biscoitos
    ("Busca genérica", "pao de forma", "Pão de Forma 500g"),
    ("Erro digitação", "pao forma tradissional", "Pão de Forma 500g"),
    ("Coloquial", "bolacha recheada", "Biscoito Recheado 130g"),
    ("Foco no sabor", "biscoito de chocolate", "Biscoito Recheado 130g"),
    ("Coloquial", "bolacha de agua e sal", "Biscoito Salgado 200g"),
    ("Nome da embalagem", "cream cracker", "Biscoito Salgado 200g"),
    ("Erro ortográfico", "crem craquer", "Biscoito Salgado 200g"),
    ("Gíria/Coloquial", "pao de sal", "Pão Francês 100g"),
    ("Gíria/Coloquial", "paozinho", "Pão Francês 100g"),
    ("Gíria/Coloquial", "cacetinho", "Pão Francês 100g"),
    ("Sabor do bolo", "bolo de cenora", "Bolo de Cenoura 400g"),
    ("Falta de acento", "fatia de bolo", "Bolo de Cenoura 400g"),

    # Categoria: Limpeza
    ("Falta de acento", "detergente neutro", "Detergente Líquido 500ml"),
    ("Coloquial", "deterjente de louca", "Detergente Líquido 500ml"),
    ("Falta de acento", "agua sanitaria", "Água Sanitária 1L"),
    ("Coloquial/Marca", "candida", "Água Sanitária 1L"),
    ("Coloquial/Marca", "quiboa", "Água Sanitária 1L"),
    ("Falta de acento", "papel higienico", "Papel Higiênico 4un"),
    ("Descrição embalagem", "papel folha dupla", "Papel Higiênico 4un"),
    ("Erro ortográfico", "esponja de aso", "Esponja de Aço 8un"),
    ("Marca/Gíria", "bombril", "Esponja de Aço 8un"),
    ("Falta acento", "sabao em po", "Sabão em Pó 1kg"),
    ("Gíria idoso", "sabao de lavar roupa", "Sabão em Pó 1kg"),
    ("Marca genérica", "omo", "Sabão em Pó 1kg"),

    # Categoria: Higiene Pessoal
    ("Fonética errada", "saboneti", "Sabonete 90g"),
    ("Descrição uso", "sabonete de banho", "Sabonete 90g"),
    ("Abreviação", "shampo", "Shampoo 200ml"),
    ("Coloquial", "xampu", "Shampoo 200ml"),
    ("Falta acento/Coloquial", "pasta de dente", "Creme Dental 90g"),
    ("Descrição sabor", "pasta de menta", "Creme Dental 90g"),
    ("Gíria/Marca", "colgate", "Creme Dental 90g"),
    ("Falta acento", "escova de dente", "Escova de Dentes"),
    ("Descrição uso", "escova macia", "Escova de Dentes"),
    ("Falta de espaço", "desodoranterollon", "Desodorante Roll-on 50ml"),
    ("Descrição", "desodorante antitranspirante", "Desodorante Roll-on 50ml"),
    ("Descrição", "absorvente interno", "Absorvente 8un"),

    # Categoria: Mercearia Básica
    ("Erro digitação", "aroz", "Arroz Branco 1kg"),
    ("Descrição do produto", "arroz agulhinha", "Arroz Branco 1kg"),
    ("Falta acento", "feijao", "Feijão Carioca 1kg"),
    ("Descrição sabor", "feijao carioca", "Feijão Carioca 1kg"),
    ("Erro ortográfico", "macarrao espageti", "Macarrão Espaguete 500g"),
    ("Descrição numero", "espaguete n8", "Macarrão Espaguete 500g"),
    ("Abreviação", "oleo", "Óleo de Soja 900ml"),
    ("Falta acento", "oleo de soja", "Óleo de Soja 900ml"),
    ("Falta acento", "acucar", "Açúcar Cristal 1kg"),
    ("Falta acento", "assucar", "Açúcar Cristal 1kg"),
    ("Descrição fina", "acucar refinado", "Açúcar Cristal 1kg"),
    ("Busca genérica", "sal", "Sal Refinado 1kg"),
    ("Descrição do sal", "sal iodado", "Sal Refinado 1kg"),
    ("Abreviação", "molho de tomate", "Molho de Tomate 340g"),
    ("Marca/Gíria", "pomarola", "Molho de Tomate 340g"),
    ("Coloquial", "extrato de tomate", "Molho de Tomate 340g"),
    ("Abreviação", "vinagre branco", "Vinagre 750ml"),
    ("Descrição completa", "vinagre de alcool", "Vinagre 750ml"),
    ("Erro ortográfico", "azeite extra virjen", "Azeite Extra Virgem 200ml"),

    # Categoria: Frios e Congelados
    ("Erro ortográfico", "presunto", "Presunto Fatiado 200g"),
    ("Descrição formato", "presunto fatiado", "Presunto Fatiado 200g"),
    ("Abreviação", "mortadela", "Mortadela 200g"),
    ("Descrição sabor", "mortadela com azeitona", "Mortadela 200g"),
    ("Falta espaço", "sorvetenapolitano", "Sorvete Napolitano 1,5L"),
    ("Busca por sabores", "sorvete de morango e chocolate", "Sorvete Napolitano 1,5L"),
    ("Erro ortográfico", "linguica toscana", "Linguiça Toscana 500g"),
    ("Descrição estado", "linguica congelada", "Linguiça Toscana 500g"),
    ("Erro digitação", "frango intero", "Frango Inteiro 1kg"),
    ("Falta acento", "pizza", "Pizza Mussarela 450g"),
    ("Descrição sabor da pizza", "pizza de queijo", "Pizza Mussarela 450g"),
    ("Marca/Gíria pizza", "pizza congelada", "Pizza Mussarela 450g"),

    # Categoria: Snacks e Doces
    ("Coloquial", "salgadinho", "Salgadinho 50g"),
    ("Marca/Gíria", "cheetos", "Salgadinho 50g"),
    ("Marca/Gíria", "fandangos", "Salgadinho 50g"),
    ("Erro digitação", "amendoin", "Amendoim Torrado 150g"),
    ("Descrição sabor", "amendoim salgado", "Amendoim Torrado 150g"),
    ("Falta de espaço", "barradechocolate", "Barra de Chocolate 80g"),
    ("Descrição do chocolate", "chocolate ao leite", "Barra de Chocolate 80g"),
    ("Descrição", "pipoca de manteiga", "Pipoca Micro-ondas 100g"),
    ("Erro digitação", "pirulituh", "Pirulito 12g"),
    ("Descrição sabor pirulito", "pirulito de fruta", "Pirulito 12g"),
    ("Gíria", "chiclete de menta", "Chiclete 8un"),
    ("Gíria", "trident", "Chiclete 8un"),
    ("Falta espaço/acento", "baladegoma", "Bala de Goma 100g"),
    ("Gíria", "jujuba", "Bala de Goma 100g"),

    # Casos Mistos e Testes Negativos
    ("Completamente Inexistente 1", "pneu de carro", None),
    ("Completamente Inexistente 2", "celular iphone", None),
    ("Completamente Inexistente 3", "computador gamer", None),
    ("Busca com números absurdos", "água mineral 500000ml", "Água Mineral 500ml"),
    ("Busca com pontuação errada", "coca.cola.lata", "Coca-Cola 350ml lata"),
    ("Apenas símbolos", "@#$%", None),
    ("Busca muito curta", "a", None),
]

# Vamos duplicar alguns com pequenas variações para chegar a quase 150 testes
variacoes_extras = [
    ("Agua menaral 500ml", "Água Mineral 500ml"), ("sukito", None), ("sukinho de laranja", "Suco de Laranja 1L"),
    ("cerveja de garrafa", "Cerveja Pilsen 600ml"), ("energético 500ml", "Energético 250ml"),
    ("leití", "Leite Integral 1L"), ("cafézinho", "Café Solúvel 100g"),
    ("queijo", "Queijo Mussarela 200g"), ("danone", "Iogurte Natural 170g"),
    ("mantega", "Manteiga 200g"), ("requeijam", "Requeijão Cremoso 200g"),
    ("creme de lete", "Creme de Leite 200ml"), ("pao d forma", "Pão de Forma 500g"),
    ("trakinas", "Biscoito Recheado 130g"), ("bolacha salgada", "Biscoito Salgado 200g"),
    ("pãozinho francês", "Pão Francês 100g"), ("bolo caseiro", "Bolo de Cenoura 400g"),
    ("detergente de maca", "Detergente Líquido 500ml"), ("candida de litro", "Água Sanitária 1L"),
    ("papel", "Papel Higiênico 4un"), ("lã de aço", "Esponja de Aço 8un"),
    ("sabao po", "Sabão em Pó 1kg"), ("sabonet", "Sabonete 90g"),
    ("shampô", "Shampoo 200ml"), ("pasta de dente branca", "Creme Dental 90g"),
    ("escovinha", "Escova de Dentes"), ("desodorante", "Desodorante Roll-on 50ml"),
    ("modess", "Absorvente 8un"), ("arroz agulha", "Arroz Branco 1kg"),
    ("feijao preto", "Feijão Carioca 1kg"), ("macarrao numero 8", "Macarrão Espaguete 500g"),
    ("olho de soja", "Óleo de Soja 900ml"), ("açucar", "Açúcar Cristal 1kg"),
    ("sal grosso", "Sal Refinado 1kg"), ("polpa de tomate", "Molho de Tomate 340g"),
    ("vinagre de maca", "Vinagre 750ml"), ("azeite", "Azeite Extra Virgem 200ml"),
    ("presunto sem capa", "Presunto Fatiado 200g"), ("mortandela", "Mortadela 200g"),
    ("pote de sorvete", "Sorvete Napolitano 1,5L"), ("linguiça de churrasco", "Linguiça Toscana 500g"),
    ("frango cru", "Frango Inteiro 1kg"), ("pizza para assar", "Pizza Mussarela 450g"),
    ("doritos", "Salgadinho 50g"), ("amendoim descascado", "Amendoim Torrado 150g"),
    ("chocolatinho", "Barra de Chocolate 80g"), ("pipoca Yoki", "Pipoca Micro-ondas 100g"),
    ("pirulito psicodelico", "Pirulito 12g"), ("chicle", "Chiclete 8un"),
    ("bala fini", "Bala de Goma 100g")
]

for q, esp in variacoes_extras:
    CENARIOS.append(("Variação Extra", q, esp))


def run_fuzzy_report():
    print(f"Iniciando {len(CENARIOS)} testes de Fuzzy Search no MCP Server...\n")
    client = MCPClient(MCP_URL)
    
    sucesso = 0
    falha = 0
    relatorio = []
    
    try:
        client.connect(timeout=15)
        
        for i, (categoria, query, esperado) in enumerate(CENARIOS, 1):
            if i % 10 == 0:
                print(f"Executando teste {i}/{len(CENARIOS)}...")
                
            status = "❌ FAIL"
            match = ""
            
            try:
                resp = client.call_tool("buscar_produto1", {"query": query}, timeout=10)
                if resp and "result" in resp:
                    content = resp["result"].get("content", [])
                    if content and len(content) > 0 and content[0].get("type") == "text":
                        data = json.loads(content[0]["text"])
                        if esperado is None:
                            if len(data) == 0:
                                status = "✅ PASS"
                                sucesso += 1
                                match = "(vazio)"
                            else:
                                match = data[0].get("nome", "???")
                                falha += 1
                        else:
                            if len(data) > 0:
                                melhor_match = data[0].get("nome", "")
                                match = melhor_match
                                # Aceita matches parciais desde que o produto certo seja retornado em primeiro
                                if esperado.lower() in melhor_match.lower() or melhor_match.lower() in esperado.lower():
                                    status = "✅ PASS"
                                    sucesso += 1
                                else:
                                    # Fallback: Se o ID ou a Categoria baterem (não temos ID aqui, mas o texto bate muito)
                                    # Para o script ser justo, o esperado deve ser o nome real retornado
                                    if esperado == melhor_match:
                                        status = "✅ PASS"
                                        sucesso += 1
                                    else:
                                        falha += 1
                            else:
                                match = "(não encontrou)"
                                falha += 1
            except Exception as e:
                match = f"(ERRO: {e})"
                falha += 1
                
            relatorio.append(f"| {i} | {query} | {esperado if esperado else 'Nenhum'} | {match} | {status} |")
            
    except Exception as e:
        print(f"Erro Crítico de Conexão: {e}")
    finally:
        client.disconnect()

    # Gera arquivo Markdown de Relatório
    md_content = f"""# Relatório de Stress Test — Agente de Busca Fuzzy
**Total de Testes:** {len(CENARIOS)}
**Sucessos:** {sucesso} ({sucesso/len(CENARIOS)*100:.1f}%)
**Falhas (Falso Negativo/Positivo):** {falha} ({falha/len(CENARIOS)*100:.1f}%)

Este teste valida a assertividade do PostgreSQL com a extensão `pg_trgm` procurando em `nome` E `descricao`.

| # | Digitado (Query) | Produto Esperado | Melhor Match (Banco) | Status |
|---|-------------------|-------------------|-----------------------|--------|
"""
    md_content += "\n".join(relatorio)
    
    with open("fuzzy_report.md", "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"\nRelatório gerado em 'fuzzy_report.md'. Sucesso: {sucesso}/{len(CENARIOS)}")

if __name__ == "__main__":
    run_fuzzy_report()
