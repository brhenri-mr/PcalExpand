
from utils.wapper import PCalcEngine
from utils.misc import matar_java_travado
from utils.output import create_xlsx
from utils.extract import init_data
from utils.plot import plot_situation
from threading import Thread
import time
import sys
import psutil
from datetime import datetime


def run_analysis(engine, esforcos, diametro_mm, barras:tuple[int, int] = (16, 0)):
    # Seu loop modificado:
    sucessos = []
    falhas = []
    fs = []

    plot = {'curvas_mr':[], 'esforco':[]}

    nx, ny = barras 

    with open('log.txt', 'a', encoding='utf-8', buffering=1) as arquivo:     
        for i, el in enumerate(esforcos):
            resultado_container = [None]
            
            def executar():
                resultado_container[0] = engine.calcular_envoltoria(
                    diametro_mm=diametro_mm,
                    nx=nx, ny=ny,
                    d_linha=8,
                    n_barras=nx,
                    esforcos=[el]
                )
            
            thread = Thread(target=executar)
            thread.daemon = True
            thread.start()
            thread.join(timeout=50)
            
            resultado = resultado_container[0]
            
            if resultado and resultado.get('sucesso'):
                print(f"✓ Iteração {i} concluída - {datetime.now()}")
                arquivo.write(f"✓ Iteração {i} concluída - {datetime.now()}\n")
                arquivo.flush()
                fs.append(resultado_container[0]['fs_por_combinacao'][0])
                plot['curvas_mr'].append(resultado['curvas_mr'])
                plot['esforco'].append(el)
                sucessos.append(i)
            else:
                print(f"⚠️  Iteração {i} travou - matando Java e pulando...")
                fs.append(['falhou']*11)
                del engine
                engine = PCalcEngine(jar_path="pcalc.jar")
                matar_java_travado()
                falhas.append(i)
                time.sleep(2)  # Aguarda processo morrer
                sys.stdout.flush()
    
    return fs, sucessos, falhas, plot

if __name__ == '__main__':

    # Inicializa o engine
    engine = PCalcEngine(jar_path=r"engine/pcalc.jar")

    print("-" * 70)

    esforcos, combine, frame = init_data(r'excel\Pilares 07.11.xlsx')
    print(esforcos)
    fs, sucessos, falhas, resultado = run_analysis(engine, [esforcos[3]], 16, (8, 0))

    print(f"\nSucessos: {len(sucessos)} | Falhas: {len(falhas)}")
    print(fs)
    #create_xlsx(fs, frame=frame[:80], combine=combine[:80], esforcos=esforcos[:80])
    #plot_situation(resultado['curvas_mr'], resultado['esforco'])