from glob import glob
import os

def clear_folder():
    '''
    Remove os JSON temporário
    '''
    for el in glob('*.json'):
        os.remove(el)
