import sys
import json
import requests
import hashlib
from py_ecc.bn128 import G1, G2, multiply, curve_order
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from web3 import Web3

if len(sys.argv) < 3:
    print("Uso correto: python data_owner.py <Nome_DO> <Palavra_Chave>")
    sys.exit(1)

DO_NAME = sys.argv[1]
KEYWORD = sys.argv[2]

LAPTOP_IP = "192.168.0.112" # ID do laptop
w3 = Web3(Web3.HTTPProvider(f"http://{LAPTOP_IP}:7545"))
cloud_url = f"http://{LAPTOP_IP}:5000/upload"

try:
    with open("contract_config.json", "r") as f:
        config = json.load(f)
    contract = w3.eth.contract(address=config["contract_address"], abi=config["abi"])
except FileNotFoundError:
    print("[ERRO] Reexecute o deploy_contract.py primeiro.")
    sys.exit(1)

w3.eth.default_account = w3.eth.accounts[0] if DO_NAME == "DO_1" else w3.eth.accounts[2]

def run():
    print(f"[{DO_NAME}] Computando índices criptográficos estáveis para '{KEYWORD}'...")
    
    # Gerando o segredo r do Data Owner
    r = int.from_bytes(get_random_bytes(32), byteorder='big') % curve_order
    kw_hash = int(hashlib.sha256(KEYWORD.encode()).hexdigest(), 16) % curve_order
    
    # Alinhamento Matemático Estrito para a EVM (Precompile 0x08)
    # W1 pertence a G1, W2 pertence a G2
    W1 = multiply(G1, r)
    W2 = multiply(G2, (r * kw_hash) % curve_order)
    
    dados = f"Telemetria Industrial - {DO_NAME}: Operação Segura."
    aes_key = get_random_bytes(16)
    cipher = AES.new(aes_key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(dados.encode('utf-8'))
    
    payload = {
        "ciphertext": ciphertext.hex(),
        "tag": tag.hex(),
        "nonce": cipher.nonce.hex(),
        "aes_key_masked": aes_key.hex()
    }
    
    res = requests.post(cloud_url, json=payload)
    file_cid = res.json().get("file_id")
    
    w1_sol = [int(W1[0]), int(W1[1])]
    w2_sol = [int(W2[0].coeffs[0]), int(W2[0].coeffs[1]), int(W2[1].coeffs[0]), int(W2[1].coeffs[1])]
    
    tx_hash = contract.functions.registerIndex(w1_sol, w2_sol, file_cid).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    idx_count = contract.functions.indexCount().call() - 1
    print(f"[{DO_NAME}] Gravado com Sucesso no ID de Busca: {idx_count}\n")

if __name__ == "__main__":
    run()