import sys
import hashlib
import time  # --- LINHA ADICIONADA PARA CRONOMETRAGEM ---
from flask import Flask, request, jsonify
from py_ecc.bn128 import G1, multiply, curve_order

app = Flask(__name__)

if len(sys.argv) < 3:
    print("Uso correto: python aa_server.py <Nome_AA> <Porta>")
    sys.exit(1)

AA_NAME = sys.argv[1]
PORT = int(sys.argv[2])

aa_secret = int(hashlib.sha256(AA_NAME.encode()).hexdigest(), 16) % curve_order
print(f"[*] Autoridade '{AA_NAME}' ativa na porta {PORT}...")

@app.route('/keygen', methods=['POST'])
def keygen():
    data = request.json
    gid = data.get("gid")
    attributes = data.get("attributes", [])
    
    print(f"[{AA_NAME}] Requisicao KeyGen para {len(attributes)} atributos...")
    
    # --- LINHAS ADICIONADAS PARA MEDIÇÃO DO GRÁFICO 3 ---
    inicio_keygen = time.perf_counter()  # Marca o início do processamento matemático pesado
    # ----------------------------------------------------
    
    user_hash = int(hashlib.sha256(f"{gid}".encode()).hexdigest(), 16) % curve_order
    
    key_components = {}
    for attr in attributes:
        attr_hash = int(hashlib.sha256(attr.encode()).hexdigest(), 16) % curve_order
        k_comp = (aa_secret * user_hash * attr_hash) % curve_order
        
        # Execução da operação pesada na curva elíptica G1 (Gargalo do artigo)
        pt_g1 = multiply(G1, k_comp)
        key_components[attr] = [str(pt_g1[0]), str(pt_g1[1])]
        
    # --- LINHAS ADICIONADAS PARA MEDIÇÃO DO GRÁFICO 3 ---
    fim_keygen = time.perf_counter()
    tempo_gasto_ms = (fim_keygen - inicio_keygen) * 1000  # Tempo real de processamento em ms
    # ----------------------------------------------------
        
    # Retorna os componentes criptográficos junto com a métrica de desempenho do servidor
    return jsonify({
        "authority": AA_NAME, 
        "keys": key_components,
        "tempo_keygen_ms": tempo_gasto_ms  # --- ENVIANDO O DADO COLETADO ---
    })

# --- CODIGO ALTERADO PARA SUPORTAR MULTIPLAS REQUISICOES LOCAIS ---
if __name__ == "__main__":
    # O parametro threaded=True impede que o servidor congele se receber chamadas em lote no mesmo Laptop
    app.run(host='0.0.0.0', port=PORT, threaded=True)