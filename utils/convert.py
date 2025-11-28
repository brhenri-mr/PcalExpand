
def kn_para_tf(n_kn:float, mx_knm:float, my_knm:float, mx_base:float, my_base:float) ->tuple[float, float, float, float, float]:
    """
    Converte os esforços de kN e kN.m para o padrão interno do Pcal de tf e tf.m

    Parameters
    ----------
    n_kn: Esforço normal em kN  
    mx_knm: Momento x do topo em kN.m  
    my_knm: Momento y do topo em kN.m  
    mx_base: Momento x da base em kN.m  
    my_base: Momento y da base em kN.m  

    """
    return (round(n_kn*0.10, 5), 
            round(mx_knm*0.10, 5), 
            round(my_knm*0.10, 5), 
            round(mx_base*0.10, 5), 
            round(my_base*0.10, 5))
