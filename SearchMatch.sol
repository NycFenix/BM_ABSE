// SPDX-License-Identifier: MIT 
pragma solidity ^0.8.0;

contract SearchMatch {
    // Estrutura do índice do Data Owner
    struct Index {
        uint256[2] W1; // Vetor G1 (X e Y)
        uint256[4] W2; // Vetor que usa números complexos (4 coordenadas)
        address owner; // Endereço do Data Owner
        string fileCID; // localização do arquivo criptografado na nuvem
    }   

    mapping(uint256 => Index) public registry; // Tabela Hash: Associda um número identificador a estrutura Index

    event MatchFound(string fileCID); 
    event MatchFailed();

    uint256 public indexCount; 
    
    // Registrando índice gerado pelo Data Owner acima
    function registerIndex(uint256[2] memory _w1, uint256[4] memory _w2, string memory _fileCID) public {
        registry[indexCount] = Index(_w1, _w2, msg.sender, _fileCID);
        indexCount++;
    }

    function searchMatch(uint256 indexId, uint256[4] memory T1, uint256[2] memory T2) public returns (bool) {
        Index memory idx = registry[indexId];

        // Smart Contract valida se e(T1,W1) == e(T2, W2)
        // A função precompile do artigo no endereço 0x08
        // O precompile no endereço x08 não testa se o pareamento é igual a outro,
        // mas sim se a multiplicação dos pareamentos é 1
        // recebe múltiplos de 6 elementos para somar os pareamentos e retornar 1 se a soma for 0.

        // e(G1, G2) * e(G1', G2') = 1 => ISSO EQUIVALE A e(A, B) * e(C, D)
        // invertendo o sinal de um dos elementos do produto

  

    
        uint256[12] memory input;

        // Primeiro par: e(T2, w2)
        input[0] = T2[0];
        input[1] = T2[1];
        input[2] = idx.W2[0];
        input[3] = idx.W2[1];
        input[4] = idx.W2[2];
        input[5] = idx.W2[3];

        // Segundo par: e(W1, -T1)
        uint256 q = 21888242871839275222246405745257275088696311157297823662689037894645226208583; // Ordem da curva
        input[6] = idx.W1[0];
        input[7] = idx.W1[1];
        input[8] = T1[0];
        input[9] = (q - T1[1]); // invertendo o sinal de t1
        input[10] = T1[2];
        input[11] = (q - T1[3]); // invertendo o sinal de t1

        uint256[1] memory output;
        bool success;

        assembly {
            // Chama o precompile de pareamento (0x08) "alt_bn128"
            // input: 12 elementos (2 pares de pontos G1 e G2)
            // output: 1 elemento (resultado do pareamento)
            success := call(sub(gas(), 2000), 8, 0, input, 384, output, 32)
        }

        if (success && output[0] == 1) {
            emit MatchFound(idx.fileCID);
            return true;
        } else {
            emit MatchFailed();
            return false;
        }
    }

}