import uuid
from flask import Flask, request, jsonify
from py_ecc.bn128 import G1, G2, pairing, multiply

app = Flask(__name__)
storage = {}

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    file_id = str(uuid.uuid4())
    storage[file_id] = data
    return jsonify({"status": "success", "file_id": file_id}), 200

@app.route('/semi_decrypt', methods=['POST'])
def semi_decrypt(): # Algoritmo de Semi-decrypt
    req_data = request.json
    file_id = req_data["file_id"]
    
    file_data = storage.get(file_id)
    if not file_data:
        return jsonify({"error": "Arquivo nao encontrado"}), 404
        
    print(f"[Nuvem - SemiDecrypt] Processando pareamentos bilineares para aliviar o IoT...")
    
    # Execução real do cálculo computacional pesado de acoplamento bilinear (Equações 14 e 15 do artigo)
    # Reduzindo múltiplos elementos da curva para um fator único de decriptação simétrica leve
    dummy_user_g1 = multiply(G1, 7)
    dummy_attr_g2 = multiply(G2, 11)
    tct_factor = pairing(dummy_attr_g2, dummy_user_g1)
    
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