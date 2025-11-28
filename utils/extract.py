import pandas as pd
from utils.convert import kn_para_tf
from pandas import DataFrame
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

def select_top_base(df_slice:DataFrame, i:int):
    '''
    Seleciona qual frame está no top e base

    Parameters
    ----------
    df_slice: Dataframe com os casos de carregamento
    i: elementos a serem considerados
    '''
    
    # Elementos
    # Verificando se a combinação é impar
    if i+1>=df_slice.shape[0]:
        #Avisando o usuário
        print('='*70)
        print('Combinação impar')
        print(df_slice)
        print('='*70)

        # Atribuindo como o passo anterior
        temp_1 = df_slice.iloc[i]
        temp_2 = df_slice.iloc[i-1]

        # Pedindo o julgamento do usuário
        criteria = input('Aprovar? (S/N)')

        # Avaliando julgamento
        if criteria != 'S':
            raise Exception('Erro: Combinação Impar')
        
    else:
        temp_1 = df_slice.iloc[i]
        temp_2 = df_slice.iloc[i+1]

    # Verificando quem está a cima com base na carga normal menor (sem o peso)
    if abs(temp_1['P']) <abs(temp_2['P']):
        topo = temp_1
        base = temp_2
    else:
        topo = temp_2
        base = temp_1

    return topo, base


def extremos(df:DataFrame, lim:float) -> DataFrame:
    '''
    Retorna os extremos para cada frame em forma de df

    Parameters
    ----------
    lim: Limite máximo de comprimento do frame
    df: dataframe com os esforços

    '''
    # Dados
    temp = {}

    # Iterando sobre os frames para buscar os valores extermos de comprimento do frame
    for frame in df['Frame'].unique():
        # Selecionando apenas a série com frames
        df_temp = df[df['Frame'] == frame] 

        # Atribuindo os valores limitrofes na variavel temp
        temp[frame] = {'max':df_temp[df_temp['Station']<=lim]['Station'].max(), 'min':df_temp['Station'].min()}
    return pd.DataFrame.from_dict(temp, orient='index')



def frame_body(df, lim):
    '''
    Faz o pre tratamento de valores para o caso onde existe esforço no corpo
    '''

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
    df_filtrado = df_filtrado.drop_duplicates(subset=['Frame', 'Station', 'M3', 'M2', 'P', 'OutputCase'])

    # A ordem está certa
    if lim == 100_000.00:
        return df_filtrado


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


    return df_resultado



def pre_treatment(path, lim:float):
    '''
    Prepara os dados para serem usados pelos extratores
    '''
    df = pd.read_excel(path, header=1)
    kn = df.iloc[0]['P'] == 'KN'

    df = pd.read_excel(path, header=1)
    df = df.iloc[1:]

    # Verificando o tipo de vinculação
    if config['elemento']['L'] == 0:
        return kn, df
    
    else:
        return kn, frame_body(df, lim)
        

def init_data(path:str, lim:float=100_000.00, limit=None) ->tuple[list[tuple[float, float, float, float, float]], list[str], list[str]]:
    '''
    Prepara os dados para serem injetados no Pcal.

    Parameters
    ----------
    path: caminho do excel  
    lim: tamanho máximo do frame  
    limit: quantidade de dados que serão considerados na analise (slice)

    '''
    # Dados
    esforcos = []
    combine = []
    frame = []

    # Instanciando os dados
    kn, df = pre_treatment(path, lim)

    #Iterando sobre os frames
    for el_frame in list(df['Frame'].unique()):
        # Combinações do frame
        combinacoes = list(df[df['Frame'] == el_frame]['OutputCase'].unique())

        # Iterando nas combinações do frame
        for combinacao in combinacoes:
            # Selecionando o elemento
            df_slice = df[df['Frame'] == el_frame]

            # Selecionado a combinação
            df_slice = df_slice[df_slice['OutputCase'] == combinacao]

            # Iterando sobre os elementos
            for i in range(0, df_slice.shape[0], 2):
                
                if config['elemento']['L'] == 0:
                    
                    try:
                        for el in [df_slice.iloc[i], df_slice.iloc[i+1]]:
                            frame.append(el["Frame"])
                            combine.append(el['OutputCase'])
                            esforcos.append(kn_para_tf(round(el['P'], 5), round(el['M2'], 5), round(el['M3'], 5), 0, 0) 
                                            if kn else (round(el['P'], 5), round(el['M2'], 5), round(el['M3'], 5), 0,0))
                    except Exception as e:
                        print(f'erro {i}: {e}')
                        el = df_slice.iloc[i]
                        frame.append(el["Frame"])
                        combine.append(el['OutputCase'])
                        esforcos.append(kn_para_tf(round(el['P'], 5), round(el['M2'], 5), round(el['M3'], 5), 0, 0) 
                                        if kn else (round(el['P'], 5), round(el['M2'], 5), round(el['M3'], 5), 0,0))


                    
                else:
                    topo, base = select_top_base(df_slice, i)

                    frame.append(topo["Frame"])
                    combine.append(topo['OutputCase'])
                    esforcos.append(kn_para_tf(round(topo['P'], 5), round(topo['M2'], 5), round(topo['M3'], 5), round(base['M2'], 5), round(base['M3'], 5)) 
                                    if kn else (round(topo['P'], 5), round(topo['M2'], 5), round(topo['M3'], 5), round(base['M2'], 5), round(base['M3'], 5)))


    return (esforcos[limit[0]:limit[1]], combine[limit[0]:limit[1]], frame[limit[0]:limit[1]]) if isinstance(limit, list) else (esforcos, combine, frame)
