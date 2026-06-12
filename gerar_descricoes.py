import asyncio
import re
from openai import AsyncOpenAI
import sys

OPENAI_API_KEY = "SUA_API_KEY_AQUI"
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Corrige encoding de print no terminal Windows
sys.stdout.reconfigure(encoding='utf-8')

async def gerar_descricao(nome_produto):
    """Chama a API da OpenAI para gerar uma descrição comercial com cerca de 50 palavras."""
    retries = 3
    for i in range(retries):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um especialista em e-commerce. Descreva o produto fornecido em aproximadamente 50 palavras de forma atrativa e direta, sem usar formatação excessiva."},
                    {"role": "user", "content": f"Crie uma descrição para o produto: {nome_produto}"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if "Rate limit" in str(e) or "429" in str(e):
                await asyncio.sleep(2 * (i + 1))
            else:
                return None
    return None

async def processar_produto(semaforo, codigo, nome, arquivo_saida):
    """Processa um único produto e escreve o comando UPDATE no arquivo SQL."""
    async with semaforo:
        # Pausa para não estourar o limite de 500 RPM da OpenAI
        await asyncio.sleep(0.2)
        
        descricao = await gerar_descricao(nome)
        if descricao:
            descricao_escapada = descricao.replace("'", "''")
            sql_update = f"UPDATE produtos SET descricao = '{descricao_escapada}' WHERE codigo_barras = '{codigo}';\n"
            
            with open(arquivo_saida, "a", encoding="utf-8") as f:
                f.write(sql_update)
            print(f"Gerado OK para codigo: {codigo}")
        else:
            print(f"Falha ao gerar para codigo: {codigo}")

async def main():
    arquivo_entrada = "popular_produtos.sql"
    arquivo_saida = "update_descricoes.sql"
    
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write("BEGIN;\n\n")

    print(f"Lendo os produtos do arquivo {arquivo_entrada}...")
    with open(arquivo_entrada, "r", encoding="utf-8") as f:
        conteudo = f.read()
        
    padrao = re.compile(r"INSERT INTO produtos \(codigo_barras, nome, preco_venda, estoque\) VALUES \('([^']+)', '([^']+)'")
    produtos = padrao.findall(conteudo)
    
    print(f"Encontrados {len(produtos)} produtos. Iniciando com limite de taxa (RPM)...")
    
    # Reduzindo concorrência para 5 para evitar rate limit
    semaforo = asyncio.Semaphore(5) 
    tarefas = [processar_produto(semaforo, cod, nome, arquivo_saida) for cod, nome in produtos]
    
    await asyncio.gather(*tarefas)
    
    with open(arquivo_saida, "a", encoding="utf-8") as f:
        f.write("\nCOMMIT;\n")
        
    print(f"\nProcesso concluído com sucesso! Arquivo {arquivo_saida} foi gerado.")

if __name__ == "__main__":
    asyncio.run(main())
