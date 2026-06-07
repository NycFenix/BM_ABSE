import sys
import requests
import hashlib
from py_ecc.bn128 import G1, G2, multiply, curve_order
from Crypto.Cipher import AES
from web3 import Web3

if len(sys.argv) < 4:
    print("Uso correto: python data_user.py <Nome_DU> <Index_ID_Blockchain> <Palavra_Busca>")
    sys.exit(1)

DU_NAME = sys.argv[1]
INDEX_ID = int(sys.argv[2])
SEARCH_KEYWORD = sys.argv[3]

LAPTOP_IP = "192.168.1.50"
w3 = Web3(Web3.HTTPProvider(f"http://{LAPTOP_IP}:7545"))

contract_address = "0x0000000000000000000000000000000000000000"
contract_abi = [...]
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Configuração de Atributos e Endereços das 3 Autoridades para a demonstração
AA_ENDPOINTS = {
    "AA_1": "http://192.168.1.50:8001/keygen",
    "AA_2": "http://192.168.1.50:8002/keygen",
    "AA_3": "http://192.168.1.50:8003/keygen"
}

# Matriz de Atributos e Contas da Blockchain exclusivas para cada Usuário da banca
USER_PROFILES = {
    "DU_1": {"gid": "user_joao", "account_idx": 1, "attrs": {"AA_1": ["Admin"], "AA_2": ["Engenheiro"], "AA_3": ["Nivel_3"]}},
    "DU_2": {"gid": "user_maria", "account_idx": 3, "attrs": {"AA_1": ["Leitura"], "AA_2": ["Visitante"], "AA_3": ["Nivel_1"]}},
    "DU_3": {"gid": "user_carlos", "account_idx": 4, "attrs": {"AA_1": ["Admin"], "AA_2": ["Diretor"], "AA_3": ["Nivel_3"]}}
}

if DU_NAME not in USER_PROFILES:
    print(f"Usuário inválido. Escolha entre: DU_1, DU_2 ou DU_3")
    sys.exit(1)

profile = USER_PROFILES[DU_NAME]
w3.eth.default_account = w3.eth.accounts[profile["account_idx"]]

def fetch_keys_from_3_authorities():
    print(f"[{DU_NAME}] Requisitando tokens às 3 Autoridades de Atributos (AA_1, AA_2, AA_3)...")
    user_keys = {}
    
    for aa_name, url in AA_ENDPOINTS.items():
        try:
            payload = {"gid": profile["gid"], "attributes": profile["attrs"].get(aa_name, [])}
            res = requests.post(url, json=payload)
            user_keys[aa_name] = res.json()["keys"]
            print(f" -> Chaves obtidas com sucesso da {aa_name}")
        except Exception as e:
            print(f" [Aviso] Não foi possível conectar à {aa_name}")
    return user_keys

def search_and_decrypt():
    # 1. Faz contato com as autoridades correspondentes
    aa_tokens = fetch_keys_from_3_authorities()
    
    print(f"[{DU_NAME}] Gerando Trapdoor criptográfico para busca...")
    s_trap = int.from_bytes(hashlib.sha256(SEARCH_KEYWORD.encode()).digest(), byteorder='big') % curve_order
    
    T1 = multiply(G2, s_trap)
    T2 = multiply(G1, s_trap)
    
    t1_sol = [int(T1[0].coeffs[0]), int(T1[0].coeffs[1]), int(T1[1].coeffs[0]), int(T1[1].coeffs[1])]
    t2_sol = [int(T2[0]), int(T2[1])]
    
    print(f"[{DU_NAME}] Enviando Trapdoor ao Smart Contract na Blockchain...")
    match_result = contract.functions.searchMatch(INDEX_ID, t1_sol, t2_sol).call()
    
    if match_result:
        file_cid = contract.functions.registry(INDEX_ID).call()[3]
        print(f"[{DU_NAME}] Match validado pela EVM! Resgatando do Servidor de Nuvem...")
        
        res = requests.post(f"http://{LAPTOP_IP}:5000/semi_decrypt", json={"file_id": file_cid})
        cloud_data = res.json()
        
        # Descriptografia local no cliente (Leve)
        ciphertext = bytes.fromhex(cloud_data["ciphertext"])
        tag = bytes.fromhex(cloud_data["tag"])
        nonce = bytes.fromhex(cloud_data["nonce"])
        aes_key = bytes.fromhex(cloud_data["aes_key_masked"])
        
        cipher_dec = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher_dec.decrypt_and_verify(ciphertext, tag)
        print(f"\n[SUCESSO] {DU_NAME} decifrou o dado: {plaintext.decode('utf-8')}\n")
    else:
        print(f"\n[ACESSO NEGADO] Falha na busca. Palavra-chave incorreta ou privilégios de atributos insuficientes para o Índice {INDEX_ID}.\n")

if __name__ == "__main__":
    search_and_decrypt()