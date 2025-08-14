print('oi alladin')
# -----------------------------------------
# CONFIGURAÇÃO E IMPORTAÇÕES
# -----------------------------------------
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Color, Direction, Port
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch

#DATA: 13/08 ---- 10 dias para a OBR

# -----------------------------------------
# Função utilitária de heading residual
# -----------------------------------------
def zerar_heading_residual(alvo):
    """
    Define o heading atual como o erro residual em relação ao alvo.
    Isso permite que o próximo movimento (Gyro_Move, por exemplo)
    corrija o desvio deixado pelo giro anterior.
    """
    erro_residual = ((MTZZ.imu.heading() - alvo + 540) % 360) - 180
    MTZZ.imu.reset_heading(erro_residual)
    print(f"[✔] Heading residual ajustado para: {erro_residual:.4f}°")


# -----------------------------------------
# CONSTANTES E PARÂMETROS GLOBAIS
# -----------------------------------------
MTZZ = PrimeHub()
sensor_esquerdo = ColorSensor(Port.C)
sensor_direito = ColorSensor(Port.D)
sensor_frente = ColorSensor(Port.E)
motoresquerdo = Motor(Port.B, Direction.CLOCKWISE)
motordireito = Motor(Port.A, Direction.COUNTERCLOCKWISE)
garra = Motor(Port.F, Direction.CLOCKWISE)
drive_base = DriveBase(motoresquerdo, motordireito, 56, 110)

# PID padrão do seguidor
pid_p = 3
pid_i = 0.002
pid_d = 0.016

# Parâmetros do gyro_turn
GYRO_TOL = 0.02    # Tolerância para giro (graus)
GYRO_MIN = 5      # Potência mínima
GYRO_MAX = 50      # Potência máxima
GYRO_RESET = True

# -----------------------------------------
# VARIÁVEIS GLOBAIS MUTÁVEIS
# -----------------------------------------
erro = 0
correcao = 0
integral = 0
derivada = 0
erro_final = 0
guinadarefmove = 0
guinadacalc = 0
method_stop = 0
method_up = 0
hsv_esquerdo = 0
hsv_direito = 0 
reflexao_esquerdo = 0
reflexao_direito = 0
prata_verify = 0
mapeamento_saida = 0
mapeamento_verde_detected = 0
mapeamento_loop_calc = 0
resgate_vitimas_finais = False
resgate_vitimas_esquerda = False
resgate_vitimas_direita = False

# -----------------------------------------
# FUNÇÕES AUXILIARES DE SENSOR/COR
# -----------------------------------------

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

# -----------------------------------------
# PID, PID ADAPTATIVO E UTILITÁRIOS
# -----------------------------------------
async def redefinir_pid():
    global erro_final, integral, derivada, correcao, erro
    erro_final = 0
    integral = 0
    derivada = 0
    correcao = 0
    erro = 0
    await wait(0)

async def PID(kp, ki, kd):
    global integral, derivada, correcao, erro_final, erro
    integral += erro
    derivada = erro - erro_final
    correcao = erro * kp + (integral * ki + derivada * kd)
    erro_final = erro
    await wait(0)

async def redefinir():
    global erro_final, integral, derivada, correcao, erro, method_stop, pid_p, pid_i, pid_d, guinadacalc, guinadarefmove
    await wait(0)
    erro_final = 0
    integral = 0
    derivada = 0
    correcao = 0
    erro = 0
    method_stop = 0
    pid_p = 3.30
    pid_i = 0.002
    pid_d = 0.016
    guinadacalc = MTZZ.imu.tilt()[1]
    guinadarefmove = MTZZ.imu.tilt()[1]








# -----------------------------------------
# GIRO UNIVERSAL COM RESIDUAL
# -----------------------------------------
async def gyro_turn(graus):
    global erro, integral, derivada, correcao, erro_final
    global GYRO_TOL, GYRO_MIN, GYRO_MAX

    

    await redefinir_pid()

    kp = 4
    ki = 0.0008
    kd = 0.16



    alvo = graus

    def erro_angular(alvo, atual):
        return ((alvo - atual + 540) % 360) - 180

    while abs(erro_angular(alvo, MTZZ.imu.heading())) > GYRO_TOL:
        erro = erro_angular(alvo, MTZZ.imu.heading())
        await PID(kp, ki, kd)
        potencia = int(min(GYRO_MAX, max(GYRO_MIN, abs(correcao))))
        if erro > 0:
            motordireito.dc(-potencia)
            motoresquerdo.dc(potencia)
        else:
            motordireito.dc(potencia)
            motoresquerdo.dc(-potencia)
    motordireito.brake()
    motoresquerdo.brake()

    # Correção fina
    erro_residual = erro_angular(alvo, MTZZ.imu.heading())
    if abs(erro_residual) > 0.5:
        pulso_pot = 15
        pulso_tempo = 70
        if erro_residual > 0:
            motordireito.dc(pulso_pot)
            motoresquerdo.dc(-pulso_pot)
        else:
            motordireito.dc(-pulso_pot)
            motoresquerdo.dc(pulso_pot)
        await wait(pulso_tempo)
        motordireito.brake()
        motoresquerdo.brake()

    # --- Zeragem residual após o giro ---
    zerar_heading_residual(alvo)



