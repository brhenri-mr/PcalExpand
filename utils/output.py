import pandas as pd


def create_xlsx(resultados_fs, frame, combine, esforcos):

    df = pd.DataFrame()

    df['frame'] = frame
    df['OutputCase'] = combine

    for i, label in enumerate(['N', 'Mx_topo', 'My_topo', 'Mx_base', 'My_base']):
        df[label] = [el[i] for el in esforcos]


    for label in range(11):
        df[f'{round(label*0.1, 1)}L'] = [el[label] for el in resultados_fs]

    verificados = []
    maximos = []
    mininumo = []

    for el in resultados_fs:

        verificados.append(not (False in [fs > 1 if isinstance(fs, (int, float)) else False for fs in el]))
        maximos.append(max(el))
        mininumo.append(min(el))

    df['max'] = maximos
    df['min']= mininumo
    df['verificado'] = verificados


    df.to_excel('saida.xlsx')
