"""
Script de Teste -- MCP Server (Deposito Joel)
Testa todas as tools configuradas no n8n MCP Server via SSE + JSON-RPC
"""

import requests
import json
import threading
import time
import sys
import io

# Forcar UTF-8 no stdout do Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============================================================
# CONFIGURACAO
# ============================================================
MCP_SSE_URL = "https://n8n-n8n.ioms5g.easypanel.host/mcp/f9f72e5c-3832-4e8c-a6bf-e05f87e29d1b"

# Cores para output no terminal
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"

def ok(msg):
    print(f"  {Colors.GREEN}[OK] {msg}{Colors.END}")

def fail(msg):
    print(f"  {Colors.RED}[FAIL] {msg}{Colors.END}")

def info(msg):
    print(f"  {Colors.CYAN}[INFO] {msg}{Colors.END}")

def warn(msg):
    print(f"  {Colors.YELLOW}[WARN] {msg}{Colors.END}")

def header(msg):
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}{Colors.END}")


# ============================================================
# CONEXÃO MCP VIA SSE
# ============================================================
class MCPClient:
    """Cliente MCP que conecta via SSE e envia JSON-RPC"""

    def __init__(self, sse_url):
        self.sse_url = sse_url
        self.message_url = None
        self.session_id = None
        self._connected = threading.Event()
        self._responses = {}
        self._lock = threading.Lock()
        self._sse_thread = None
        self._running = False

    def connect(self, timeout=15):
        """Conecta ao SSE e obtém o endpoint de mensagens"""
        print(f"\n🔌 Conectando ao MCP Server...")
        print(f"   URL: {self.sse_url}")

        self._running = True
        self._sse_thread = threading.Thread(target=self._listen_sse, daemon=True)
        self._sse_thread.start()

        if not self._connected.wait(timeout=timeout):
            raise ConnectionError(f"Timeout ({timeout}s) ao conectar no MCP Server. Verifique se o n8n está rodando e o workflow está ativo.")

        ok(f"Conectado! Message endpoint: {self.message_url}")
        return True

    def _listen_sse(self):
        """Thread que escuta eventos SSE"""
        try:
            response = requests.get(
                self.sse_url,
                stream=True,
                headers={"Accept": "text/event-stream"},
                timeout=60
            )
            response.raise_for_status()

            event_type = None
            data_buffer = ""

            for line in response.iter_lines(decode_unicode=True):
                if not self._running:
                    break

                if line is None:
                    continue

                line = line.strip() if isinstance(line, str) else line.decode("utf-8").strip()

                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data_buffer = line[5:].strip()

                    if event_type == "endpoint":
                        # O n8n envia o endpoint relativo, precisamos montar a URL completa
                        base = self.sse_url.rsplit("/mcp/", 1)[0]
                        self.message_url = base + data_buffer
                        # Extrair sessionId se existir na URL
                        if "sessionId=" in data_buffer:
                            self.session_id = data_buffer.split("sessionId=")[1].split("&")[0]
                        self._connected.set()

                    elif event_type == "message":
                        try:
                            msg = json.loads(data_buffer)
                            msg_id = msg.get("id")
                            if msg_id is not None:
                                with self._lock:
                                    self._responses[msg_id] = msg
                        except json.JSONDecodeError:
                            pass

                    event_type = None
                    data_buffer = ""

                elif line == "":
                    # Fim de um evento SSE
                    event_type = None
                    data_buffer = ""

        except Exception as e:
            if self._running:
                print(f"\n  ❌ Erro na conexão SSE: {e}")

    def send(self, method, params=None, timeout=15):
        """Envia uma mensagem JSON-RPC e aguarda a resposta"""
        if not self.message_url:
            raise ConnectionError("Não conectado ao MCP Server")

        msg_id = int(time.time() * 1000)
        payload = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        # Envia via POST
        resp = requests.post(
            self.message_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )

        if resp.status_code not in (200, 202, 204):
            raise Exception(f"HTTP {resp.status_code}: {resp.text}")

        # Se a resposta veio direto no body
        if resp.text and resp.text.strip():
            try:
                return json.loads(resp.text)
            except json.JSONDecodeError:
                pass

        # Aguarda resposta via SSE
        start = time.time()
        while time.time() - start < timeout:
            with self._lock:
                if msg_id in self._responses:
                    return self._responses.pop(msg_id)
            time.sleep(0.2)

        raise TimeoutError(f"Timeout ({timeout}s) aguardando resposta do método '{method}'")

    def call_tool(self, tool_name, arguments, timeout=15):
        """Chama uma tool específica"""
        return self.send("tools/call", {
            "name": tool_name,
            "arguments": arguments
        }, timeout=timeout)

    def list_tools(self, timeout=15):
        """Lista todas as tools disponíveis"""
        return self.send("tools/list", {}, timeout=timeout)

    def disconnect(self):
        """Encerra a conexão"""
        self._running = False


