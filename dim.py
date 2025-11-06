from utils.extract import init_data
from utils.wapper import PCalcEngine
from run import run_analysis
import pandas as pd


def especial_case(value):
    if value == 10000000000.0:
        return 'N conver.'

    return value

PATH = r'excel\Pilares DAT.xlsx'
esforcos, combine, frame = init_data(PATH)
engine = PCalcEngine(jar_path=r"engine/pcalc.jar")

bitolas = [5.0, 6.3, 8, 12.5, 16, 20, 25, 32]
quantidades = [4,6,8,10,12, 13, 14, 15, 16,18,20]
esforco = [(-425.7256, -8.63801, 32.52083, 18.52773, -79.61383)]

saida = {'n':quantidades}
for quantidade in quantidades:
    for barra in bitolas:
        fs, _, _, _ = run_analysis(engine, esforco, barra, (quantidade, 0))

        if barra not in saida.keys():
            minimo = min(fs[0])
            saida[barra] = [especial_case(minimo)]
        else:
            minimo = min(fs[0])

            saida[barra].append(especial_case(minimo))

print(saida)

df = pd.DataFrame(saida)
df_com_indice = df.set_index('n')
df_com_indice.to_excel('temp.xlsx')
