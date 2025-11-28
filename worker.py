import sys
import json
import time
from threading import Thread
from utils.wapper import PCalcEngine
from utils.misc import matar_todos_java

# FORCE UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')



def processar_lote(lote_data):
    """
    Processa um lote de cálculos com lógica robusta de thread + timeout
    """
    sucessos = []
    falhas = []
    fs = []
    falhas_consecutivas = 0
    
    # Inicializa engine
    print("Inicializando engine...")
    engine = PCalcEngine(jar_path=r"engine/pcalc.jar")
    
    esforcos = lote_data['esforcos']
    indices = lote_data['indices']
    
    for idx, (i, el) in enumerate(zip(indices, esforcos)):
        print(f"  [{idx+1}/{len(esforcos)}] Cálculo {i}...", end=' ', flush=True)
        
        resultado_container = [None]
        thread_travou = False
        
        def executar():
            try:
                resultado_container[0] = engine.calcular_envoltoria(
                    diametro_mm=25,
                    d_linha=8,
                    n_barras=10,
                    esforcos=[el]
                )
            except Exception as e:
                print(f"\n    ERRO na thread: {e}")
                resultado_container[0] = None
        
        # Executa em thread com timeout
        thread = Thread(target=executar)
        thread.daemon = True
        inicio = time.time()
        thread.start()
        thread.join(timeout=5.0)  # 30 segundos de timeout
        tempo_decorrido = time.time() - inicio
        
        resultado = resultado_container[0]
        
        # Verifica se travou
        if thread.is_alive():
            thread_travou = True
        
        # Processa resultado
        if resultado and resultado.get('sucesso') and not thread_travou:
            mensagem = f"✓ OK ({tempo_decorrido:.1f}s)"
            print(mensagem)
            
            fs.append(resultado['fs_por_combinacao'][0])
            sucessos.append(i)
            falhas_consecutivas = 0
            
        else:
            # Determina tipo de falha
            if thread_travou:
                tipo_falha = "TRAVOU (timeout)"
            elif resultado is None:
                tipo_falha = "ERRO"
            else:
                tipo_falha = "FALHOU"
            
            mensagem = f"✗ {tipo_falha} ({tempo_decorrido:.1f}s)"
            print(mensagem)
            
            fs.append(['falhou']*11)
            falhas.append(i)
            falhas_consecutivas += 1
            
            # REINICIALIZA O ENGINE após cada falha
            print("    → Destruindo engine...", flush=True)
            try:
                del engine
            except:
                pass
            
            print("    → Matando processos Java...", flush=True)
            matar_todos_java()
            
            print("    → Reinicializando engine...", flush=True)

            engine = PCalcEngine(jar_path="pcalc.jar")
            
            # Se muitas falhas consecutivas, pausa maior
            if falhas_consecutivas >= 3:
                print("    → Muitas falhas consecutivas, pausando 5s...")
                time.sleep(5)
                falhas_consecutivas = 0
            else:
                time.sleep(0.5)
    
    # Limpa engine no final
    try:
        del engine
    except:
        pass
    
    matar_todos_java()
    
    return {
        'fs': fs,
        'sucessos': sucessos,
        'falhas': falhas
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python worker.py <arquivo_lote.json>")
        sys.exit(1)
    
    lote_file = sys.argv[1]
    
    try:
        # Carrega dados do lote
        with open(lote_file, 'r') as f:
            lote_data = json.load(f)
        
        # Processa
        resultado = processar_lote(lote_data)
        
        # Salva resultado
        lote_id = lote_file.replace('lote_', '').replace('.json', '')
        resultado_file = f'resultado_{lote_id}.json'
        
        with open(resultado_file, 'w') as f:
            json.dump(resultado, f)
        
        print(f"\n✓ Lote {lote_id} finalizado!")
        print(f"  Sucessos: {len(resultado['sucessos'])}")
        print(f"  Falhas: {len(resultado['falhas'])}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n ERRO FATAL no worker: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)