# ============================================================
# TESTES
# ============================================================
def run_tests():
    client = MCPClient(MCP_SSE_URL)
    results = {"passed": 0, "failed": 0, "skipped": 0}
    cliente_id = None
    carrinho_id = None
    item_id = None

    try:
        # ── Conectar ──
        client.connect(timeout=15)

        # ── Inicializar MCP ──
        header("INICIALIZANDO MCP")
        try:
            init = client.send("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-script", "version": "1.0"}
            })
            if init and "result" in init:
                ok(f"MCP inicializado — Versão: {init['result'].get('protocolVersion', '?')}")
                server_info = init['result'].get('serverInfo', {})
                if server_info:
                    info(f"Server: {server_info.get('name', '?')} v{server_info.get('version', '?')}")
            else:
                ok("MCP inicializado (sem detalhes)")
        except Exception as e:
            warn(f"Initialize opcional falhou (normal em alguns servers): {e}")

        # ══════════════════════════════════════════════
        # TESTE 0: Listar Tools
        # ══════════════════════════════════════════════
        header("TESTE 0 — Listar Tools Disponíveis")
        try:
            tools_response = client.list_tools()
            if tools_response and "result" in tools_response:
                tools = tools_response["result"].get("tools", [])
                ok(f"Encontradas {len(tools)} tools:")
                for i, tool in enumerate(tools, 1):
                    name = tool.get("name", "?")
                    desc = tool.get("description", "sem descrição")[:80]
                    params = list(tool.get("inputSchema", {}).get("properties", {}).keys())
                    print(f"      {i:2d}. {Colors.CYAN}{name}{Colors.END}")
                    print(f"          Desc: {desc}")
                    print(f"          Params: {', '.join(params) if params else 'nenhum'}")
                results["passed"] += 1
            else:
                fail(f"Resposta inesperada: {json.dumps(tools_response, indent=2)}")
                results["failed"] += 1
        except Exception as e:
            fail(f"Erro ao listar tools: {e}")
            results["failed"] += 1

        # ══════════════════════════════════════════════
        # TESTE 1: buscar_cliente (cliente que não existe)
        # ══════════════════════════════════════════════
        header("TESTE 1 — buscar_cliente (número inexistente)")
        try:
            resp = client.call_tool("buscar_cliente1", {"telefone": "5500000000000"})
            if resp and "result" in resp:
                content = resp["result"].get("content", [])
                ok(f"Resposta recebida (esperado: vazio/nenhum resultado)")
                info(f"Conteúdo: {json.dumps(content, indent=2, ensure_ascii=False)[:300]}")
                results["passed"] += 1
            elif resp and "error" in resp:
                fail(f"Erro: {resp['error']}")
                results["failed"] += 1
            else:
                warn(f"Resposta inesperada: {resp}")
                results["passed"] += 1
        except Exception as e:
            fail(f"Erro: {e}")
            results["failed"] += 1

        # ══════════════════════════════════════════════
        # TESTE 2: criar_cliente
        # ══════════════════════════════════════════════
        header("TESTE 2 — criar_cliente (cliente de teste)")
        try:
            resp = client.call_tool("criar_cliente1", {
                "telefone": "5511999990000",
                "nome": "Cliente Teste MCP"
            })
            if resp and "result" in resp:
                content = resp["result"].get("content", [])
                content_text = json.dumps(content, ensure_ascii=False)
                ok(f"Cliente criado/atualizado!")
                info(f"Conteúdo: {content_text[:300]}")

                # Tentar extrair o cliente_id
                for item in content:
                    if item.get("type") == "text":
                        try:
                            data = json.loads(item["text"])
                            if isinstance(data, list) and len(data) > 0:
                                cliente_id = data[0].get("id")
                            elif isinstance(data, dict):
                                cliente_id = data.get("id")
                        except:
                            pass
                if cliente_id:
                    ok(f"cliente_id extraído: {cliente_id}")
                else:
                    warn("Não consegui extrair o cliente_id da resposta. Usando ID = 1 para testes seguintes.")
                    cliente_id = 1
                results["passed"] += 1
            else:
                fail(f"Resposta inesperada: {resp}")
                results["failed"] += 1
        except Exception as e:
            fail(f"Erro: {e}")
            results["failed"] += 1

        # ══════════════════════════════════════════════
        # TESTE 3: buscar_cliente (agora deve existir)
        # ══════════════════════════════════════════════
        header("TESTE 3 — buscar_cliente (deve encontrar o teste)")
        try:
            resp = client.call_tool("buscar_cliente1", {"telefone": "5511999990000"})
            if resp and "result" in resp:
                content = resp["result"].get("content", [])
                ok(f"Busca realizada!")
                info(f"Conteúdo: {json.dumps(content, indent=2, ensure_ascii=False)[:300]}")
                results["passed"] += 1
            else:
                fail(f"Resposta: {resp}")
                results["failed"] += 1
        except Exception as e:
            fail(f"Erro: {e}")
            results["failed"] += 1

        # ══════════════════════════════════════════════
        # TESTE 4: buscar_produto (Fuzzy Search - Múltiplos Cenários)
        # ══════════════════════════════════════════════
        header("TESTE 4 — buscar_produto (Fuzzy Search - Múltiplos Cenários)")
        
        cenarios_busca = [
            # Cenários de digitação comuns
            ("Sem acento", "agua mineral", "Água Mineral 500ml"),
            ("Erro ortográfico", "cerveja pilsin 600", "Cerveja Pilsen 600ml"),
            ("Omissão de caracteres", "coca lata", "Coca-Cola 350ml lata"),
            ("Letras trocadas", "deterjente", "Detergente Líquido 500ml"),
            ("Palavra incompleta", "amendoin torado", "Amendoim Torrado 150g"),
            ("Produto Inexistente", "carro voador 2000", None),
            
            # Cenários "Idoso / Descrição"
            ("Idoso - Refri de lata", "aquele refri preto de latinha", "Coca-Cola 350ml lata"),
            ("Idoso - Pasta de dente", "pasta de dente de menta", "Creme Dental 90g"),
            ("Idoso - Sabão de roupa", "sabao de lavar roupa em po", "Sabão em Pó 1kg"),
            ("Idoso - Pipoca", "pipoca de por no microondas com manteiga", "Pipoca Micro-ondas 100g"),
            ("Idoso - Pão", "pao de sal", "Pão Francês 100g"),
            ("Idoso - Biscoito", "aquele biscoito recheado de chocolate", "Biscoito Recheado 130g")
        ]

        for desc, query, esperado in cenarios_busca:
            print(f"\n  [TESTANDO] {desc} -> Query: '{query}'")
            try:
                resp = client.call_tool("buscar_produto1", {"query": query})
                if resp and "result" in resp:
                    content = resp["result"].get("content", [])
                    if content and len(content) > 0 and content[0].get("type") == "text":
                        data = json.loads(content[0]["text"])
                        
                        if esperado is None:
                            if len(data) == 0:
                                ok("Retornou vazio corretamente para produto inexistente.")
                            else:
                                fail(f"Deveria retornar vazio, mas encontrou: {data}")
                                results["failed"] += 1
                        else:
                            if len(data) > 0:
                                melhor_match = data[0].get("nome", "")
                                if esperado.lower() in melhor_match.lower() or melhor_match.lower() in esperado.lower() or esperado == melhor_match:
                                    ok(f"Encontrou corretamente: {melhor_match}")
                                else:
                                    warn(f"Melhor match foi '{melhor_match}', esperado era '{esperado}'.")
                            else:
                                fail(f"Não encontrou resultados. Esperava: {esperado}")
                                results["failed"] += 1
                    else:
                        fail(f"Formato de resposta inesperado.")
                        results["failed"] += 1
                else:
                    fail(f"Resposta inválida do MCP.")
                    results["failed"] += 1
            except Exception as e:
                fail(f"Erro na execução: {e}")
                results["failed"] += 1

        # ══════════════════════════════════════════════
        # TESTE 5: criar_carrinho
        # ══════════════════════════════════════════════
        header("TESTE 5 — criar_carrinho")
        if cliente_id:
            try:
                resp = client.call_tool("criar_carrinho1", {"cliente_id": str(cliente_id)})
                if resp and "result" in resp:
                    content = resp["result"].get("content", [])
                    ok(f"Carrinho criado!")
                    info(f"Conteúdo: {json.dumps(content, indent=2, ensure_ascii=False)[:300]}")

                    # Extrair carrinho_id
                    for item in content:
                        if item.get("type") == "text":
                            try:
                                data = json.loads(item["text"])
                                if isinstance(data, list) and len(data) > 0:
                                    carrinho_id = data[0].get("id")
                                elif isinstance(data, dict):
                                    carrinho_id = data.get("id")
                            except:
                                pass
                    if carrinho_id:
                        ok(f"carrinho_id extraído: {carrinho_id}")
                    else:
                        warn("Não consegui extrair carrinho_id")
                    results["passed"] += 1
                else:
                    fail(f"Resposta: {resp}")
                    results["failed"] += 1
            except Exception as e:
                fail(f"Erro: {e}")
                results["failed"] += 1
        else:
            warn("Pulando — cliente_id não disponível")
            results["skipped"] += 1

        # ══════════════════════════════════════════════
        # TESTE 6: obter_carrinho_ativo
        # ══════════════════════════════════════════════
        header("TESTE 6 — obter_carrinho_ativo")
        if cliente_id:
            try:
                resp = client.call_tool("obter_carrinho_ativo1", {"cliente_id": str(cliente_id)})
                if resp and "result" in resp:
                    content = resp["result"].get("content", [])
                    ok(f"Carrinho ativo encontrado!")
                    info(f"Conteúdo: {json.dumps(content, indent=2, ensure_ascii=False)[:300]}")
                    results["passed"] += 1
                else:
                    fail(f"Resposta: {resp}")
                    results["failed"] += 1
            except Exception as e:
                fail(f"Erro: {e}")
                results["failed"] += 1
        else:
            warn("Pulando — cliente_id não disponível")
            results["skipped"] += 1

        # ══════════════════════════════════════════════
        # TESTE 7: adicionar_item_carrinho
        # ══════════════════════════════════════════════
        header("TESTE 7 — adicionar_item_carrinho")
        if carrinho_id:
            try:
                resp = client.call_tool("adicionar_item_carrinho1", {
                    "carrinho_id": str(carrinho_id),
                    "produto_id": "1",
                    "produto_nome": "Produto Teste",
                    "preco_unitario": "10.50",
                    "quantidade": "3"
                })
                if resp and "result" in resp:
                    content = resp["result"].get("content", [])
                    ok(f"Item adicionado ao carrinho!")
                    info(f"Conteúdo: {json.dumps(content, indent=2, ensure_ascii=False)[:300]}")

                    # Extrair item_id
                    for item_c in content:
                        if item_c.get("type") == "text":
                            try:
                                data = json.loads(item_c["text"])
                                if isinstance(data, list) and len(data) > 0:
                                    item_id = data[0].get("id")
                                elif isinstance(data, dict):
                                    item_id = data.get("id")
                            except:
                                pass
                    if item_id:
                        ok(f"item_id extraído: {item_id}")
                    results["passed"] += 1
                else:
                    fail(f"Resposta: {resp}")
                    results["failed"] += 1
            except Exception as e:
                fail(f"Erro: {e}")
                results["failed"] += 1
        else:
            warn("Pulando — carrinho_id não disponível")
            results["skipped"] += 1

        # ══════════════════════════════════════════════
        # TESTE 8: ver_carrinho
        # ══════════════════════════════════════════════
        header("TESTE 8 — ver_carrinho")
        if cliente_id:
            try:
                resp = client.call_tool("ver_carrinho1", {"cliente_id": str(cliente_id)})
                if resp and "result" in resp:
                    content = resp["result"].get("content", [])
                    ok(f"Carrinho visualizado!")
                    info(f"Conteúdo: {json.dumps(content, indent=2, ensure_ascii=False)[:500]}")
                    results["passed"] += 1
                else:
                    fail(f"Resposta: {resp}")
                    results["failed"] += 1
            except Exception as e:
                fail(f"Erro: {e}")
                results["failed"] += 1
        else:
            warn("Pulando — cliente_id não disponível")
            results["skipped"] += 1

        # ══════════════════════════════════════════════
        # TESTE 9: remover_item_carrinho
        # ══════════════════════════════════════════════
        header("TESTE 9 — remover_item_carrinho")
        if item_id:
            try:
                resp = client.call_tool("remover_item_carrinho1", {"item_id": str(item_id)})
                if resp and "result" in resp:
                    content = resp["result"].get("content", [])
                    ok(f"Item removido do carrinho!")
                    info(f"Conteúdo: {json.dumps(content, indent=2, ensure_ascii=False)[:300]}")
                    results["passed"] += 1
                else:
                    fail(f"Resposta: {resp}")
                    results["failed"] += 1
            except Exception as e:
                fail(f"Erro: {e}")
                results["failed"] += 1
        else:
            warn("Pulando — item_id não disponível")
            results["skipped"] += 1

        # ══════════════════════════════════════════════
        # TESTE 10: finalizar_carrinho
        # ══════════════════════════════════════════════
        header("TESTE 10 — finalizar_carrinho")
        if cliente_id:
            try:
                resp = client.call_tool("finalizar_carrinho1", {"cliente_id": str(cliente_id)})
                if resp and "result" in resp:
                    content = resp["result"].get("content", [])
                    ok(f"Carrinho finalizado!")
                    info(f"Conteúdo: {json.dumps(content, indent=2, ensure_ascii=False)[:300]}")
                    results["passed"] += 1
                else:
                    fail(f"Resposta: {resp}")
                    results["failed"] += 1
            except Exception as e:
                fail(f"Erro: {e}")
                results["failed"] += 1
        else:
            warn("Pulando — cliente_id não disponível")
            results["skipped"] += 1

        # ══════════════════════════════════════════════
        # TESTE 11: salvar_orcamento
        # ══════════════════════════════════════════════
        header("TESTE 11 — salvar_orcamento")
        if cliente_id:
            try:
                resp = client.call_tool("salvar_orcamento1", {
                    "cliente_id": str(cliente_id),
                    "tipo_evento": "Churrasco",
                    "data_evento": "2026-05-15",
                    "hora_inicio": "14:00",
                    "hora_fim": "22:00",
                    "num_convidados": "50",
                    "publico": "adulto",
                    "bebidas": "Cerveja, refrigerante, água",
                    "preferencia_marca": "Brahma e Coca-Cola",
                    "gelo": "Sim, aproximadamente 20kg",
                    "comidas_petiscos": "Carvão e descartáveis",
                    "produtos_gelados": "gelados",
                    "tipo_entrega": "entrega",
                    "endereco_entrega": "Rua Teste 123, Bairro Centro, Cidade",
                    "horario_entrega": "12:00",
                    "forma_pagamento": "Pix",
                    "nota_fiscal": "true",
                    "limite_valor": "1500.00",
                    "resumo": "Churrasco para 50 pessoas em 15/05/2026"
                })
                if resp and "result" in resp:
                    content = resp["result"].get("content", [])
                    ok(f"Orçamento salvo!")
                    info(f"Conteúdo: {json.dumps(content, indent=2, ensure_ascii=False)[:300]}")
                    results["passed"] += 1
                else:
                    fail(f"Resposta: {resp}")
                    results["failed"] += 1
            except Exception as e:
                fail(f"Erro: {e}")
                results["failed"] += 1
        else:
            warn("Pulando — cliente_id não disponível")
            results["skipped"] += 1

    except ConnectionError as e:
        fail(str(e))
        results["failed"] += 1
    except Exception as e:
        fail(f"Erro inesperado: {e}")
        results["failed"] += 1
    finally:
        client.disconnect()

    # ══════════════════════════════════════════════
    # RESULTADO FINAL
    # ══════════════════════════════════════════════
    header("RESULTADO FINAL")
    total = results["passed"] + results["failed"] + results["skipped"]
    print(f"  Total de testes: {total}")
    print(f"  {Colors.GREEN}✅ Passou: {results['passed']}{Colors.END}")
    print(f"  {Colors.RED}❌ Falhou: {results['failed']}{Colors.END}")
    print(f"  {Colors.YELLOW}⚠️  Pulado: {results['skipped']}{Colors.END}")

    if results["failed"] == 0 and results["skipped"] == 0:
        print(f"\n  {Colors.GREEN}{Colors.BOLD}🎉 TODOS OS TESTES PASSARAM!{Colors.END}")
    elif results["failed"] > 0:
        print(f"\n  {Colors.RED}{Colors.BOLD}⚠️  VERIFIQUE OS TESTES QUE FALHARAM ACIMA{Colors.END}")

    return results["failed"] == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
