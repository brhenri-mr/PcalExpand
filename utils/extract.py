import pandas as pd
from utils.convert import kn_para_tf


def pre_treatment(path):
    '''
    Prepara os dados para serem usados pelos extratores
    '''
    df = pd.read_excel(path, header=1)
    kn = df.iloc[0]['P'] == 'KN'

    df = pd.read_excel(path, header=1)
    df = df.iloc[1:]
    df = df[(df['Station'] == df['Station'].max()) | (df['Station'] == df['Station'].min())]

    return kn, df



def init_data(path:str, limit:list[int]|None=None):

    kn, df = pre_treatment(path)

    esforcos = []
    combine = []
    frame = []

    for i in range(df.shape[0] - 1):
        topo = df.iloc[i]
        base = df.iloc[i+1]
        frame.append(topo["Frame"])
        combine.append(topo['OutputCase'])
        if kn:
            esforcos.append(kn_para_tf(topo['P'], topo['M2'], topo['M3'], base['M2'], base['M3']))
        else:
            esforcos.append((topo['P'], topo['M2'], topo['M3'], base['M2'], base['M3']))
    
    return [esforcos[limit[0]:limit[1]], combine[limit[0]:limit[1]], frame[limit[0]:limit[1]]] if isinstance(limit, list) else [esforcos, combine, frame]


def preparar_lotes(path, tamanho_lote=10):
    """
    Divide o DataFrame em lotes menores
    """
    kn, df = pre_treatment(path)

    esforcos = []
    combine = []
    frame = []
    indices = []

    
    for i in range(df.shape[0] - 1):
        topo = df.iloc[i]
        base = df.iloc[i+1]
        frame.append(topo["Frame"])
        combine.append(topo['OutputCase'])
        
        if kn:
            esforcos.append(kn_para_tf(topo['P'], topo['M2'], topo['M3'], base['M2'], base['M3']))
        else:
            esforcos.append((topo['P'], topo['M2'], topo['M3'], base['M2'], base['M3']))
        indices.append(i)
    
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
