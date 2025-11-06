
def kn_para_tf(n_kn, mx_knm, my_knm, mx_base, my_base):
    """Converte kN e kN.m para tf e tf.m"""
    return (n_kn*0.10, mx_knm*0.10, my_knm*0.10, mx_base*0.10, my_base*0.10)
