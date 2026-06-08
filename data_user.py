import sys
import json
import requests
import hashlib
import time  # --- LINHA ADICIONADA PARA CRONOMETRAGEM ---
import matplotlib.pyplot as plt  # --- LINHA ADICIONADA PARA GERAR O GRÁFICO ---
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

LAPTOP_IP = "192.168.0.112"
w3 = Web3(Web3.HTTPProvider(f"http://{LAPTOP_IP}:7545"))

# try:
#     with open("contract_config.json", "r") as f:
#         config = json.load(f)
#     contract = w3.eth.contract(address=config["contract_address"], abi=config["abi"])
# except FileNotFoundError:
#     print("[ERRO] Executar o deploy_contract.py no laptop primeiro.")
#     sys.exit(1)

try:
    # Faz uma requisição GET para a Nuvem buscar o endereço e a ABI atualizados do Ganache
    res_config = requests.get(f"http://{LAPTOP_IP}:5000/contract_config")
    config = res_config.json()
    contract_address = config["contract_address"]
    contract_abi = config["abi"]
    print(f"[*] Contrato sincronizado via Nuvem no endereço: {contract_address}")
except Exception as e:
    print(f"[ERRO] Nao foi possivel sincronizar o contrato com a Nuvem: {e}")
    sys.exit(1)

contract = w3.eth.contract(address=contract_address, abi=contract_abi)


AA_ENDPOINTS = {
    "AA_1": f"http://{LAPTOP_IP}:8001/keygen",
    "AA_2": f"http://{LAPTOP_IP}:8002/keygen"
}

USER_PROFILES = {
    "DU_1": {"gid": "joao_mestre", "acc": 1, "attrs": {"AA_1": ["Supervisor"], "AA_2": ["TI"]}},
    "DU_2": {"gid": "maria_tech", "acc": 3, "attrs": {"AA_1": ["Operador"], "AA_2": ["Visitas"]}},
    "DU_3": {"gid": "carlos_analista", "acc": 4, "attrs": {"AA_1": ["Supervisor"], "AA_2": ["Diretor"]}}
}

if DU_NAME not in USER_PROFILES:
    sys.exit(1)

profile = USER_PROFILES[DU_NAME]
#w3.eth.default_account = w3.eth.accounts[profile["acc"]]
w3.eth.default_account = w3.eth.accounts[profile["acc"]]

# --- FUNÇÃO MODIFICADA PARA RECEBER O NÚMERO DE ATRIBUTOS E RETORNAR OS TEMPOS DE EXECUÇÃO ---
def executar_teste_benchmark(num_attrs):
    print(f"\n[Benchmark] Iniciando teste para {num_attrs} atributos...")
    
    # 1. Simulação do TrapGen e Chamada do Smart Contract
    s_trap = int.from_bytes(hashlib.sha256(SEARCH_KEYWORD.encode()).digest(), byteorder='big') % curve_order
    T1 = multiply(G2, s_trap)
    T2 = multiply(G1, s_trap)
    t1_sol = [int(T1[0].coeffs[0]), int(T1[0].coeffs[1]), int(T1[1].coeffs[0]), int(T1[1].coeffs[1])]
    t2_sol = [int(T2[0]), int(T2[1])]
    
    match_result = contract.functions.searchMatch(INDEX_ID, t1_sol, t2_sol).call()
    
    if match_result:
        file_cid = contract.functions.registry(INDEX_ID).call()[3]
        
        # 2. Medição do tempo do SemiDecrypt (Nuvem)
        inicio_nuvem = time.perf_counter() # Captura tempo inicial
        
        # Passa a quantidade de atributos no payload para que a nuvem processe proporcionalmente
        res = requests.post(f"http://{LAPTOP_IP}:5000/semi_decrypt", json={
            "file_id": file_cid,
            "num_atributos": num_attrs 
        })
        cloud_data = res.json()
        
        fim_nuvem = time.perf_counter() # Captura tempo final
        tempo_nuvem_ms = (fim_nuvem - inicio_nuvem) * 1000 # Converte para milissegundos
        
        # Pega tamanho do payload serializado pra nuvem
        payload_byte_size = len(json.dumps(cloud_data))


        # 3. Medição do tempo do DataDecrypt 
        inicio_iot = time.perf_counter()
        
        ciphertext = bytes.fromhex(cloud_data["ciphertext"])
        tag = bytes.fromhex(cloud_data["tag"])
        nonce = bytes.fromhex(cloud_data["nonce"])
        aes_key = bytes.fromhex(cloud_data["aes_key_masked"])
        
        cipher_dec = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher_dec.decrypt_and_verify(ciphertext, tag) # Decifra o conteúdo e verifica a integridade
        
        fim_iot = time.perf_counter() # Captura tempo final do DataDecrypt
        tempo_iot_ms = (fim_iot - inicio_iot) * 1000
        
        # Pega o tamanho do payload puro
        original_byte_size = len(plaintext)

        print(f" -> Nuvem gasta: {tempo_nuvem_ms:.2f} ms | IoT gasta: {tempo_iot_ms:.2f} ms")
        return tempo_nuvem_ms, tempo_iot_ms, payload_byte_size, original_byte_size
    else:
        print(" -> Falha na busca. Abortando benchmark.")
        return None, None, None, None

