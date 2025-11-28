from utils.extract import init_data
from utils.wapper import PCalcEngine
from run import run_analysis
import pandas as pd


def especial_case(value):
    if value == 10000000000.0:
        return 'Ok!'
    return value

PATH = r'excel\pILARES ULTIMO.xlsx'
#esforcos, combine, frame = init_data(PATH)
engine = PCalcEngine(jar_path=r"engine/pcalc.jar")

bitolas = [10, 12.5, 16, 20, 25, 32]
quantidades = range(4,50)
esforco = (-316.8816	,66.37991	,75.89921	,-7.35069	,129.33481)



saida = {'n':quantidades}
for quantidade in quantidades:
    for barra in bitolas:
        print(f'Barra: {barra}, Quantidade: {quantidade}')
        fs, _, _, _ = run_analysis(engine, [esforco], barra, (quantidade, 0))

        if barra not in saida.keys():
            print(fs[0])
            minimo = min(fs[0])
            print(minimo)
            saida[barra] = [minimo]
        else:
            print(fs[0])
            minimo = min(fs[0])
            print(minimo)

            saida[barra].append(minimo)
    print('-'*70)

df = pd.DataFrame(saida)
df_com_indice = df.set_index('n')
df_com_indice.to_excel(f'DIM-{PATH.replace('.xlsx', '').split('\\')[-1]}.xlsx')







