import matplotlib.pyplot as plt

def plot_situation(resultado, dots):

    plt.xlabel('My (tf.m)')
    plt.ylabel('Mx (tf.m)')
    # Plotar envoltória
    for i, inf in enumerate(resultado):
        mx = [p['mx_tfm'] for p in inf]
        my = [p['my_tfm'] for p in inf]
        plt.plot(my, mx,  'b-')
        pontos = dots[i]
        plt.scatter(pontos[2], pontos[1], s=20, color='orange', edgecolors='black',linewidths=1)
        plt.scatter(pontos[4], pontos[3], s=20, color='orange', edgecolors='black',linewidths=1)

    plt.title('Diagrama de Interação Mx × My')
    print(f"\n  Gráfico salvo: envoltoria_exemplo1.png")
    plt.savefig('envoltoria_exemplo1.png', dpi=850, bbox_inches='tight')
    #[print(el[::-1]) for el in resultado['fs_por_combinacao']]