# -----------------------------------------
# SEGUIDOR DE LINHA (PID CLÁSSICO) e outros movimentos
# -----------------------------------------
async def seguidor(velocidade):
    global erro, pid_p, pid_i, pid_d, PID
    await wait(0)
    while True:
        erro = await sensor_direito.reflection() - await sensor_esquerdo.reflection()
        await PID(pid_p, pid_i, pid_d)
        motoresquerdo.dc(velocidade - correcao)
        motordireito.dc(velocidade + correcao)
        await subida()
        await obstaculo()
        await Green_Right()
        await pratax_resgate()
        await Green_Left()
        await multitask(wait(0))
        await wait(0)

# -----------------------------------------
# GYRO_MOVE COM AJUSTE RESIDUAL NO FINAL
# -----------------------------------------
async def Gyro_Move(rotacoes, velocidade_final, reverso=False):
    global erro, correcao
    await redefinir_pid()
    motoresquerdo.reset_angle(0)
    await wait(0)

    alvo_heading = 0

    # Configuração de aceleração
    velocidade_final = abs(velocidade_final)
    velocidade_atual = 30
    incremento = 2
    desacelera_a_partir = 0.8 * abs(rotacoes)

    sinal = -1 if reverso else 1
    corr_sinal = -1 if reverso else 1

    motoresquerdo.dc(sinal * (velocidade_atual + corr_sinal * correcao))
    motordireito.dc(sinal * (velocidade_atual - corr_sinal * correcao))

    while True:
        rot_atual = abs(motoresquerdo.angle() / 360)
        if rot_atual >= abs(rotacoes):
            break

        
        erro = ((alvo_heading - MTZZ.imu.heading() + 540) % 360) - 180

        if reverso:
            await PID(8.5, 0.002, 0.025)
        else:
            await PID(8.5, 0.002, 0.025)

        if rot_atual < 0.3 * abs(rotacoes):
            if velocidade_atual < velocidade_final:
                velocidade_atual += incremento
        elif rot_atual > desacelera_a_partir:
            velocidade_atual -= incremento
            if velocidade_atual < 50:
                velocidade_atual = 50

        if reverso:
            pot_esq = sinal * (velocidade_atual - correcao)
            pot_dir = sinal * (velocidade_atual + correcao)
        else:
            pot_esq = sinal * (velocidade_atual + correcao)
            pot_dir = sinal * (velocidade_atual - correcao)

        motoresquerdo.dc(pot_esq)
        motordireito.dc(pot_dir)


    motoresquerdo.brake()
    motordireito.brake()

    
    erro_residual = ((alvo_heading - MTZZ.imu.heading() + 540) % 360) - 180

    if abs(erro_residual) > 0.05:
        pulso_pot = 15
        pulso_tempo = 80
        print(f"Corrigindo heading final: erro = {erro_residual:.2f}°")

        if erro_residual > 0:
            motordireito.dc(-pulso_pot)
            motoresquerdo.dc(pulso_pot)
        else:
            motordireito.dc(pulso_pot)
            motoresquerdo.dc(-pulso_pot)

        await wait(pulso_tempo)
        motoresquerdo.brake()
        motordireito.brake()

    print("✅ Gyro_Move concluído. Heading atual:", MTZZ.imu.heading())
    zerar_heading_residual(alvo_heading)


