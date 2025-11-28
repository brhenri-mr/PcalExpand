from utils.extract import init_data

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
