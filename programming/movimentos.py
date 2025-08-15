# Funções de movimento e controle de motores
"""
Módulo de movimentos do robô OBR.
Inclui funções assíncronas para giros e deslocamentos com correção de heading.
"""
from typing import Any, Callable
from pybricks.parameters import Color
from pybricks.tools import wait, multitask

async def gyro_turn(
    graus: float,
    MTZZ: Any,
    motoresquerdo: Any,
    motordireito: Any,
    PID: Callable,
    redefinir_pid: Callable,
    zerar_heading_residual: Callable,
    GYRO_TOL: float,
    GYRO_MIN: float,
    GYRO_MAX: float
) -> None:
    """
    Realiza um giro preciso usando o IMU, com correção residual ao final.
    """
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
        potencia = int(min(GYRO_MAX, max(GYRO_MIN, abs(erro))))
        if erro > 0:
            motordireito.dc(-potencia)
            motoresquerdo.dc(potencia)
        else:
            motordireito.dc(potencia)
            motoresquerdo.dc(-potencia)
    motordireito.brake()
    motoresquerdo.brake()
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
    zerar_heading_residual(alvo)

async def Gyro_Move(
    rotacoes: float,
    velocidade_final: float,
    MTZZ: Any,
    motoresquerdo: Any,
    motordireito: Any,
    PID: Callable,
    redefinir_pid: Callable,
    zerar_heading_residual: Callable,
    reverso: bool = False
) -> None:
    """
    Move o robô em linha reta por um número de rotações, corrigindo o heading.
    """
    await redefinir_pid()
    motoresquerdo.reset_angle(0)
    await wait(0)
    alvo_heading = 0
    velocidade_final = abs(velocidade_final)
    velocidade_atual = 30
    incremento = 2
    desacelera_a_partir = 0.8 * abs(rotacoes)
    sinal = -1 if reverso else 1
    corr_sinal = -1 if reverso else 1
    motoresquerdo.dc(sinal * (velocidade_atual + corr_sinal * 0))
    motordireito.dc(sinal * (velocidade_atual - corr_sinal * 0))
    while True:
        rot_atual = abs(motoresquerdo.angle() / 360)
        if rot_atual >= abs(rotacoes):
            break
        erro = ((alvo_heading - MTZZ.imu.heading() + 540) % 360) - 180
        await PID(8.5, 0.002, 0.025)
        if rot_atual < 0.3 * abs(rotacoes):
            if velocidade_atual < velocidade_final:
                velocidade_atual += incremento
        elif rot_atual > desacelera_a_partir:
            velocidade_atual -= incremento
            if velocidade_atual < 50:
                velocidade_atual = 50
        if reverso:
            pot_esq = sinal * (velocidade_atual - 0)
            pot_dir = sinal * (velocidade_atual + 0)
        else:
            pot_esq = sinal * (velocidade_atual + 0)
            pot_dir = sinal * (velocidade_atual - 0)
        motoresquerdo.dc(pot_esq)
        motordireito.dc(pot_dir)
    motoresquerdo.brake()
    motordireito.brake()
    erro_residual = ((alvo_heading - MTZZ.imu.heading() + 540) % 360) - 180
    if abs(erro_residual) > 0.05:
        pulso_pot = 15
        pulso_tempo = 80
        if erro_residual > 0:
            motordireito.dc(-pulso_pot)
            motoresquerdo.dc(pulso_pot)
        else:
            motordireito.dc(pulso_pot)
            motoresquerdo.dc(-pulso_pot)
        await wait(pulso_tempo)
        motoresquerdo.brake()
        motordireito.brake()
    zerar_heading_residual(alvo_heading)