# --- BLOCO PRINCIPAL TOTALMENTE ALTERADO PARA COLETAR E PLOTAR OS CASOS 2, 4, 6 e 8 ---
if __name__ == "__main__":
    casos_atributos = [2, 4, 6, 8]
    historico_nuvem = []
    historico_iot = []
    historico_payload = []
    historico_original = []

    print("="*60)
    print(f" INICIANDO AMBIENTE DE BENCHMARK Duplo - {DU_NAME}")
    print("="*60)
    
    # Executa a coleta sequencial para cada caso exigido
    for qtd in casos_atributos:
        t_nuvem, t_iot, size_payload, size_original = executar_teste_benchmark(qtd)
        if t_nuvem is not None:
            historico_nuvem.append(t_nuvem)
            historico_iot.append(t_iot)
            historico_payload.append(size_payload)
            historico_original.append(size_original)

            
    # Se todas as coletas foram executadas com sucesso, monta o gráfico na tela
    if len(historico_nuvem) == len(casos_atributos):
        print("\n[Benchmark] Gerando gráfico de desempenho...")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize = (13, 5))

        # Gráfico 1: Tempo do SemiDecrypt (Nuvem) vs. DataDecrypt (Raspberry Pi) em função do número de atributos
        ax1.plot(casos_atributos, historico_nuvem, color='#1f77b4', marker='o', linewidth=2, label='SemiDecrypt (Nuvem / Laptop)')
        ax1.plot(casos_atributos, historico_iot, color='#d62728', marker='s', linewidth=2, label='DataDecrypt (IoT / Raspberry Pi 3)')
        ax1.set_title('Gráfico 1: Impacto do Número de Atributos no Tempo', fontsize=10, fontweight='bold', pad=10)
        ax1.set_xlabel('Quantidade de Atributos Analisados')
        ax1.set_ylabel('Tempo de Computação (ms)')
        ax1.set_xticks(casos_atributos)
        ax1.grid(True, linestyle='--', alpha=0.5)
        ax1.legend(frameon=True, facecolor='#fafafa')

        # Gráfico 2: Sobrecarga de Comunicação (Tamanho do Payload) em função do número de atributos
        x_indices = np.arange(len(casos_atributos))
        width = 0.35
        
        ax2.bar(x_indices - width/2, historico_original, width, label='Dado Original (Texto Limpo)', color='#7f7f7f', alpha=0.7)
        ax2.bar(x_indices + width/2, historico_payload, width, label='Texto Cifrado + Metadados (Rede)', color='#2ca02c', alpha=0.8)
        
        ax2.set_title('Gráfico 2: Sobrecarga de Comunicação (Rede)', fontsize=10, fontweight='bold', pad=10)
        ax2.set_xlabel('Quantidade de Atributos Analisados')
        ax2.set_ylabel('Tamanho do Pacote de Dados (Bytes)')
        ax2.set_xticks(x_indices)
        ax2.set_xticklabels(casos_atributos)
        ax2.grid(True, axis='y', linestyle='--', alpha=0.5)
        ax2.legend(frameon=True, facecolor='#fafafa')

        plt.tight_layout()
       
        # Salva o gráfico gerado na pasta atual e abre a janela visual automaticamente
        plt.savefig('resultado_benchmark_real.png', dpi=300)
        print("[SUCESSO] Imagem salva como 'resultado_benchmark_real.png'.")
        plt.show()