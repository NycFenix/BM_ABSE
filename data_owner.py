import sys
import requests
import hashlib
import json
from py_ecc.bn128 import G1, G2, multiply, curve_order
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from web3 import Web3

if len(sys.argv) < 3:
    print("Uso correto: python data_owner.py <Nome_DO> <Palavra_Chave>")
    sys.exit(1)

DO_NAME = sys.argv[1]
KEYWORD = sys.argv[2]

LAPTOP_IP = "192.168.0.112"  # Substitua pelo IP real do seu laptop ou URL do Render/Ngrok
w3 = Web3(Web3.HTTPProvider(f"http://{LAPTOP_IP}:7545"))
cloud_url = f"http://{LAPTOP_IP}:5000/upload"
#cloud_url = "https://bm-abse.onrender.com/"



# contract_address = "0x0000000000000000000000000000000000000000"  # Mude após deploy
# contract_abi = [...]  # Insira a ABI aqui
# contract = w3.eth.contract(address=contract_address, abi=contract_abi)

try:
    with open("contract_config.json", "r") as config_file:
        config = json.load(config_file)
    contract_address = config["contract_address"]
    contract_abi = config["abi"]
    print(f"[*] Contrato carregado automaticamente no endereço: {contract_address}")
except FileNotFoundError:
    print("[ERRO] Arquivo 'contract_config.json' não encontrado. Execute o deploy_contract.py primeiro.")
    sys.exit(1)

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Atribui uma conta do Ganache baseada no número do Data Owner para não colidir chaves na blockchain
if DO_NAME == "DO_1":
    w3.eth.default_account = w3.eth.accounts[0]
else:
    w3.eth.default_account = w3.eth.accounts[2] # DO_2 usa outra conta

def encrypt_and_register():
    print(f"[{DO_NAME}] Iniciando processo de criptografia para o termo: '{KEYWORD}'...")
    
    # Matemática Multi-Autoridade (BM-ABSE)
    r = int.from_bytes(get_random_bytes(32), byteorder='big') % curve_order
    kw_hash = int(hashlib.sha256(KEYWORD.encode()).hexdigest(), 16) % curve_order
    
    W1 = multiply(G1, r)
    W2 = multiply(G2, (r * kw_hash) % curve_order)
    
    # Cifragem simétrica AES-GCM do payload de dados
    dados_sensor = f"Dados criptografados vindos do {DO_NAME}. ID de Segurança Ativo."
    aes_key = get_random_bytes(16)
    cipher = AES.new(aes_key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(dados_sensor.encode('utf-8'))
    
    payload = {
        "ciphertext": ciphertext.hex(),
        "tag": tag.hex(),
        "nonce": cipher.nonce.hex(),
        "aes_key_masked": aes_key.hex()
    }
    
    print(f"[{DO_NAME}] Enviando arquivo cifrado para a Nuvem...")
    response = requests.post(cloud_url, json=payload)
    file_cid = response.json().get("file_id")
    
    # Formatação para o Smart Contract (EVM)
    w1_sol = [int(W1[0]), int(W1[1])]
    w2_sol = [int(W2[0].coeffs[0]), int(W2[0].coeffs[1]), int(W2[1].coeffs[0]), int(W2[1].coeffs[1])]
    
    print(f"[{DO_NAME}] Registrando Índice Criptografado na Blockchain...")
    tx_hash = contract.functions.registerIndex(w1_sol, w2_sol, file_cid).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Retorna o ID do índice gerado para facilitar seu teste no terminal
    index_id = contract.functions.indexCount().call() - 1
    print(f"[{DO_NAME}] Concluído com sucesso! Registrado no Índice ID: {index_id}. Tx: {tx_hash.hex()}\n")

if __name__ == "__main__":
    encrypt_and_register()