import sys
import psutil
import time

def matar_todos_java():
    """Mata TODOS os processos Java do pcalc"""
    contagem = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'java' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'pcalc.jar' in cmdline:
                    proc.kill()
                    proc.wait(timeout=2)
                    contagem += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass
    
    if contagem > 0:
        print(f"    → {contagem} processo(s) Java matado(s)")
        time.sleep(1)
    return contagem


def matar_java_travado():
    """Mata processos Java do pcalc.jar travados"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'java' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'pcalc.jar' in cmdline:
                    print(f"Matando processo Java PID {proc.info['pid']}")
                    proc.kill()
                    proc.wait(timeout=3)  # Aguarda o processo terminar
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass

