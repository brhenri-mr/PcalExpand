import json
from glob import glob
from utils.extract import init_data
from utils.output import create_xlsx


def ordenar(txt):
    return int(txt.split("_")[-1].replace('.json',''))


fs_total = []
for i, path in enumerate(sorted(glob('*.json'), key=ordenar)):
    with open(path, 'r') as arquivo:
        print(path, i)
        [fs_total.append(el) for el in json.load(arquivo)['fs']]


PATH = r'excel\Pilares DAT.xlsx'
esforcos, combine, frame = init_data(PATH)
if len(esforcos) == len(fs_total):
    print('Dimensões Corretas!')
    create_xlsx(fs_total, frame=frame, combine=combine, esforcos=esforcos)
    

