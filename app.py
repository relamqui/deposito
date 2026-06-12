from fastapi import FastAPI
from rapidfuzz import process, fuzz
from pydantic import BaseModel
from db import get_produtos
import unidecode

app = FastAPI()

class BuscarRequest(BaseModel):
    query: str

def limpar_texto(texto: str) -> str:
    """Remove acentos, pontos e transforma em minúsculas"""
    if not texto: return ""
    return unidecode.unidecode(texto).lower().strip()

@app.get("/")
def home():
    return {"status": "API rotando com AI Search 🚀"}

@app.post("/buscar")
def buscar_produto(request: BuscarRequest):
    query = limpar_texto(request.query)
    
    if not query:
        return {"query_recebida": request.query, "resultados_ia": []}

    produtos = get_produtos()
    
    # Criamos uma lista com os nomes já "limpos" (sem acentos) para bater com a pesquisa
    nomes_para_pesquisa = [limpar_texto(p["nome"]) for p in produtos]

    # fuzzy search - Usando token_set_ratio ideal para palavras omitidas
    resultados = process.extract(
        query,
        nomes_para_pesquisa,
        scorer=fuzz.token_set_ratio,
        limit=5
    )

    resposta = []
    for _nome_limpo, score, index in resultados:
        # Ponto de corte para evitar falsos positivos do IA
        if score > 40:
            produto_original = produtos[index]
            resposta.append({
                "id": produto_original["id"],
                "nome_original": produto_original["nome"],
                "score": score
            })

    # Restaura a ordem dos de maior score
    resposta = sorted(resposta, key=lambda x: x["score"], reverse=True)

    return {
        "query_recebida": request.query,
        "resultados_ia": resposta
    }