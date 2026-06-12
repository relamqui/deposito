import psycopg2
import psycopg2.extras
from time import time
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (caso você rode localmente)
# No EasyPanel, ele vai ignorar o .env e usar as "Environment Variables" cadastradas lá
load_dotenv()

DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "postgres"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "sua_senha_aqui"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432")
}

# Variáveis para armazenar o cache e deixar a API intantânea
_CACHE_PRODUTOS = []
_CACHE_TIMESTAMP = 0
# Busca o tempo de cache do ENV, por padrão é 300 segundos (5 min)
CACHE_TTL = int(os.environ.get("CACHE_TTL_SECONDS", 300))

def fetch_produtos_from_db():
    """Busca os produtos diretamente do PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Ajuste a query abaixo para puxar as colunas corretas da sua tabela
        cursor.execute("SELECT id, nome FROM produtos")
        produtos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return produtos
    except Exception as e:
        print(f"Erro ao acessar BD PostgreSQL: {e}")
        return []

def get_produtos():
    """Retorna os produtos utilizando cache na memória (Ultra rápido)"""
    global _CACHE_PRODUTOS, _CACHE_TIMESTAMP
    
    agora = time()
    if not _CACHE_PRODUTOS or (agora - _CACHE_TIMESTAMP) > CACHE_TTL:
        print("Atualizando cache de produtos do banco de dados...")
        novos_produtos = fetch_produtos_from_db()
        if novos_produtos:
            _CACHE_PRODUTOS = novos_produtos
            _CACHE_TIMESTAMP = agora

    return _CACHE_PRODUTOS
