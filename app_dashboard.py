import os
from flask import Flask, jsonify, request, render_template
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Configuração do Banco de Dados
# Coloque aqui a sua URL de conexão do PostgreSQL
# Exemplo: postgres://usuario:senha@localhost:5432/deposito_joel
DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

def get_db_connection():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pedidos')
def get_pedidos():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Busca carrinhos abertos e finalizados
    query = """
        SELECT c.id as carrinho_id, c.status, cl.nome as cliente_nome, cl.telefone, 
               c.criado_em as carrinho_criado_em,
               ci.id as item_id, ci.produto_nome, ci.quantidade, ci.preco_unitario
        FROM "CARRINHOS" c
        JOIN "CLIENTES" cl ON c.cliente_id = cl.id
        LEFT JOIN "CARRINHO_ITENS" ci ON ci.carrinho_id = c.id
        WHERE c.status IN ('aberto', 'finalizado', 'em_preparacao')
        ORDER BY c.atualizado_em DESC, ci.criado_em ASC;
    """
    cur.execute(query)
    rows = cur.fetchall()
    
    # Agrupar por carrinho
    pedidos_dict = {}
    for row in rows:
        cid = row['carrinho_id']
        if cid not in pedidos_dict:
            pedidos_dict[cid] = {
                "id": cid,
                "status": row['status'],
                "cliente": row['cliente_nome'] or "Cliente Sem Nome",
                "telefone": row['telefone'],
                "hora": row['carrinho_criado_em'].strftime("%H:%M") if row['carrinho_criado_em'] else "",
                "itens": [],
                "total": 0.0
            }
        
        if row['item_id']:
            subtotal = float(row['quantidade']) * float(row['preco_unitario'])
            pedidos_dict[cid]["total"] += subtotal
            pedidos_dict[cid]["itens"].append({
                "nome": row['produto_nome'],
                "quantidade": row['quantidade'],
                "preco": float(row['preco_unitario']),
                "subtotal": subtotal
            })
            
    cur.close()
    conn.close()

    # Separar em duas listas para o Kanban
    abertos = []
    preparacao = []
    
    for p in pedidos_dict.values():
        if p['status'] == 'aberto':
            abertos.append(p)
        elif p['status'] in ('finalizado', 'em_preparacao'):
            preparacao.append(p)

    return jsonify({"abertos": abertos, "preparacao": preparacao})

@app.route('/api/pedidos/<int:carrinho_id>/concluir', methods=['POST'])
def concluir_pedido(carrinho_id):
    conn = get_db_connection()
    cur = conn.cursor()
    # Muda o status para entregue, assim ele some do Kanban
    cur.execute('UPDATE "CARRINHOS" SET status = %s WHERE id = %s', ('entregue', carrinho_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    print("Iniciando Painel do Depósito Joel na porta 5000...")
    print("Por favor, verifique a variável de conexão do banco (DB_URL) no código fonte.")
    app.run(debug=True, port=5000, host='0.0.0.0')
