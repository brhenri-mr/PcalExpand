import pandas as pd
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)



def create_xlsx(resultados_fs:list[list], frame:list[str], combine:list[str], esforcos:list[tuple], name:str='saida')->None:
    '''
    Exporta os dados em um arquivo excel

    Parameters
    ---------
    resultados_fs: Lista com os fatores do degurança do pcal  
    frame: Lista com o nome dos frames
    combine: lista com as combinações
    esforco: lista com os esforcos que provocaram os fs
    name: Nome do arquivo de saida

    
    '''
    # Dados
    verificados = []
    maximos = []
    mininumo = []

    # Instanciando um dataframe
    df = pd.DataFrame()

    # Atribuindo colonas de frame e combinação na ordem que devem aparecer
    df['frame'] = frame
    df['OutputCase'] = combine

    # Atribuindo as colunas dos esforcos
    for i, label in enumerate(['N', 'Mx_topo', 'My_topo', 'Mx_base', 'My_base']):
        df[label] = [el[i] for el in esforcos]

    # Atribuindo as colunas dos esforços pelo comprimento da barra
    if config['elemento']['L'] != 0:
        if config['method']['2_ordem'] == 3:
            temp = ['0 (Base)', 'Intermed', 'L (topo)', ]
            for label in range(3):
                df[temp[label]] = [el[label] if 10000000000 != el[label] else "Não Converge" for el in resultados_fs]
        else:
            for label in range(11):
                df[f'{round(label*0.1, 1)}L'] = [el[label] if 10000000000 != el[label] else "Não Converge" for el in resultados_fs]
     


    # Atribuindo os valores máximos e mínimo e a condição de verificação
    for el in resultados_fs:
        verificados.append(not (False in [fs > 1 if isinstance(fs, (int, float)) else False for fs in el]))
        maximos.append(max(el))
        mininumo.append(min(el))

    # Atribuindo os valores máximos, mínimos e fs na ordem que aparecem
    df['max'] = maximos
    df['min']= mininumo
    df['verificado'] = verificados

    # Exportando o excel
    df.to_excel(f'PCAL-{name}.xlsx')
