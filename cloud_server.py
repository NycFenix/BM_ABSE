from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)
storage = {}

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    file_id = str(uuid.uuid4())
    storage[file_id] = data
    return jsonify({"status": "success", "file_id": file_id}), 200

@app.route('/semi_decrypt', methods=['POST'])
def semi_decrypt():
    req_data = request.json
    file_id = req_data["file_id"]
    
    file_data = storage.get(file_id)
    if not file_data:
        return jsonify({"error": "Arquivo não encontrado"}), 404
        
    print(f"[Cloud] Executando terceirização de cálculo para o arquivo {file_id}...")
    # O artigo implementa o SemiDecrypt para aliviar o processamento do IoT Receptor
    return jsonify(file_data), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)