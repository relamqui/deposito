import re
import ast

def clean_response(resp_str):
    if not resp_str or resp_str == '`': return ""
    try:
        # Tenta avaliar o string que parece um dict
        resp_str = resp_str.strip('` ')
        if resp_str.endswith('...'):
            resp_str = resp_str[:-3]
            if resp_str.endswith("'" or '"'):
                 resp_str = resp_str[:-1]
        
        # Limpeza simples
        resp_str = resp_str.replace("{'result': {'content': [{'type': 'text', 'text': '", "")
        if "Error:" in resp_str:
             match = re.search(r'(Error: [^\'\"]+)', resp_str)
             if match: return f"Falha: {match.group(1)}"
        if resp_str.startswith("[{"):
             return f"Sucesso (ID Retornado)"
        if resp_str == "[]":
             return "Sucesso (Vazio)"
        return resp_str[:60] + "..."
    except:
        return resp_str[:50]

with open("stress_test_500_report.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
in_log = False
current_module = ""

for line in lines:
    if line.startswith("## 📜 Log Detalhado"):
        new_lines.append(line)
        new_lines.append("\n*Abaixo estão as requisições agrupadas por módulo de forma limpa:*\n\n")
        in_log = True
        continue
    
    if in_log:
        if line.startswith("| `"):
            parts = line.split(" | ")
            if len(parts) >= 4:
                mod = parts[0].replace("| ", "").replace("`", "").strip()
                params = parts[1].replace("`", "").strip()
                status = parts[2].strip()
                resp = parts[3].strip()
                
                if mod != current_module:
                    if current_module != "":
                        new_lines.append("\n</details>\n\n")
                    current_module = mod
                    new_lines.append(f"<details>\n<summary><b>🔍 Mostrar Requisições do Módulo: {mod}</b></summary>\n\n")
                    new_lines.append("| Status | Parâmetros | Resposta Simplificada |\n")
                    new_lines.append("|--------|------------|-----------------------|\n")
                
                clean_r = clean_response(resp)
                new_lines.append(f"| {status} | `{params}` | `{clean_r}` |\n")
        elif not line.startswith("|") and line.strip() != "":
            # ignore headers of old table
            pass
    else:
        new_lines.append(line)

if in_log and current_module != "":
    new_lines.append("\n</details>\n")

with open("stress_test_500_report.md", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