async def Gyro_Move_Infinito(velocidade_final, reverso=False):
    global erro, correcao
    """
    Anda para frente infinitamente corrigindo a direção com IMU,
    até que o sensor frontal detecte verde, branco ou vermelho (HSV).
    """

    await redefinir_pid()
    motoresquerdo.reset_angle(0)
    await wait(0)

     
    alvo_heading = 0

    print("Gyro_Move_Infinito iniciado. Alvo =", alvo_heading)

    # Configurações iniciais
    velocidade_final = abs(velocidade_final)
    velocidade_atual = 30
    incremento = 2
    velocidade_maxima = velocidade_final
    velocidade_minima = 35

    while True:
        # Verifica HSV frontal
        hsv = await sensor_frente.hsv()
        if is_verdefrente(hsv) or is_brancofrente(hsv) or is_vermelhofrente(hsv) or is_pretoresgate(await sensor_direito.hsv()) and is_pretoresgate(await sensor_esquerdo.hsv()):
            print("[✅] Cor de parada detectada:", hsv)
            break

        # Correção com PID baseado no heading inicial
        erro = ((alvo_heading - MTZZ.imu.heading() + 540) % 360) - 180
        await PID(7.5, 0.002, 0.025)

        # Aceleração progressiva
        if velocidade_atual < velocidade_maxima:
            velocidade_atual += incremento

        velocidade_atual = max(velocidade_minima, min(velocidade_atual, velocidade_maxima))
        print("heading:", MTZZ.imu.heading())
        # Aplicação nos motores
        if reverso:
            motoresquerdo.dc(-(velocidade_atual + correcao))
            motordireito.dc(-(velocidade_atual - correcao))
        else:
            motoresquerdo.dc(velocidade_atual + correcao)
            motordireito.dc(velocidade_atual - correcao)

        await wait(10)

    # Parada suave
    motoresquerdo.brake()
    motordireito.brake()

    # Correção de heading final 
    erro_residual = ((alvo_heading - MTZZ.imu.heading() + 540) % 360) - 180

    if abs(erro_residual) > 0.05:
        pulso_pot = 15
        pulso_tempo = 80
        print(f"[🛠️] Corrigindo heading final: erro residual = {erro_residual:.2f}°")

        if erro_residual > 0:
            motordireito.dc(-pulso_pot)
            motoresquerdo.dc(pulso_pot)
        else:
            motordireito.dc(pulso_pot)
            motoresquerdo.dc(-pulso_pot)

        await wait(pulso_tempo)
        motoresquerdo.brake()
        motordireito.brake()

    await wait(1000)
    print("[✅] Gyro_Move_Infinito concluído. Heading final:", MTZZ.imu.heading())
    zerar_heading_residual(alvo_heading)


async def subir_garra():
    await garra.run_angle(300, 160)

async def descer_garra():
    await garra.run_angle(-300, 160)


async def Gyro_Move_Ate_Colisao(velocidade_final, reverso=False):
    global erro, correcao
    await redefinir_pid()
    motoresquerdo.reset_angle(0)
    await wait(0)

    alvo_heading = 0
    print("🔃 Gyro_Move_Ate_Colisao iniciado. Heading alvo:", alvo_heading, "| Reverso:", reverso)

    velocidade_atual = 45
    incremento = 1
    velocidade_maxima = abs(velocidade_final)
    velocidade_minima = 30
    paredecalc = 0

    # Define o sinal com base no reverso
    sinal = -1 if reverso else 1

    while True:
        # Corrige heading baseado em IMU
        erro = ((alvo_heading - MTZZ.imu.heading() + 540) % 360) - 180
        await PID(2.5, 0.002, 0.025)
        
        # Aceleração progressiva
        if velocidade_atual < velocidade_maxima:
            velocidade_atual += incremento
        velocidade_atual = max(velocidade_minima, min(velocidade_maxima, velocidade_atual))

        
        if reverso:
            pot_esq = sinal * (velocidade_atual - correcao)
            pot_dir = sinal * (velocidade_atual + correcao)
        else:
            pot_esq = sinal * (velocidade_atual + correcao)
            pot_dir = sinal * (velocidade_atual - correcao)

        motoresquerdo.dc(pot_esq)
        motordireito.dc(pot_dir)

        # Velocidade real dos motores
        vel_real_esq = motoresquerdo.speed()
        vel_real_dir = motordireito.speed()
        print(vel_real_esq, vel_real_dir)
        # Inicia contagem para considerar colisão
        if abs(vel_real_esq) >= 360 or abs(vel_real_dir) >= 360:
            paredecalc = 5
        if reverso and (abs(vel_real_esq) >= 300 or abs(vel_real_dir) >= 300):
            paredecalc = 5

        


        # Detecção de colisão — mesma lógica serve pra frente e ré
        if (
            abs(vel_real_esq) < 360 and abs(vel_real_dir) < 360 and paredecalc == 5 or
            abs(vel_real_esq) < 380 and abs(vel_real_dir) < 340 and paredecalc == 5 or
            abs(vel_real_esq) < 340 and abs(vel_real_dir) < 380 and paredecalc == 5
        ):
            print("🧱 Colisão detectada! Parando.")
            break

        await wait(0)

    # Parada
    motoresquerdo.brake()
    motordireito.brake()

    
    await wait(1000)
    print("✅ Gyro_Move_Ate_Colisao concluído. Heading final:", MTZZ.imu.heading())
    zerar_heading_residual(alvo_heading)