async def Gyro_Move_Infinito(velocidade_final, MTZZ, motoresquerdo, motordireito, sensor_frente, sensor_direito, sensor_esquerdo, PID, redefinir_pid, zerar_heading_residual, is_verdefrente, is_brancofrente, is_vermelhofrente, is_pretoresgate, reverso=False):
    await redefinir_pid()
    motoresquerdo.reset_angle(0)
    await wait(0)
    alvo_heading = 0
    velocidade_final = abs(velocidade_final)
    velocidade_atual = 30
    incremento = 2
    velocidade_maxima = velocidade_final
    velocidade_minima = 35
    while True:
        hsv = await sensor_frente.hsv()
        if is_verdefrente(hsv) or is_brancofrente(hsv) or is_vermelhofrente(hsv) or (is_pretoresgate(await sensor_direito.hsv()) and is_pretoresgate(await sensor_esquerdo.hsv())):
            break
        erro = ((alvo_heading - MTZZ.imu.heading() + 540) % 360) - 180
        await PID(7.5, 0.002, 0.025)
        if velocidade_atual < velocidade_maxima:
            velocidade_atual += incremento
        velocidade_atual = max(velocidade_minima, min(velocidade_atual, velocidade_maxima))
        if reverso:
            motoresquerdo.dc(-(velocidade_atual + 0))
            motordireito.dc(-(velocidade_atual - 0))
        else:
            motoresquerdo.dc(velocidade_atual + 0)
            motordireito.dc(velocidade_atual - 0)
        await wait(10)
    motoresquerdo.brake()
    motordireito.brake()
    erro_residual = ((alvo_heading - MTZZ.imu.heading() + 540) % 360) - 180
    if abs(erro_residual) > 0.05:
        pulso_pot = 15
        pulso_tempo = 80
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
    zerar_heading_residual(alvo_heading)

async def Gyro_Move_Ate_Colisao(velocidade_final, MTZZ, motoresquerdo, motordireito, PID, redefinir_pid, zerar_heading_residual, reverso=False):
    await redefinir_pid()
    motoresquerdo.reset_angle(0)
    await wait(0)
    alvo_heading = 0
    velocidade_atual = 45
    incremento = 1
    velocidade_maxima = abs(velocidade_final)
    velocidade_minima = 30
    paredecalc = 0
    sinal = -1 if reverso else 1
    while True:
        erro = ((alvo_heading - MTZZ.imu.heading() + 540) % 360) - 180
        await PID(2.5, 0.002, 0.025)
        if velocidade_atual < velocidade_maxima:
            velocidade_atual += incremento
        velocidade_atual = max(velocidade_minima, min(velocidade_maxima, velocidade_atual))
        if reverso:
            pot_esq = sinal * (velocidade_atual - 0)
            pot_dir = sinal * (velocidade_atual + 0)
        else:
            pot_esq = sinal * (velocidade_atual + 0)
            pot_dir = sinal * (velocidade_atual - 0)
        motoresquerdo.dc(pot_esq)
        motordireito.dc(pot_dir)
        vel_real_esq = motoresquerdo.speed()
        vel_real_dir = motordireito.speed()
        if abs(vel_real_esq) >= 360 or abs(vel_real_dir) >= 360:
            paredecalc = 5
        if reverso and (abs(vel_real_esq) >= 300 or abs(vel_real_dir) >= 300):
            paredecalc = 5
        if (
            (abs(vel_real_esq) < 360 and abs(vel_real_dir) < 360 and paredecalc == 5) or
            (abs(vel_real_esq) < 380 and abs(vel_real_dir) < 340 and paredecalc == 5) or
            (abs(vel_real_esq) < 340 and abs(vel_real_dir) < 380 and paredecalc == 5)
        ):
            break
        await wait(0)
    motoresquerdo.brake()
    motordireito.brake()
    await wait(1000)
    zerar_heading_residual(alvo_heading)

async def subir_garra(garra):
    await garra.run_angle(300, 160)

async def descer_garra(garra):
    await garra.run_angle(-300, 160)
# Funções de movimento do robô
# Exemplo: andar, girar, parar, etc.

def andar_frente():
    pass  # Implementar lógica

def girar_esquerda():
    pass

def girar_direita():
    pass

def parar():
    pass
