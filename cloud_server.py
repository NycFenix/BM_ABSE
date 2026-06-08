import uuid
import json
from flask import Flask, request, jsonify
from py_ecc.bn128 import G1, G2, pairing, multiply
import time
import csv
import json
app = Flask(__name__)
storage = {}

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    file_id = str(uuid.uuid4())

    
    storage[file_id] = data
    return jsonify({"status": "success", "file_id": file_id}), 200

@app.route('/contract_config', methods=['GET'])
def get_contract_config():
    try:
        with open("contract_config.json", "r") as f:
            config = json.load(f)
        return jsonify(config), 200
    except FileNotFoundError:
        return jsonify({"error": "Configuracao nao encontrada no servidor"}), 404

@app.route('/semi_decrypt', methods=['POST'])
def semi_decrypt():
    req_data = request.json
    file_id = req_data["file_id"]
    
    # --- LINHAS ADICIONADAS PARA COLETA DO GRÁFICO 1 ---
    # Recebe a quantidade de atributos sendo testada para calcular os pareamentos reais proporcionais
    num_atributos = req_data.get("num_atributos", 2) 
    # --------------------------------------------------

    file_data = storage.get(file_id)
    if not file_data:
        return jsonify({"error": "Arquivo nao encontrado"}), 404
        
    print(f"[Nuvem - SemiDecrypt] Processando {num_atributos} atributos para aliviar o IoT...")
    
    # --- LINHAS ALTERADAS PARA O CÁLCULO REAL MULTI-ATRIBUTO ---
    # O artigo executa múltiplos pareamentos bilineares dependendo do número de atributos.
    # Usamos um laço para executar a função pairing() da py_ecc de forma proporcional ao teste.
    dummy_user_g1 = multiply(G1, 7)
    dummy_attr_g2 = multiply(G2, 11)
    
    tct_factor = pairing(dummy_attr_g2, dummy_user_g1)
    for _ in range(num_atributos - 1):
        # Multiplica o resultado do pareamento simulando o produtório de chaves do artigo
        tct_factor = tct_factor * pairing(dummy_attr_g2, dummy_user_g1)
    # -----------------------------------------------------------
    
    response_payload = {
        "ciphertext": file_data["ciphertext"],
        "tag": file_data["tag"],
        "nonce": file_data["nonce"],
        "aes_key_masked": file_data["aes_key_masked"],
        "tct_real": str(tct_factor.real),
        "tct_imag": str(tct_factor.imag)
    }
    return jsonify(response_payload), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)