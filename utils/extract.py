import pandas as pd
from utils.convert import kn_para_tf

def pre_treatment_old(path):
    '''
    Prepara os dados para serem usados pelos extratores
    '''
    df = pd.read_excel(path, header=1)
    kn = df.iloc[0]['P'] == 'KN'

    df = pd.read_excel(path, header=1)
    df = df.iloc[1:]
    df = df[(df['Station'] == df['Station'].max()) | (df['Station'] == df['Station'].min())]

    return kn, df

def extremos(df, lim):
    '''
    Retorna os extremos para cada frame em forma de df
    '''
    temp = {}

    for frame in df['Frame'].unique():
        df_temp = df[df['Frame'] == frame]
        temp[frame] = {'max':df_temp[df_temp['Station']<=lim]['Station'].max(), 'min':df_temp['Station'].min()}
    return pd.DataFrame.from_dict(temp, orient='index')


def pre_treatment(path, lim):
    '''
    Prepara os dados para serem usados pelos extratores
    '''
    df = pd.read_excel(path, header=1)
    kn = df.iloc[0]['P'] == 'KN'

    df = pd.read_excel(path, header=1)
    df = df.iloc[1:]

    df_limites = extremos(df, lim)
    

    df_limites['Frame'] = df_limites.index
    # Fazer merge
    df_com_limites = df.merge(df_limites, on='Frame', how='left')

    # Filtrar apenas os extremos
    df_filtrado = df_com_limites[
        (df_com_limites['Station'] == df_com_limites['min']) | 
        (df_com_limites['Station'] == df_com_limites['max'])
    ]


    # Remover colunas auxiliares
    df_filtrado = df_filtrado.drop(columns=['min', 'max'])
    df_filtrado = df_filtrado.drop_duplicates(subset=['Frame', 'Station', 'M3', 'M2', 'P'])
    
    # A ordem está certa
    if lim == 100_000.00:
        return kn, df_filtrado


    # Criar grupos onde Station consecutivas são iguais
    df_filtrado['grupo'] = (df_filtrado['Station'] != df_filtrado['Station'].shift()).cumsum()

    # Agrupar e calcular a média das colunas numéricas
    df_resultado = df_filtrado.groupby('grupo').agg({
        'Frame': 'first',  # Manter o primeiro valor
        'Station': 'first',
        'P': 'mean', 
        'M2': 'first',
        'M3': 'first',
        'OutputCase': 'first',
        'Station': 'first',
    }).reset_index(drop=True)


    return kn, df_resultado


def init_data(path:str, lim:float=100_000.00, limit=None):

    kn, df = pre_treatment(path, lim)

    esforcos = []
    combine = []
    frame = []
    
    frames = list(df['Frame'].unique())

    for el_frame in frames:
        combinacoes = list(df[df['Frame'] == el_frame]['OutputCase'].unique())
        for combinacao in combinacoes:
            df_slice = df[df['Frame'] == el_frame]
            df_slice = df_slice[df_slice['OutputCase'] == combinacao]

            for i in range(0, df_slice.shape[0], 2): # corrigi o problema
                #print('-'*10)
                temp_1 = df_slice.iloc[i]
                temp_2 = df_slice.iloc[i+1]

                if abs(temp_1['P']) <abs(temp_2['P']):
                    topo = temp_1
                    base = temp_2
                else:
                    topo = temp_2
                    base = temp_1
                if topo["OutputCase"] == base["OutputCase"]:
                    pass
                    #print(f'Igual: {base["OutputCase"]}')
                else:
                    print(f'Diferente: {base["OutputCase"]} e {topo["OutputCase"]}')


                frame.append(topo["Frame"])
                combine.append(topo['OutputCase'])


                if kn:
                    esforcos.append(kn_para_tf(round(topo['P'], 5), round(topo['M2'], 5), round(topo['M3'], 5), round(base['M2'], 5), round(base['M3'], 5)))
                else:
                    #print((round(topo['P'], 5), round(topo['M2'], 5), round(topo['M3'], 5), round(base['M2'], 5), round(base['M3'], 5)))
                    esforcos.append((round(topo['P'], 5), round(topo['M2'], 5), round(topo['M3'], 5), round(base['M2'], 5), round(base['M3'], 5)))

    print(len(esforcos))
    return [esforcos[limit[0]:limit[1]], combine[limit[0]:limit[1]], frame[limit[0]:limit[1]]] if isinstance(limit, list) else [esforcos, combine, frame]


def init_data_old(path:str, limit:list[int]|None=None, lim:float=100_000.00):

    kn, df = pre_treatment(path, lim)

    esforcos = []
    combine = []
    frame = []

    for i in range(df.shape[0] - 1):
        print('-'*10)
        temp_1 = df.iloc[i]
        temp_2 = df.iloc[i+1]

        if abs(temp_1['P']) <abs(temp_2['P']):
            topo = temp_1
            base = temp_2
        else:
            topo = temp_2
            base = temp_1


        frame.append(topo["Frame"])
        combine.append(topo['OutputCase'])
        print('# Topo')
        print(topo)
        print('# Base')
        print(base)
        print('-'*10)
        if kn:
            esforcos.append(kn_para_tf(round(topo['P'], 5), round(topo['M2'], 5), round(topo['M3'], 5), round(base['M2'], 5), round(base['M3'], 5)))
        else:
            esforcos.append((round(topo['P'], 5), round(topo['M2'], 5), round(topo['M3'], 5), round(base['M2'], 5), round(base['M3'], 5)))
    
    return [esforcos[limit[0]:limit[1]], combine[limit[0]:limit[1]], frame[limit[0]:limit[1]]] if isinstance(limit, list) else [esforcos, combine, frame]


def preparar_lotes(path, tamanho_lote=10, lim:float=100_000.00):
    """
    Divide o DataFrame em lotes menores
    """

    esforcos, combine, frame = init_data(path, lim=lim)

    indices = list(range(len(esforcos)))

    # Divide em lotes
    lotes = []
    for i in range(0, len(esforcos), tamanho_lote):
        lote = {
            'indices': indices[i:i+tamanho_lote],
            'esforcos': esforcos[i:i+tamanho_lote],
            'combine': combine[i:i+tamanho_lote],
            'frame': frame[i:i+tamanho_lote]
        }
        lotes.append(lote)
    
    return lotes