#obstaculo seguidor
async def obstaculo():
    await wait(0)
    if await sensor_frente.color() == Color.WHITE:
        await drive_base.straight(-100)
        await gyro_turn(65)
        await drive_base.straight(100)
        
        while not await sensor_direito.color() == Color.NONE:
            await wait(0)
            motordireito.dc(86)

            motoresquerdo.dc(28)
            
            await multitask(
                wait(0),
            )


#verde esquerdo
async def Green_Left():
    if is_verde(await sensor_esquerdo.hsv()):
        drive_base.stop()
        await wait(500)
        await drive_base.straight(100)
        await gyro_turn(-90)
        await drive_base.straight(40)
        await redefinir()  # <- também limpa
        await redefinir_pid()
    

async def Green_Right():
    if is_verde(await sensor_direito.hsv()):
        drive_base.stop()
        await wait(500)
        await drive_base.straight(100)
        await gyro_turn(90)
        await drive_base.straight(40)
        await redefinir()  # <- aqui limpa o PID antes de voltar ao seguidor
        await redefinir_pid()
    




# subida / ladeira
async def subida():
    global method_up, prata_verify
    await wait(0)
    if MTZZ.imu.tilt()[1] < -6 and method_up == 0:
        prata_verify = 1
        await drive_base.straight(80)
        method_up = 10
        pid_p = 0.5 
        pid_i = 0
        pid_d = 0
        
        await descer_garra()
        await drive_base.straight(80)
        
        drive_base.stop()
        await wait(500)
    else:
        if MTZZ.imu.tilt()[1] > -4 and method_up == 10:
            drive_base.stop()
            method_up = 0
            pid_p = 3.30
            pid_i = 0.002
            pid_d = 0.016
            prata_verify = 0
            await subir_garra()
            drive_base.stop()
            await wait(500)


#VER PRATA ENTRADA DO RESGATE
async def pratax_resgate():
    global hsv_esquerdo, hsv_direito, reflexao_esquerdo, reflexao_direito, prata_verify
    await wait(0)
    
    # Obtenção dos valores HSV dos sensores
    hsv_esquerdo = await sensor_esquerdo.hsv()
    hsv_direito = await sensor_direito.hsv()

    # Obtenção da reflexão dos sensores
    reflexao_esquerdo = await sensor_esquerdo.reflection()
    reflexao_direito = await sensor_direito.reflection()

    # Definindo uma faixa de reflexão mínima para não confundir com outras superfícies
    limite_reflexao = 50  # Ajuste conforme necessário (quanto maior o valor, mais reflexiva precisa ser a superfície)

    # Verificando se ambos os sensores estão vendo prata e com reflexão adequada
    if is_prata(await sensor_esquerdo.hsv()) and is_prata(await sensor_direito.hsv()) and reflexao_esquerdo < limite_reflexao and reflexao_direito < limite_reflexao and prata_verify == 0:
        print("Ambos os sensores detectaram prata com reflexão adequada! Finalizando a execução...")
        raise SystemExit  # Finaliza o programa



# LOOP RESGATE ---------------------------------------------
async def resgate_dir():
    global resgate_vitimas_finais, resgate_vitimas_direita
    await Gyro_Move(1, 70)
    await gyro_turn(90)
    await Gyro_Move(0.7, 70)
    if is_brancofrente(await sensor_frente.hsv()):
        resgate_vitimas_finais = True
        resgate_vitimas_direita = True
    await gyro_turn(90)
    await Gyro_Move(1.6, 70, reverso=True)
    await Gyro_Move(0.5, 70)
    await Gyro_Move(0.4, 70, reverso=True)
    await descer_garra()
    await Gyro_Move_Ate_Colisao(70)
    await multitask(
        Gyro_Move(0.7, 70, reverso=True),
        subir_garra()
    )
    






