import json
import os
import numpy as np

# --- CONFIGURAÇÃO CRÍTICA DE BACKEND PARA EVITAR FALHAS VISUAIS ---
import matplotlib
matplotlib.use('Agg') # Força a renderização direto em arquivo, sem depender da GUI do SO
import matplotlib.pyplot as plt
# -----------------------------------------------------------------

def gerar_painel_graficos():
    arquivo_dados = "metricas_demonstracao.json"
    
    if not os.path.exists(arquivo_dados):
        print(f"[ERRO] Arquivo '{arquivo_dados}' nao encontrado. Rode o 'data_user.py' primeiro.")
        return

    print("[Plotter] Carregando metricas reais colhidas no teste...")
    with open(arquivo_dados, "r") as f:
        dados = json.load(f)
        
    casos_atributos = dados["casos_atributos"]
    historico_nuvem = dados["historico_nuvem"]
    historico_iot = dados["historico_iot"]
    historico_payload = dados["historico_payload"]
    historico_original = dados["historico_original"]
    dados_grafico3 = dados["dados_grafico3"]

    print("[Plotter] Renderizando painel cientifico unificado...")
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5.5))
    
    # ---- PLOT GRÁFICO 1 (TEMPO DE EXECUÇÃO) ----
    ax1.plot(casos_atributos, historico_nuvem, color='#1f77b4', marker='o', linewidth=2, label='SemiDecrypt (Nuvem)')
    ax1.plot(casos_atributos, historico_iot, color='#d62728', marker='s', linewidth=2, label='DataDecrypt (IoT)')
    ax1.set_title('Gráfico 1: Desempenho Computacional', fontsize=11, fontweight='bold', pad=10)
    ax1.set_xlabel('Quantidade de Atributos')
    ax1.set_ylabel('Tempo (ms)')
    ax1.set_xticks(casos_atributos)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(frameon=True, facecolor='#fafafa')
    
    # ---- PLOT GRÁFICO 2 (OVERHEAD DE REDE) ----
    x_indices = np.arange(len(casos_atributos))
    width = 0.35
    ax2.bar(x_indices - width/2, historico_original, width, label='Dado Original', color='#7f7f7f', alpha=0.7)
    ax2.bar(x_indices + width/2, historico_payload, width, label='Texto Cifrado (Rede)', color='#2ca02c', alpha=0.8)
    ax2.set_title('Gráfico 2: Sobrecarga de Comunicação', fontsize=11, fontweight='bold', pad=10)
    ax2.set_xlabel('Quantidade de Atributos')
    ax2.set_ylabel('Tamanho do Pacote (Bytes)')
    ax2.set_xticks(x_indices)
    ax2.set_xticklabels(casos_atributos)
    ax2.grid(True, axis='y', linestyle='--', alpha=0.5)
    ax2.legend(frameon=True, facecolor='#fafafa')
    
    # ---- PLOT GRÁFICO 3 (DISTRIBUIÇÃO MULTI-AUTORIDADE) ----
    cenarios = ['1 AA Central', '2 AAs (Dividido)', '3 AAs (Dividido)']
    bars = ax3.bar(cenarios, dados_grafico3, color=['#9467bd', '#bcbd22', '#17becf'], width=0.5, edgecolor='#444444', linewidth=0.7)
    for bar in bars:
        height = bar.get_height()
        ax3.annotate(f'{height:.1f} ms', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')
    ax3.set_title('Gráfico 3: Tempo de Emissão (KeyGen)\npor Servidor (Total: 12 Atributos)', fontsize=11, fontweight='bold', pad=10)
    ax3.set_ylabel('Tempo de Processamento Criptográfico (ms)')
    ax3.set_ylim(0, max(dados_grafico3) * 1.2)
    ax3.grid(True, axis='y', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    
    # Salva diretamente no repositório local
    nome_arquivo = 'tcc_validacao_completa.png'
    plt.savefig(nome_arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig) # Libera o buffer de memória do Matplotlib
    
    print(f"\n" + "="*60)
    print(f"[SUCESSO] Painel salvo com sucesso!")
    print(f"Arquivo gerado: {os.path.abspath(nome_arquivo)}")
    print("="*60 + "\n")

if __name__ == "__main__":
    gerar_painel_graficos()