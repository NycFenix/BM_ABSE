import sys
import hashlib
from flask import Flask, request, jsonify
from py_ecc.bn128 import G1, multiply, curve_order

app = Flask(__name__)

if len(sys.argv) < 3:
    print("Uso correto: python aa_server.py <Nome_Da_Autoridade> <Porta>")
    sys.exit(1)

AA_NAME = sys.argv[1]
PORT = int(sys.argv[2])


aa_secret = int(hashlib.sha256(AA_NAME.encode()).hexdigest(), 16) % curve_order
print(f"[*] Autoridade de Atributo '{AA_NAME}' inicializada na porta {PORT}...")

@app.route('/keygen', methods=['POST'])
def keygen():
    """Gera chave parcial de atributo vinculada ao GID do Usuário """
    data = request.json
    gid = data.get("gid")
    attributes = data.get("attributes", [])
    
    print(f"[{AA_NAME}] gerando chaves para GID: {gid} com atributos: {attributes}")
    
    # Vincula matematicamente o GID e os Atributos ao segredo da Autoridade
    user_hash = int(hashlib.sha256(f"{gid}".encode()).hexdigest(), 16) % curve_order
    
    key_components = {}
    for attr in attributes:
        attr_hash = int(hashlib.sha256(attr.encode()).hexdigest(), 16) % curve_order
        # Componente da chave: (Secret * User_Hash * Attr_Hash) mod curve_order
        k_comp = (aa_secret * user_hash * attr_hash) % curve_order
        pt_g1 = multiply(G1, k_comp)
        
        key_components[attr] = [str(pt_g1[0]), str(pt_g1[1])]
        
    return jsonify({"authority": AA_NAME, "keys": key_components})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)