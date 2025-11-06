import subprocess
from collections import Counter
import sys


# Adicione esta função antes do loop
def verificar_travamento(timeout=10):
    """Monitora se está travado em loop de erro"""
    msg_count = Counter()
    max_repeats = 30
    
    # Redireciona temporariamente o stderr para capturar erros
    import io
    from contextlib import redirect_stderr, redirect_stdout
    
    captured = io.StringIO()
    
    with redirect_stderr(captured), redirect_stdout(captured):
        yield
    
    output = captured.getvalue()
    for line in output.split('\n'):
        msg = line.strip()
        if msg:
            msg_count[msg] += 1
            if msg_count[msg] >= max_repeats:
                raise Exception(f"Processo travado - msg repetida {max_repeats}x")
