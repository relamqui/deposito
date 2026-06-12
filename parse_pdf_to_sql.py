import fitz
import re

pdf_path = "RELATORIODEPRODUTOS.pdf"
sql_path = "popular_produtos.sql"

doc = fitz.open(pdf_path)
full_text = ""
for page in doc:
    full_text += page.get_text() + "\n"

# Clean up headers
full_text = re.sub(r'RELATÓRIO DE ESTOQUE.*?\n', '', full_text)
full_text = re.sub(r'CÓDIGO NOME VALOR ESTOQUE\n', '', full_text)
full_text = re.sub(r'V6\.1\.0 LST PÁGINA \d+ DE \d+\n?', '', full_text)

# The pattern looks for:
# # followed by digits
# Any characters (non-greedy) for the name
# R$ followed by price
# space and then stock number
pattern = re.compile(r'#(\d+)\s+([\s\S]+?)\s+R\$(\d+,\d+)\s+(-?\d+(?:\.\d+)?)')

matches = pattern.findall(full_text)

sql_statements = ["BEGIN;"]
for match in matches:
    code = match[0]
    name = match[1].strip().replace('\n', ' ').replace("'", "''")
    # Condense multiple spaces into one
    name = re.sub(r'\s+', ' ', name)
    price = match[2].replace(',', '.')
    stock = match[3].replace('.', '') # handle thousands separator if any
    
    sql = f"INSERT INTO produtos (codigo_barras, nome, preco_venda, estoque) VALUES ('{code}', '{name}', {price}, {stock});"
    sql_statements.append(sql)

sql_statements.append("COMMIT;\n")

with open(sql_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(sql_statements))

print(f"Generated {len(matches)} insert statements in {sql_path}")
