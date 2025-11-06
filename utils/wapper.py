"""
Wrapper Python completo para o motor de cálculo de flexo-compressão do pcalc
Inclui:
- Dimensionamento automático de armadura
- Cálculo de envoltória com armadura pré-definida
"""

import jpype
import jpype.imports
from typing import List, Dict, Any, Tuple, Optional
import json
import math
import os
import yaml


class PCalcEngine:
    """
    Wrapper Python para a engine de cálculo de envoltória de flexo-compressão.
    
    Uso para ENVOLTÓRIA (armadura definida):
        engine = PCalcEngine(jar_path="pcalc.jar")
        resultado = engine.calcular_envoltoria(
            fck=30,
            fyk=500,
            hx=40,
            hy=20,
            diametro_mm=12.5,
            nx=3,
            ny=3,
            d_linha=3.5
        )
        # Retorna pontos da envoltória (N, Mx, My)
    
    Uso para DIMENSIONAMENTO:
        resultado = engine.calcular(
            fck=30,
            fyk=500,
            hx=40,
            hy=20,
            esforcos=[(150, 40, 20)],
            cobrimento=2.5
        )
        # Retorna armadura dimensionada
    """
    
    def __init__(self, jar_path: str, jvm_path: Optional[str] = None):
        """
        Inicializa o wrapper e carrega o JAR do pcalc
        
        Args:
            jar_path: Caminho para o arquivo .jar do pcalc
            jvm_path: (Opcional) Caminho para a JVM específica
        """
        self.jar_path = jar_path
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Inicia a JVM se ainda não estiver rodando
        if not jpype.isJVMStarted():
            jvm_path = r'C:\Program Files\Java\jdk-25\bin\server\jvm.dll'
            devnull = open(os.devnull, 'w')
            jpype.startJVM(jvm_path, 
                           "--enable-native-access=ALL-UNNAMED",
                           classpath=[jar_path],
                           convertStrings=False)

            System = jpype.JClass('java.lang.System')
            PrintStream = jpype.JClass('java.io.PrintStream')
            null_stream = PrintStream(jpype.JClass('java.io.File')('NUL'))
            System.setOut(null_stream)
            System.setErr(null_stream)
        
        # Configurações
        self.config = config

        # Importa as classes Java necessárias
        self.Dados = jpype.JClass('pcalc.Dados')
        self.Dimensiona = jpype.JClass('pcalc.Dimensiona')
        self.DiscretizaSecao = jpype.JClass('pcalc.DiscretizaSecao')
        self.CurvaMr = jpype.JClass('pcalc.CurvaMr')
        self.CalculaMomCurv = jpype.JClass('pcalc.CalculaMomCurv')
        self.CalculaEsforcos = jpype.JClass('pcalc.CalculaEsforcos')
        self.CalculaFs = jpype.JClass('pcalc.CalculaFs')
        self.CalculaFsMomentoMin = jpype.JClass('pcalc.CalculaFsMomentoMin')   
        self.alphaB = jpype.JClass('pcalc.calcula.AlphaB') 
        self.ELS = jpype.JClass('pcalc.ELS')   
        self.dados = self.Dados()

        # Configurar o básico 
        self._configurar_materiais(self.dados)
        self._configurar_parametros(self.dados)
        self._configurar_disposicao(self.dados)
        


    def _configurar_disposicao(self, dados):
        dados.secao.setL(self.config['elemento']['L'])

    
    def _configurar_materiais(self, dados: Any, metodo_seg_ord:int=5) :
        """
        Configura propriedades dos materiais
        
        Args:
            dados: Objeto Dados do Java
            fck: Resistência característica do concreto (MPa)
            fyk: Resistência característica do aço (MPa)
            mod_es: Módulo de elasticidade do aço (GPa)
        """
        dados.config.setFck(self.config['materials']['concrete']['fck']*0.010)   # MPa → tf/cm²
        dados.config.setFyk(self.config['materials']['steel']['fyk']*0.010)   # MPa → tf/cm²
        dados.config.setModEs(self.config['materials']['steel']['mod_es']*10)     # GPa → tf/cm²
        dados.config.setMetodoSegOrd(metodo_seg_ord)  


    def _configurar_parametros(self, dados: Any, 
                            taxa_as_min: float = 0.004,
                            taxa_as_max: float = 0.04):
        """Configura parâmetros de cálculo"""
        #dados.config.setCobrimento(cobrimento)

        dados.config.setGamaF(self.config['coef']['gamma_f'])
        dados.config.setGamaC(self.config['coef']['gamma_c'])
        dados.config.setGamaS(self.config['coef']['gamma_s'])
        dados.config.setGamaF3(self.config['coef']['gamma_3'])

        dados.config.setConsiderarFluencia(1)

        dados.config.setNSecao(400)
        #dados.config.setNGraficoMomCurv(50)
        
        taxas = jpype.JArray(jpype.JDouble)(2)
        taxas[0] = taxa_as_min
        taxas[1] = taxa_as_max
        dados.config.setTaxa(taxas)


    def configurar_secao_retangular(self, dados: Any, hx: float, hy: float,tipo_vinculacao: int = 0):
        """
        Configura uma seção retangular
        
        Args:
            dados: Objeto Dados do Java
            hx: Largura da seção (cm)
            hy: Altura da seção (cm)
            tipo_vinculacao: 0=Bi-rotulado, 1=Engastado-rotulado, 2=Bi-engastado
        """
        dados.secao.setTipoSecao("Retangular")
        dados.secao.setHx(hx)
        dados.secao.setHy(hy)
        dados.secao.setTipoVinculacao(tipo_vinculacao)

        
        # Calcula propriedades geométricas
        area = hx * hy
        ix = hx * hy**3 / 12.0
        iy = hy * hx**3 / 12.0
        
        dados.secao.setAreaAc(area)
        dados.secao.setIX(ix)
        dados.secao.setIY(iy)
        dados.secao.setXm(hx / 2.0)
        dados.secao.setYm(hy / 2.0)
        

    def configurar_secao_circular(self, dados: Any, diametro: float, tipo_vinculacao: int = 0):
        """
        Configura uma seção circular
        
        Args:
            dados: Objeto Dados do Java
            diametro: Diâmetro da seção (cm)
            tipo_vinculacao: 0=Bi-rotulado, 1=Engastado-rotulado, 2=Bi-engastado
        """
        dados.secao.setTipoSecao("Circular")
        dados.secao.setHx(diametro)
        dados.secao.setHy(diametro)
        dados.secao.setHx1(diametro)  # ← ADICIONE ISSO!
        dados.secao.setHy1(diametro)  # ← E ISSO!
        dados.secao.setTipoVinculacao(tipo_vinculacao)
        
        # Calcula propriedades geométricas
        raio = diametro/2
        area = math.pi*raio**2
        ix = math.pi*(raio**4)/4
        
        dados.secao.setAreaAc(area)
        dados.secao.setIX(ix)
        dados.secao.setIY(ix)
        dados.secao.setXm(diametro/2)
        dados.secao.setYm(diametro/2)


    def configurar_secao_circular_vazada(self, dados: Any, diametro: float, tipo_vinculacao: int = 0, interno:float =0.0):
        """
        Configura uma seção circular
        
        Args:
            dados: Objeto Dados do Java
            diametro: Diâmetro da seção (cm)
            tipo_vinculacao: 0=Bi-rotulado, 1=Engastado-rotulado, 2=Bi-engastado
        """
        dados.secao.setTipoSecao("Circular Vazada")
        dados.secao.setHx(diametro)
        dados.secao.setHy(diametro)
        dados.secao.setHx1(diametro)  # ← ADICIONE ISSO!
        dados.secao.setHy1(interno) 
        dados.secao.setTipoVinculacao(tipo_vinculacao)
        
        # Calcula propriedades geométricas
        raio = diametro*0.5
        area = math.pi*raio**2 - 0.25*math.pi*(interno)**2
        ix = 0.25*math.pi*(raio**4)- 0.25*math.pi*((interno/2)**4)
        
        dados.secao.setAreaAc(area)
        dados.secao.setIX(ix)
        dados.secao.setIY(ix)
        dados.secao.setXm(diametro*0.5)
        dados.secao.setYm(diametro*0.5)
    
    
    def _montar_armadura_retangular(self, dados: Any, diametro_mm: float, 
                                    nx: int, ny: int, d_linha: float):
        """
        Monta a armadura para seção retangular seguindo a lógica do programa
        
        Args:
            dados: Objeto Dados
            diametro_mm: Diâmetro das barras em mm (ex: 12.5)
            nx: Número de barras no lado horizontal
            ny: Número de barras no lado vertical
            d_linha: Distância do CG da barra à face (cm)
        """
        from java.util import ArrayList
        
        hx = dados.secao.getHx()
        hy = dados.secao.getHy()
        fi = diametro_mm / 10.0  # Converte mm para cm
        asfi = math.pi * fi**2 / 4.0  # Área de uma barra
        
        lista_as = ArrayList()
        
        # Barras na base (y = d_linha)
        for i in range(nx):
            barra = jpype.JArray(jpype.JDouble)(4)
            barra[0] = d_linha + (hx - 2.0 * d_linha) / (nx - 1) * i
            barra[1] = d_linha
            barra[2] = asfi
            barra[3] = fi
            lista_as.add(barra)
        
        # Barras nas laterais (intermediárias)
        for i in range(1, ny - 1):
            # Lado esquerdo
            barra_esq = jpype.JArray(jpype.JDouble)(4)
            barra_esq[0] = d_linha
            barra_esq[1] = d_linha + (hy - 2.0 * d_linha) / (ny - 1) * i
            barra_esq[2] = asfi
            barra_esq[3] = fi
            lista_as.add(barra_esq)
            
            # Lado direito
            barra_dir = jpype.JArray(jpype.JDouble)(4)
            barra_dir[0] = hx - d_linha
            barra_dir[1] = d_linha + (hy - 2.0 * d_linha) / (ny - 1) * i
            barra_dir[2] = asfi
            barra_dir[3] = fi
            lista_as.add(barra_dir)
        
        # Barras no topo (y = hy - d_linha)
        for i in range(nx):
            barra = jpype.JArray(jpype.JDouble)(4)
            barra[0] = d_linha + (hx - 2.0 * d_linha) / (nx - 1) * i
            barra[1] = hy - d_linha
            barra[2] = asfi
            barra[3] = fi
            lista_as.add(barra)
        
        # Calcula área total
        area_total = asfi * lista_as.size()
        
        # Configura no objeto dados
        dados.armacao.setListaAs(lista_as)
        dados.armacao.setAreaAs(area_total)
        dados.armacao.setNx(nx)
        dados.armacao.setNy(ny)
        dados.armacao.setDL(d_linha)
        dados.armacao.setFi(fi)
    

    def _montar_armadura_circular(self, dados: Any, diametro_mm: float, 
                                  n_barras: int, d_linha: float):
        """
        Monta a armadura para seção circular
        
        Args:
            dados: Objeto Dados
            diametro_mm: Diâmetro das barras em mm
            n_barras: Número de barras distribuídas no perímetro
            d_linha: Distância do CG da barra à face (cm)
        """
        from java.util import ArrayList
        
        diametro_secao = dados.secao.getHx()
        fi = diametro_mm / 10.0
        asfi = math.pi * fi**2 / 4.0
        centro_x = dados.secao.getXm()
        centro_y = dados.secao.getYm()
        
        lista_as = ArrayList()
        ri = diametro_secao/2.0 - d_linha  # Raio até CG das barras
        
        for i in range(n_barras):
            teta = i * 2 * math.pi / n_barras
            barra = jpype.JArray(jpype.JDouble)(4)
            barra[0] = ri*math.cos(teta)
            barra[1] = ri*math.sin(teta)
            barra[2] = asfi
            barra[3] = fi
            lista_as.add(barra)
        
        area_total = asfi * n_barras
        
        dados.armacao.setListaAs(lista_as)
        dados.armacao.setAreaAs(area_total)
        dados.armacao.setNx(n_barras)
        dados.armacao.setNy(n_barras)
        dados.armacao.setDL(d_linha)
        dados.armacao.setFi(fi)
    

    def adicionar_esforcos(self, dados: Any, 
                          esforcos: List[Tuple[float, float, float, float, float]]):
        """
        Adiciona combinações de esforços (usado no dimensionamento)
        
        Args:
            dados: Objeto Dados do Java
            esforcos: Lista de tuplas (N, Mx, My, Mx_base, My_base) em tf e tf.m
        """
        from java.util import ArrayList
        
        lista_esforcos = ArrayList()
        for n, mx, my, mx_base, my_base in esforcos:
            esforco = jpype.JArray(jpype.JDouble)(7)
            esforco[0] = float(n) # nsk
            esforco[1] = float(mx) # msk,x topp
            esforco[2] = float(my) # msk,y (top)
            esforco[3] = float(mx_base) # msx,y base
            esforco[4] = float(my_base) # msk,y base
            esforco[5] = 0.0
            esforco[6] = 0.0
            lista_esforcos.add(esforco)
        
        dados.esforcos.setListaEsforcos(lista_esforcos)


    def _esbeltez(self, dados):
        '''
        Calcula a esbeltez da secao
        '''
        L = self.config['elemento']['L']
        tipo_vinculacao = self.config['elemento']['vinculacao']

        if tipo_vinculacao == 0:  # Bi-rotulado
            l_flamb = L
        elif tipo_vinculacao == 1:  # Bi-apoiado (engastado-rotulado)
            l_flamb = L
        elif tipo_vinculacao == 2:  # Bi-engastado
            l_flamb = 2.0 * L
        
        ix = dados.secao.getIX()
        iy = dados.secao.getIY()
        area = dados.secao.getAreaAc()

        # Calcula raio de giração
        rx = math.sqrt(ix/area)
        ry = math.sqrt(iy/area)
        
        
        # Calcula esbeltez
        lambda_x = int(l_flamb/rx)
        lambda_y = int(l_flamb/ry)
        
        dados.secao.setLambdaX(lambda_x)
        dados.secao.setLambdaY(lambda_y)
        dados.secao.setLambdaMax(max(lambda_x, lambda_y))


    def calcular_envoltoria(self,
                           diametro_mm: float = 12.5,
                           nx: int = 3,
                           ny: int = 3,
                           n_barras: Optional[int] = None,
                           d_linha: float = 3.5,
                           esforcos: Optional[List[Tuple[float, float, float, float, float]]] = None) -> Dict[str, Any]:
        """
        Calcula a envoltória de resistência com armadura pré-definida
        
        Args:
            tipo_secao: "retangular" ou "circular"
            hx: Largura (cm) - para retangular / Diâmetro - para circular
            hy: Altura (cm) - apenas para retangular
            diametro: Diâmetro da seção (cm) - para circular
            diametro_mm: Diâmetro das barras (mm): 5, 6.3, 8, 10, 12.5, 16, 20, 25, 32, 40
            nx: Número de barras no lado horizontal (retangular)
            ny: Número de barras no lado vertical (retangular)
            n_barras: Número de barras (circular)
            d_linha: Distância do CG da barra à face externa (cm)
            interno: ângulo interno vazado
            L: Comprimento da barra
            tipo_vinculacao: 0=secao-unica, 1=Bi-rotulado, 2=Engaste-livre
            
        Returns:
            Dicionário com envoltória e dados da armadura
            
        Example:
            >>> engine = PCalcEngine("pcalc.jar")
            >>> resultado = engine.calcular_envoltoria(
            ...     fck=30,
            ...     fyk=500,
            ...     hx=40,
            ...     hy=20,
            ...     diametro_mm=12.5,
            ...     nx=3,
            ...     ny=3,
            ...     d_linha=3.5
            ... )
            >>> pontos_x = resultado['envoltoria_nrd_mrdx']
            >>> pontos_y = resultado['envoltoria_nrd_mrdy']
        """
        
        dados = self.dados
        tipo_secao = self.config['elemento']['secao']['tipo_secao']
        tipo_vinculacao = self.config['elemento']['vinculacao']
        hx = self.config['elemento']['dim_x']
        hy = self.config['elemento']['dim_y']
        interno = self.config['elemento']['hole']
        diametro = self.config['elemento']['dim_x'] 

        # Configura seção
        if "retangular" in tipo_secao.lower():
            self.configurar_secao_retangular(dados, hx, hy, tipo_vinculacao)
            # Monta armadura retangular
            self._montar_armadura_retangular(dados, diametro_mm, nx, ny, d_linha)
        elif "circular" in tipo_secao.lower():
            # Dados gerais
            diam = diametro if diametro else hx # Diâmetro da barra
            n_barras_calc = n_barras if n_barras else nx # Quantidade de barras 
            # Selecionando se a seção é vazada
            if "vazada" in tipo_secao.lower():
                self.configurar_secao_circular_vazada(dados, diam, tipo_vinculacao, interno=interno)
            else:
                self.configurar_secao_circular(dados, diam, tipo_vinculacao)

            # Monta armadura circular
            self._montar_armadura_circular(dados, diametro_mm, n_barras_calc, d_linha)
        else:
            raise ValueError(f"Tipo de seção '{tipo_secao}' não suportado")
        
        self._esbeltez(self.dados)


        if esforcos:
            self.adicionar_esforcos(dados, esforcos)
            n_comb = len(esforcos)
        else:
            # Esforço dummy para inicializar
            self.adicionar_esforcos(dados, [(0, 0, 0, 0, 0)])
            n_comb = 1

        dados.erros.iniciarErros(n_comb)
        
        # CALCULA ENVOLTÓRIA (sequência do método verifica())
        self.DiscretizaSecao(dados)
        self.CurvaMr(dados)
       
        # SE tiver esforços, calcula FS também
        if esforcos:
            self.CalculaMomCurv(dados)
            self.CalculaEsforcos(dados)
            self.CalculaFs(dados)
            self.CalculaFsMomentoMin(dados) 

        return self._extrair_envoltoria(dados)
    

    def _extrair_envoltoria(self, dados: Any) -> Dict[str, Any]:
        """
        Extrai os dados da envoltória calculada
        
        Args:
            dados: Objeto Dados com resultados
            
        Returns:
            Dicionário com pontos da envoltória e informações da armadura
        """
        resultado = {
            'sucesso': True,
            'armadura': {},
            'envoltoria_nrd_mrdx': [],
            'envoltoria_nrd_mrdy': [],
            'curvas_mr': []
        }
        
        # Informações da armadura
        lista_as = dados.armacao.getAs()
        armadura_info = {
            'diametro_mm': dados.armacao.getFi() * 10.0,
            'area_total_cm2': dados.armacao.getAreaAs(),
            'n_barras': lista_as.size(),
            'nx': dados.armacao.getNx(),
            'ny': dados.armacao.getNy(),
            'd_linha_cm': dados.armacao.getDL(),
            'posicoes': []
        }
        
        for barra in lista_as:
            armadura_info['posicoes'].append({
                'x_cm': float(barra[0]),
                'y_cm': float(barra[1]),
                'area_cm2': float(barra[2]),
                'diametro_cm': float(barra[3])
            })
        
        resultado['armadura'] = armadura_info
        
        # Extrai envoltória Nrd x Mrdx
        curvas_nrd_mrdx = dados.resultados.getCurvasNrdMrdx()
        #print(f"DEBUG: tipo = {type(curvas_nrd_mrdx)}")
        #print(f"DEBUG: tamanho = {curvas_nrd_mrdx.size() if hasattr(curvas_nrd_mrdx, 'size') else len(curvas_nrd_mrdx)}")
        if curvas_nrd_mrdx and curvas_nrd_mrdx.size() > 0:
            pontos_x = []
            for i in range(curvas_nrd_mrdx.size()):
                        ponto = curvas_nrd_mrdx.get(i)  # ponto = [Nrd, Mrd]
                        pontos_x.append({
                            'nrd_tf': float(ponto[0]),
                            'mrd_tfm': float(ponto[1])
                        })
            resultado['envoltoria_nrd_mrdx'] = pontos_x
      
        # Extrai envoltória Nrd x Mrdy
        curvas_nrd_mrdy = dados.resultados.getCurvasNrdMrdy()
        if curvas_nrd_mrdy and curvas_nrd_mrdy.size() > 0:
            pontos_y = []
            for i in range(curvas_nrd_mrdy.size()):
                curva_y = curvas_nrd_mrdy.get(i)
                pontos_y.append({
                    'nrd_tf': float(ponto[0]),
                    'mrd_tfm': float(ponto[1])
                })
            resultado['envoltoria_nrd_mrdy'] = pontos_y
        
        # Extrai curvas Mr completas (N, teta, Mx, My)
        curvas_mr = dados.resultados.getCurvasMr()
        if curvas_mr and curvas_mr.size() > 0:
            curva = curvas_mr.get(0)
            pontos_mr = []
            
            n_pontos = len(curva[0])
            for i in range(n_pontos):
                pontos_mr.append({
                    'nrd_tf': float(curva[0][i]),
                    'teta_rad': float(curva[1][i]),
                    'mx_tfm': float(curva[3][i]),
                    'my_tfm': float(curva[2][i])
                })
            
            resultado['curvas_mr'] = pontos_mr
        # Pega FS de cada combinação
        try:
            esforcos_obj = dados.resultados.getesforcos()
            if esforcos_obj:
                
                list_fs = esforcos_obj[5]  # índice 5 = lista de FS
                resultado['fs_por_combinacao'] = []
                for i in range(list_fs.size()):
                    fs_comb = list_fs.get(i)
                    resultado['fs_por_combinacao'].append([float(x) for x in fs_comb])
            
            resultado['fs_min'] = float(dados.resultados.getFsMin())
            resultado['comb_fs_min'] = int(dados.resultados.getCombFsMin())
        except Exception as e:
            print(f"Aviso: Não foi possível extrair FS - {e}")
        
        return resultado
    

    def debug_completo_2ord(self, dados):
        """
        Coleta TODOS os dados intermediários do cálculo de 2ª ordem
        """
        print("\n" + "="*80)
        print("DEBUG COMPLETO - CÁLCULO DE 2ª ORDEM")
        print("="*80)
        
        # ========== 1. CONFIGURAÇÕES ==========
        print("\n### 1. CONFIGURAÇÕES ###")
        print(f"fck = {dados.config.getFck():.6f} tf/cm²")
        print(f"fyk = {dados.config.getFyk():.6f} tf/cm²")
        print(f"Es = {dados.config.getModEs():.2f} tf/cm²")
        print(f"γC = {dados.config.getGamaC()}")
        print(f"γS = {dados.config.getGamaS()}")
        print(f"γF = {dados.config.getGamaF()}")
        print(f"γF3 = {dados.config.getGamaF3()}")
        print(f"Método 2ª ordem = {dados.config.getMetodoSegOrd()}")
        print(f"Calcular 2ª ordem = {dados.config.getCalcular2ord()}")
        print(f"Considerar fluência = {dados.config.getConsiderarFluencia()}")
        print(f"Limitar Mb = {dados.config.getLimMb()}")
        print(f"Lim momento mín = {dados.config.getLimMomentoMin()}")
        print(f"NGraficoMomCurv = {dados.config.getNGraficoMomCurv()}")

        # ========== 2. GEOMETRIA ==========
        print("\n### 2. GEOMETRIA ###")
        print(f"Tipo seção = {dados.secao.getTipoSecao()}")
        print(f"hx (D) = {dados.secao.getHx()} cm")
        print(f"hy (d) = {dados.secao.getHy()} cm")
        print(f"L = {dados.secao.getL()} cm")
        print(f"Tipo vinculação = {dados.secao.getTipoVinculacao()}")
        print(f"Área concreto = {dados.secao.getAreaAc():.2f} cm²")
        print(f"Ix = {dados.secao.getIX():.2e} cm⁴")
        print(f"Iy = {dados.secao.getIY():.2e} cm⁴")
        print(f"λx = {dados.secao.getLambdaX():.2f}")
        print(f"λy = {dados.secao.getLambdaY():.2f}")

        # ===== 3. ARMADURAS (igual ao PDF página 2) =====
        print("\n### 3. ARMADURAS ###")
        lista_as = dados.resultados.getSecaoS()  # Lista de armaduras
        
        print(f"{'Barra':<8} | {'φ (mm)':<8} | {'X (cm)':<10} | {'Y (cm)':<10} | {'As (cm²)':<10}")
        print("-" * 60)
        
        for i, barra in enumerate(lista_as):
            x = barra[0]  # Coordenada X
            y = barra[1]  # Coordenada Y
            area = barra[2]  # Área da barra
            diam = 3.2  # Diâmetro
            
            print(f"{i+1:<8} | {diam*10:<8.1f} | {x:<10.2f} | {y:<10.2f} | {area:<10.4f}")


        # ========== 4. ESFORÇOS ENTRADA ==========
        print("\n### 4. ESFORÇOS DE ENTRADA (Comb 0) ###")
        esf_entrada = list(dados.esforcos.getListaEsforcos()[0])
        print(f"N = {esf_entrada[0]:.4f} tf")
        print(f"Mx_topo = {esf_entrada[1]:.4f} tf.m")
        print(f"My_topo = {esf_entrada[2]:.4f} tf.m")
        print(f"Mx_base = {esf_entrada[3]:.4f} tf.m")
        print(f"My_base = {esf_entrada[4]:.4f} tf.m")
        
        # ========== 5. ECI e propriedades calculadas ==========
        print("\n### 5. PROPRIEDADES CALCULADAS ###")
        # Calcular Eci (linha 54 de CalculaEsforcos)
        import math
        fck_mpa = dados.config.getFck() / 0.010197  # Converter de volta para MPa
        eci = 5600.0 * math.sqrt(fck_mpa)
        print(f"Eci = {eci:.2f} MPa = {eci*0.010197:.2f} tf/cm²")
        
      
        
        # ========== 7. EI SECANTE ==========
        print("\n### 7. EI SECANTE X  ###")
        ei_sec_x1 = dados.resultados.getEiSecX1()
        ei_sec_y1 = dados.resultados.getEiSecY1()
        print("Seção |     EI     |   M usado   |      φ")
        print("------|------------|-------------|------------")
        for i in range(len(ei_sec_x1)):
            ei_x1 = list(ei_sec_x1[i])
            print(f"{i+1:5} | {ei_x1[0]:.4e} |   {ei_x1[1]:.4f}  | {ei_x1[2]:.6e}")

        print("\n### 7. EI SECANTE Y  ###")
        print("Seção |     EI     |   M usado   |      φ")
        print("------|------------|-------------|------------")
        for i in range(len(ei_sec_x1)):
            ei_y1 = list(ei_sec_y1[i])
            print(f"{i+1:5} | {ei_y1[0]:.4e} |   {ei_y1[1]:.4f}  | {ei_y1[2]:.6e}")

        print("\n### 8. MOMENTOS 1ª ORDEM (Comb 0) ###")
        esforcos_obj = dados.resultados.getesforcos()
        nsd = esforcos_obj[0][0]
        msxd = list(esforcos_obj[1][0])
        msyd = list(esforcos_obj[2][0])
        
        print(f"Nsd = {nsd:.4f} tf (= N × γF = {esf_entrada[0]:.4f} × {dados.config.getGamaF()})")
        
        print("\nDistribuição Mx1d ao longo do pilar:")
        print("Seção |  z (cm)  |   1/r   |     EI    | Mx1d (tf.m) | Mx2d (tf.m)")
        print("------|----------|---------|-----------|-------------|------------")
        L = dados.secao.getL()
        n_secoes = len(msxd)

        mxd2 = list(esforcos_obj[3])[0]
        myd2 = list(esforcos_obj[4])[0]

        for i in range(n_secoes):
            z = i * L / (n_secoes - 1)

            resEI = self.ELS().ELS(dados, 
                                esf_entrada[0]/dados.config.getGamaF3(),        
                                mxd2[i]/dados.config.getGamaF3(), 
                                myd2[i]/dados.config.getGamaF3(), 
                                True, 
                                1.1)
            print(f"{i+1:5} | {z:8.2f} | {round(resEI[5], 3):7.2f} | {round(resEI[7]/dados.unidades.getCUnEsforcos(1.0), 2):7.2f} | {msxd[i]:11.4f} | {mxd2[i]:11.4f}")
        
        # ========== 9. MOMENTOS TOTAIS (1ª + 2ª) ==========
        print("\n### 9. MOMENTOS TOTAIS - 1ª + 2ª ORDEM (Comb 0) ###")
        msxd2 = list(esforcos_obj[3][0])
        msyd2 = list(esforcos_obj[4][0])
        
        print("Seção |  Mx1d   |  Mxtot  |  M2d    | Amplif")
        print("------|---------|---------|---------|--------")
        for i in range(n_secoes):
            m1d = msxd[i]
            mtot = msxd2[i]
            m2d = mtot - m1d
            amp = mtot/m1d if abs(m1d) > 0.01 else 0
            print(f"{i+1:5} | {m1d:7.2f} | {mtot:7.2f} | {m2d:7.2f} | {amp:6.2f}x")


        print("Seção |  Mx1d   |  Mxtot  |  M2d    | Amplif")
        print("------|---------|---------|---------|--------")
        



        # Quando você pega o EI:
        """alphaB = self.alphaB(dados.secao.getTipoVinculacao(), esf_entrada[1], -esf_entrada[3]).getMa()

        ei_bruto = dados.resultados.getEIsec(0, alphaB, "x")

        # Ele precisa ser convertido para exibição:
        fator_conversao = dados.unidades.getCUnEsforcos(1.0)
        ei_em_kNm2 = ei_bruto / fator_conversao

        print(f"EI bruto: {ei_bruto}")
        print(f"Fator conversão: {fator_conversao}")
        print(f"EI em kN.m²: {ei_em_kNm2}")"""
                
      
        
        print("\n" + "="*80)


    def extrair_dados_para_graficos(self, dados, comb_idx=0):
        """
        Extrai todos os dados que aparecem na interface gráfica
        """
        print("\n" + "="*80)
        print(f"DADOS PARA GRÁFICOS - COMBINAÇÃO {comb_idx + 1}")
        print("="*80)
        
        # 1. CURVA MR (Diagrama de Interação)
        print("\n### CURVA MR (Envoltória) ###")
        curvasMr = dados.resultados.getCurvasMr()
        curva = curvasMr[comb_idx]
        
        nrd = list(curva[0])
        theta = list(curva[1])
        mrx = list(curva[2])
        mry = list(curva[3])
        
        print(f"Número de pontos: {len(nrd)}")
        print("\nPrimeiros 5 pontos:")
        print("   Nrd    |   Theta  |   Mrx   |   Mry")
        print("-----------+----------+---------+---------")
        for i in range(min(5, len(nrd))):
            print(f"{nrd[i]:9.2f} | {theta[i]:8.4f} | {mrx[i]:7.2f} | {mry[i]:7.2f}")
        
        # 2. MOMENTOS AO LONGO DO PILAR
        print("\n### MOMENTOS AO LONGO DO PILAR ###")
        esforcos = dados.resultados.getesforcos()
        
        mx1d = list(esforcos[1][comb_idx])
        my1d = list(esforcos[2][comb_idx])
        mxtot = list(esforcos[3][comb_idx])
        mytot = list(esforcos[4][comb_idx])
        fsi = list(esforcos[5][comb_idx])
        
        n_secoes = len(mx1d)
        L = dados.secao.getL()
        
        print(f"Número de seções: {n_secoes}")
        print(f"Altura total: {L} cm")
        print("\nSeção |  Altura  | Mx1d   | Mxtot  | My1d   | Mytot   | FS")
        print("------|----------|--------|--------|--------|--------|--------")
        for i in range(n_secoes):
            z = i * L / (n_secoes - 1)
            print(f"{i+1:5} | {z:8.2f} | {mx1d[i]:6.2f} | {mxtot[i]:6.2f} | "
                f"{my1d[i]:6.2f} | {mytot[i]:6.2f} | {fsi[i]:6.2f}")
        

        
        # 4. PONTO DO ESFORÇO SOLICITANTE (para plotar no diagrama)
        print("\n### ESFORÇO SOLICITANTE (para plotar) ###")
        esf_original = dados.esforcos.getListaEsforcos()[comb_idx]
        nsd = esforcos[0][comb_idx]
        
        # Pegar momento máximo ao longo do pilar
        mx_max = max(mxtot, key=abs)
        my_max = max(mytot, key=abs)
        
        print(f"Nsd = {nsd:.2f} tf")
        print(f"Mx máximo = {mx_max:.2f} tf.m")
        print(f"My máximo = {my_max:.2f} tf.m")
        
        # 5. FATOR DE SEGURANÇA
        print("\n### FATOR DE SEGURANÇA ###")
        fs_lista = list(esforcos[5][comb_idx])
        theta_lista = list(esforcos[6][comb_idx])
        
        fs_min = min(fs_lista)
        idx_fs_min = fs_lista.index(fs_min)
        
        print(f"FS mínimo: {fs_min:.2f} (seção {idx_fs_min + 1})")
        print(f"Theta correspondente: {theta_lista[idx_fs_min]:.4f} rad")
        
        print("\n" + "="*80)
        

    def dimensionar(self, dados: Any) -> Any:
        """Executa o dimensionamento (para uso com método calcular)"""
        self.Dimensiona(dados)
        return dados
        

    def extrair_resultados_dimensionamento(self, dados: Any) -> Dict[str, Any]:
        """Extrai os resultados do dimensionamento"""
        resultados = {
            'sucesso': False,
            'armaduras': [],
            'custo_minimo_idx': -1,
            'erros': []
        }
        
        resultados['custo_minimo_idx'] = dados.resultados.getCustoMin()
        resultado_as = dados.resultados.getResultadoAs()
        
        for i, item in enumerate(resultado_as):
            if item[0] is not None:
                armadura_info = {
                    'diametro': float(item[1]),
                    'n_barras_x': int(item[2]) if item[2] is not None else 0,
                    'n_barras_y': int(item[3]) if item[3] is not None else 0,
                    'd_linha': float(item[4]),
                    'status': str(item[5]) if item[5] else "OK",
                    'posicoes': []
                }
                
                lista_as = item[0]
                for barra in lista_as:
                    armadura_info['posicoes'].append({
                        'x': float(barra[0]),
                        'y': float(barra[1]),
                        'area': float(barra[2]),
                        'diametro': float(barra[3])
                    })
                
                area_total = sum(pos['area'] for pos in armadura_info['posicoes'])
                armadura_info['area_total'] = area_total
                armadura_info['n_barras_total'] = len(armadura_info['posicoes'])
                
                resultados['armaduras'].append(armadura_info)
                
                if i == resultados['custo_minimo_idx']:
                    resultados['sucesso'] = True
            else:
                resultados['armaduras'].append(None)
        
        resultados['fs_min'] = float(dados.resultados.getFsMin())
        resultados['comb_fs_min'] = int(dados.resultados.getCombFsMin())
        resultados['fs_min_momento'] = float(dados.resultados.getFsMi())
        
        n_comb = dados.esforcos.getNComb()
        for i in range(n_comb):
            erro_nrd = dados.erros.getListaErroNrd(i)
            erro_2ord = dados.erros.getLista2Ord(i)
            erro_mmin = dados.erros.getLista2OrdMmin(i)
            
            if erro_nrd or erro_2ord or erro_mmin:
                resultados['erros'].append({
                    'combinacao': i,
                    'erro_nrd': str(erro_nrd) if erro_nrd else None,
                    'erro_2ord': str(erro_2ord) if erro_2ord else None,
                    'erro_mmin': str(erro_mmin) if erro_mmin else None
                })
        
        return resultados
    


def salvar_resultados_json(resultados: List[Dict], arquivo: str):
    """Salva resultados em arquivo JSON"""
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"Resultados salvos em: {arquivo}")


def carregar_casos_json(arquivo: str) -> List[Dict]:
    """Carrega casos de um arquivo JSON"""
    with open(arquivo, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    print("Wrapper PCalc Completo carregado com sucesso!")
    print("\nMétodos disponíveis:")
    print("  - calcular_envoltoria(): Calcula envoltória com armadura definida")
    print("  - calcular(): Dimensiona armadura para esforços dados")
    print("  - calcular_batch(): Processa múltiplos casos")