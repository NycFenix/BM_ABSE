import json
from web3 import Web3
from solcx import compile_standard, install_solc

# 1. Configuração de Conexão com o Ganache Local
GANACHE_URL = "http://192.168.0.112:7545"
# IP local do seu Ganache no Laptop
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# Define a conta que vai pagar as taxas de Gas do Deploy (Conta 0 do Ganache)
w3.eth.default_account = w3.eth.accounts[0]

def deploy():
    print("[Blockchain] Instalando e configurando o compilador Solidity v0.8.0...")
    # Garante que a versão correta do Solidity está instalada no ambiente
    install_solc("0.8.0")

    print("[Blockchain] Lendo o arquivo SearchMatch.sol...")
    with open("SearchMatch.sol", "r") as file:
        contract_source_code = file.read()

    print("[Blockchain] Compilando o Smart Contract...")
    # Compilação padrão do código fonte do Solidity
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"SearchMatch.sol": {"content": contract_source_code}},
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            },
        },
        solc_version="0.8.0",
    )

    # Extrai o Bytecode e a ABI gerados na compilação
    bytecode = compiled_sol["contracts"]["SearchMatch.sol"]["SearchMatch"]["evm"]["bytecode"]["object"]
    abi = compiled_sol["contracts"]["SearchMatch.sol"]["SearchMatch"]["abi"]

    print("[Blockchain] Enviando transação de Deploy para o Ganache...")
    # Inicializa a estrutura do contrato para deploy
    SearchMatchContract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Envia a transação de criação do contrato
    tx_hash = SearchMatchContract.constructor().transact()
    
    print("[Blockchain] Aguardando confirmação do bloco...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    contract_address = tx_receipt.contractAddress

    print("\n" + "="*50)
    print(f" SUCCESS: Contrato ativado com sucesso no Ganache!")
    print(f" Endereço do Contrato: {contract_address}")
    print("="*50 + "\n")

    # Salva a ABI e o Endereço em um arquivo JSON para que os outros módulos leiam automaticamente
    config_data = {
        "contract_address": contract_address,
        "abi": abi
    }
    with open("contract_config.json", "w") as config_file:
        json.dump(config_data, config_file, indent=4)
    print("[Blockchain] Configurações salvas em 'contract_config.json'.")

if __name__ == "__main__":
    deploy()