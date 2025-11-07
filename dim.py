from utils.extract import init_data
from utils.wapper import PCalcEngine
from run import run_analysis
import pandas as pd


def especial_case(value):
    if value == 10000000000.0:
        return 'Ok!'
    return value

PATH = r'excel\Esforços estacas.xlsx'
esforcos, combine, frame = init_data(PATH)
engine = PCalcEngine(jar_path=r"engine/pcalc.jar")

bitolas = [10, 12.5, 16, 20, 25, 32]
quantidades = range(4,30)
esforco = [(-153.7319, -0.10896, -1.35123, 0, 0)]

saida = {'n':quantidades}
for quantidade in quantidades:
    for barra in bitolas:
        fs, _, _, _ = run_analysis(engine, esforco, barra, (quantidade, 0))

        if barra not in saida.keys():
            minimo = min(fs[0])
            saida[barra] = [minimo]
        else:
            minimo = min(fs[0])

            saida[barra].append(minimo)

print(saida)

df = pd.DataFrame(saida)
df_com_indice = df.set_index('n')
df_com_indice.to_excel('temp.xlsx')
