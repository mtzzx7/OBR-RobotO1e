# Funções de sensores e cor
def is_prata(hsv):
    h, s, v = hsv
    return 205 <= h <= 215 and s <= 30 and v >= 70

def is_verde(hsv):
    h, s, v = hsv
    return 95 <= h <= 165 and s >= 50 and v >= 40

def is_brancofrente(hsv):
    h, s, v = hsv
    return 195 <= h <= 200 and s <= 15 and v <= 90

def is_verdefrente(hsv):
    h, s, v = hsv
    return 150 <= h <= 165 and s <= 90 and v <= 35

def is_vermelhofrente(hsv):
    h, s, v = hsv
    return 345 <= h <= 350 and s <= 95 and v <= 30

def is_pretoresgate(hsv):
    h, s, v = hsv
    return 160 <= h <= 220 and s <= 30 and v <= 80
# Funções relacionadas aos sensores
# Exemplo: leitura de sensores, interpretação de cor, etc.

def ler_sensor_direito():
    pass

def ler_sensor_esquerdo():
    pass

def interpretar_cor(valor):
    pass
