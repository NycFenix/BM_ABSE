import sys
import json
import requests
import hashlib
import time  
import matplotlib.pyplot as plt  
import numpy as np
from py_ecc.bn128 import G1, G2, multiply, curve_order
from Crypto.Cipher import AES
from web3 import Web3

if len(sys.argv) < 4:
    print("Uso correto: python data_user.py <Nome_DU> <Index_ID> <Palavra_Busca>")
    sys.exit(1)

DU_NAME = sys.argv[1]
INDEX_ID = int(sys.argv[2])
SEARCH_KEYWORD = sys.argv[3]

LAPTOP_IP = "192.268.0.112" # IP do laptop
w3 = Web3(Web3.HTTPProvider(f"http://{LAPTOP_IP}:7545"))

try:
    with open("contract_config.json", "r") as f:
        config = json.load(f)
    contract = w3.eth.contract(address=config["contract_address"], abi=config["abi"])
except FileNotFoundError:
    print("[ERRO] Execute o deploy_contract.py primeiro.")
    sys.exit(1)

contract = w3.eth.contract(address=contract_address, abi=contract_abi)


AA_ENDPOINTS = {
    "AA_1": f"http://{LAPTOP_IP}:8001/keygen",
    "AA_2": f"http://{LAPTOP_IP}:8002/keygen"
}

USER_PROFILES = {
    "DU_1": {"gid": "joao_mestre", "acc": 1},
    "DU_2": {"gid": "maria_tech", "acc": 3},
    "DU_3": {"gid": "carlos_analista", "acc": 4}
}

profile = USER_PROFILES[DU_NAME]
w3.eth.default_account = w3.eth.accounts[profile["acc"]]

def executar_teste_benchmark(num_attrs):
    print(f"\n[Benchmark] Iniciando teste para {num_attrs} atributos...")
    
    # Segredo temporário s do Data User para a Trapdoor
    s_trap = int.from_bytes(hashlib.sha256(SEARCH_KEYWORD.encode()).digest(), byteorder='big') % curve_order
    kw_hash_user = int(hashlib.sha256(SEARCH_KEYWORD.encode()).hexdigest(), 16) % curve_order
    
    # --- CORREÇÃO DA EQUAÇÃO DE PAREAMENTO DA EVM ---
    # Inversão geométrica exata para validar a equação bilinear do precompile 0x08:
    # e(T2, W2) == e(W1, T1)
    T1 = multiply(G1, s_trap) # T1 no grupo G1
    T2 = multiply(G2, (s_trap * kw_hash_user) % curve_order) # T2 no grupo G2 com amarração da palavra-chave
    
    # Formatação adequada para o mapeamento de memória do Solidity
    t1_sol = [int(T2[0].coeffs[0]), int(T2[0].coeffs[1]), int(T2[1].coeffs[0]), int(T2[1].coeffs[1])]
    t2_sol = [int(T1[0]), int(T1[1])]
    # -----------------------------------------------
    
    # Executa a chamada local na Blockchain
    match_result = contract.functions.searchMatch(INDEX_ID, t1_sol, t2_sol).call()
    
    if match_result:
        file_cid = contract.functions.registry(INDEX_ID).call()[3]
        
        # Métrica de Tempo (Gráfico 1)
        inicio_nuvem = time.perf_counter() 
        
        res = requests.post(f"http://{LAPTOP_IP}:5000/semi_decrypt", json={
            "file_id": file_cid,
            "num_atributos": num_attrs 
        })
        cloud_data = res.json()
        
        fim_nuvem = time.perf_counter() 
        tempo_nuvem_ms = (fim_nuvem - inicio_nuvem) * 1000 
        
        tamanho_payload_bytes = len(json.dumps(cloud_data))
        
        inicio_iot = time.perf_counter()
        
        ciphertext = bytes.fromhex(cloud_data["ciphertext"])
        tag = bytes.fromhex(cloud_data["tag"])
        nonce = bytes.fromhex(cloud_data["nonce"])
        aes_key = bytes.fromhex(cloud_data["aes_key_masked"])
        
        cipher_dec = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher_dec.decrypt_and_verify(ciphertext, tag)
        
        fim_iot = time.perf_counter()
        tempo_iot_ms = (fim_iot - inicio_iot) * 1000
        
        tamanho_original_bytes = len(plaintext)
        
        print(f" -> [SUCESSO] EVM Match Confirmado!")
        print(f" -> Nuvem: {tempo_nuvem_ms:.2f} ms | IoT: {tempo_iot_ms:.2f} ms")
        
        return tempo_nuvem_ms, tempo_iot_ms, tamanho_payload_bytes, tamanho_original_bytes
    else:
        print(" -> [ERRO] Falha na busca. Matemática Rejeitada pela EVM.")
        return None, None, None, None

if __name__ == "__main__":
    casos_atributos = [2, 4, 6, 8]
    historico_nuvem = []
    historico_iot = []
    historico_payload = []
    historico_original = []
    
    print("="*60)
    print(f" AMBIENTE DE BENCHMARK REPARADO - {DU_NAME}")
    print("="*60)
    
    for qtd in casos_atributos:
        t_nuvem, t_iot, size_payload, size_orig = executar_teste_benchmark(qtd)
        if t_nuvem is not None:
            historico_nuvem.append(t_nuvem)
            historico_iot.append(t_iot)
            historico_payload.append(size_payload)
            historico_original.append(size_orig)
            
    if len(historico_nuvem) == len(casos_atributos):
        print("\n[Benchmark] Plotando Gráficos Combinados...")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
        
        # Gráfico 1
        ax1.plot(casos_atributos, historico_nuvem, color='#1f77b4', marker='o', linewidth=2, label='SemiDecrypt (Nuvem / Laptop)')
        ax1.plot(casos_atributos, historico_iot, color='#d62728', marker='s', linewidth=2, label='DataDecrypt (IoT / Raspberry Pi 3)')
        ax1.set_title('Gráfico 1: Tempo de Computação Versus Atributos', fontsize=10, fontweight='bold', pad=10)
        ax1.set_xlabel('Quantidade de Atributos')
        ax1.set_ylabel('Tempo (ms)')
        ax1.set_xticks(casos_atributos)
        ax1.grid(True, linestyle='--', alpha=0.5)
        ax1.legend()
        
        # Gráfico 2
        x_indices = np.arange(len(casos_atributos))
        width = 0.35
        ax2.bar(x_indices - width/2, historico_original, width, label='Dado Puro', color='#7f7f7f', alpha=0.7)
        ax2.bar(x_indices + width/2, historico_payload, width, label='Payload com Sobrecarga', color='#2ca02c', alpha=0.8)
        ax2.set_title('Gráfico 2: Tamanho de Pacote na Rede (Bytes)', fontsize=10, fontweight='bold', pad=10)
        ax2.set_xlabel('Quantidade de Atributos')
        ax2.set_ylabel('Bytes')
        ax2.set_xticks(x_indices)
        ax2.set_xticklabels(casos_atributos)
        ax2.grid(True, axis='y', linestyle='--', alpha=0.5)
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('painel_demonstracao.png', dpi=300)
        plt.show()