async def resgate_esq():
    global resgate_vitimas_finais, resgate_vitimas_esquerda
    await Gyro_Move(1, 70)
    await gyro_turn(-90)
    await Gyro_Move(0.7, 70)
    if is_brancofrente(await sensor_frente.hsv()):
        resgate_vitimas_finais = True
        resgate_vitimas_esquerda = True
    await gyro_turn(-90)
    await Gyro_Move(1.6, 70, reverso=True)
    await Gyro_Move(0.5, 70)
    await Gyro_Move(0.4, 70, reverso=True)
    await descer_garra()
    await Gyro_Move_Ate_Colisao(70)
    await multitask(
        Gyro_Move(0.7, 60, reverso=True),
        subir_garra()
    )




async def cores_resgate_viradas():
    global mapeamento_saida, mapeamento_verde_detected, mapeamento_loop_calc
    hsv = await sensor_frente.hsv()
    if is_pretoresgate(await sensor_direito.hsv()) and is_pretoresgate(await sensor_esquerdo.hsv()):
        mapeamento_saida = mapeamento_loop_calc + 1
        
        await Gyro_Move(0.8, 60, reverso=True)
        await gyro_turn(-90)
        await Gyro_Move_Infinito(60)
    elif is_verdefrente(hsv):
        #fazer logica depois do verde detectado para outros fins...
        mapeamento_verde_detected = True
        
    elif is_vermelhofrente(hsv):
        await gyro_turn(-45)
        await Gyro_Move(0.8, 60)
        await gyro_turn(-45)
        await Gyro_Move_Infinito(60)
    elif is_brancofrente(hsv):
        await gyro_turn(-90)
        await Gyro_Move_Infinito(60)
        

async def resgate_procura():
    global resgate_vitimas_finais, resgate_vitimas_esquerda, resgate_vitimas_direita
    await Gyro_Move(0.4, 60, reverso=True)
    await gyro_turn(-45)
    await Gyro_Move(0.6, 60, reverso=True)
    await descer_garra()
    await Gyro_Move(1.2, 60)
    await gyro_turn(-135)
    await Gyro_Move_Ate_Colisao(60)
    await multitask(
        Gyro_Move(1.0, 60, reverso=True),
        subir_garra()
        )
    while not resgate_vitimas_finais == True:
        if resgate_vitimas_finais == False:
            await resgate_dir()
        if resgate_vitimas_finais == False:
            await resgate_esq()
    if resgate_vitimas_esquerda == True:
        await Gyro_Move(1.2, 60)
        await gyro_turn(45)
    else:
        await Gyro_Move_Ate_Colisao(60, reverso=True)
        await gyro_turn(-135)
    await Gyro_Move_Ate_Colisao(60, reverso=True)
    await Gyro_Move(0.7, 60)
    await Gyro_Move_Ate_Colisao(80, reverso=True)
    await gyro_turn(90)
    await Gyro_Move(1.2, 60)
    await gyro_turn(-45)
    await Gyro_Move_Infinito(80)



async def resgate_principal_loop():
    global mapeamento_saida, mapeamento_verde_detected, mapeamento_loop_calc
    #primeiro movimento ao entrar na area de resgate
    await Gyro_Move(0.5, 60)
    #vira pra esquerda
    await gyro_turn(90)
    #procura a parede/ verde/ vermelho
    await Gyro_Move_Infinito(60)
    while not mapeamento_verde_detected == True:
        mapeamento_loop_calc += 1
        await cores_resgate_viradas()
    await resgate_procura()
        




# -----------------------------------------
# AREA DE INICIAR A PROGRAMAÇÃO = MAIN
# -----------------------------------------
async def main():
    await resgate_principal_loop()
    





    # -----------------------------------------------------------------------------------
    # FALTA IMPLEMENTAR O PROCURAR A SAIDA NOS LOOPS DE CAÇAR AS BOLINHASSS !!!!!!!!!!!!!
    # -----------------------------------------------------------------------------------
    '''await Gyro_Move(0.4, 60, reverso=True)
    await gyro_turn(-45)
    await Gyro_Move(0.6, 60, reverso=True)
    await descer_garra()
    await Gyro_Move(1.2, 60)
    await gyro_turn(-135)
    await Gyro_Move_Ate_Colisao(60)
    await multitask(
        Gyro_Move(1.0, 60, reverso=True),
        subir_garra()
        )
    await resgate_dir()
    await resgate_esq()
    await resgate_dir()
    await resgate_esq()
    await resgate_dir()
    await resgate_esq()'''
    
        
    

run_task(main())

# -----------------------------------------------------------------------------------------
# É OBRIGATÓRIO TER run_task(main()) FECHANDO A PROGRAMAÇÃO PARA INICIAR A PROGRAMAÇÃO
# -----------------------------------------------------------------------------------------
