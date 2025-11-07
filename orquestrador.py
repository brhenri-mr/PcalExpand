import subprocess
import pandas as pd
import time
import json
import os
from utils.extract import preparar_lotes, init_data
from utils.output import create_xlsx
from utils.pos_processing import clear_folder


def executar_lote(lote_id, lote_data, timeout=300):
    """
    Executa um lote em subprocess e aguarda finalização
    """
    # Salva dados do lote em arquivo JSON temporário
    lote_file = f'lote_{lote_id}.json'
    with open(lote_file, 'w') as f:
        json.dump(lote_data, f)
    
    print(f"\n{'='*70}")
    print(f"   LOTE {lote_id + 1} - Iniciando subprocess")
    print(f"   Índices: {lote_data['indices'][0]} a {lote_data['indices'][-1]}")
    print(f"   Total de cálculos: {len(lote_data['esforcos'])}")
    print(f"{'='*70}\n")
    
    inicio = time.time()
    
    try:
        # Executa o worker em subprocess
        resultado = subprocess.run(
            ['python', 'worker.py', lote_file],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        tempo_decorrido = time.time() - inicio
        
        # Verifica resultado
        if resultado.returncode == 0:
            print(f"\n LOTE {lote_id + 1} - SUCESSO ({tempo_decorrido:.1f}s)")
            
            # Lê resultados
            resultado_file = f'resultado_{lote_id}.json'
            if os.path.exists(resultado_file):
                with open(resultado_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️  Arquivo de resultado não encontrado")
                return None
        else:
            print(f"\n LOTE {lote_id + 1} - FALHOU (código: {resultado.returncode})")
            print(f"STDOUT: {resultado.stdout}")
            print(f"STDERR: {resultado.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"\n LOTE {lote_id + 1} - TIMEOUT ({timeout}s)")
        return None
        
    except Exception as e:
        print(f"\n LOTE {lote_id + 1} - ERRO: {e}")
        return None
    
    finally:
        # Limpa arquivo temporário do lote
        if os.path.exists(lote_file):
            os.remove(lote_file)


def consolidar_resultados(resultados_lotes):
    """
    Consolida resultados de todos os lotes
    """
    fs_total = []
    sucessos_total = []
    falhas_total = []
    
    for resultado in resultados_lotes:
        if resultado:
            fs_total.extend(resultado.get('fs', []))
            sucessos_total.extend(resultado.get('sucessos', []))
            falhas_total.extend(resultado.get('falhas', []))
    
    return {
        'fs': fs_total,
        'sucessos': sucessos_total,
        'falhas': falhas_total
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("="*70)
    print("ORQUESTRADOR DE CÁLCULOS")
    print("="*70)
    

    PATH = r'excel\Esforços estacas.xlsx'
    TAMANHO_LOTE = 100  # Ajuste conforme necessário

    # Prepara lotes
    
    print(f"📦 Preparando lotes de {TAMANHO_LOTE} cálculos...")
    lotes = preparar_lotes(PATH, tamanho_lote=TAMANHO_LOTE, lim=5)
    print(f"✓ {len(lotes)} lotes preparados - total de {len(lotes)*TAMANHO_LOTE}\n")
    
    # Executa lotes sequencialmente
    inicio_total = time.time()
    resultados_lotes = []

    #retry =[12]
    #for i, lote in enumerate(lotes):
    for i, lote in enumerate(lotes):
        #i = retry[i] - 1
        #lote = lotes[i]
        resultado = executar_lote(i, lote, timeout=500)  
        resultados_lotes.append(resultado)
        
        # Pequena pausa entre lotes
        if i < len(lotes) - 1:
            print("\n⏸️  Pausa antes do próximo lote...")
            time.sleep(0.5)
    
    tempo_total = time.time() - inicio_total
    
    # Consolida resultados
    print("\n" + "="*70)
    print("📊 CONSOLIDANDO RESULTADOS")
    print("="*70)
    
    resultado_final = consolidar_resultados(resultados_lotes)
    
    print(f"\n✅ Sucessos: {len(resultado_final['sucessos'])}")
    print(f"❌ Falhas: {len(resultado_final['falhas'])}")
    print(f"⏱️  Tempo total: {tempo_total:.1f}s")
    print(f"⏱️  Tempo médio por lote: {tempo_total/len(lotes):.1f}s")
    
    # Gera planilha final
    print("\n📄 Gerando planilha final...")

    
    # Reconstrói dados completos
    esforcos, combine, frame = init_data(PATH)
    #create_xlsx(resultado_final['fs'], frame=frame, combine=combine, esforcos=esforcos)
    #clear_folder()

    print("✅ PROCESSAMENTO COMPLETO!")
    print("="*70)