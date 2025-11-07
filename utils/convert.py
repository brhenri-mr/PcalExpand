
def kn_para_tf(n_kn, mx_knm, my_knm, mx_base, my_base):
    """Converte kN e kN.m para tf e tf.m"""
    return (round(n_kn*0.10, 5), 
            round(mx_knm*0.10, 5), 
            round(my_knm*0.10, 5), 
            round(mx_base*0.10, 5), 
            round(my_base*0.10, 5))
