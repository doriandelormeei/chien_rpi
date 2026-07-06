import RPi.GPIO as GPIO
import time
from gpiozero import Servo
from gpiozero.tones import Tone

# Configuration GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# ═══════════════════════════════
# PARTIE STEPPER 28BYJ-48
# ═══════════════════════════════
IN1 = 14
IN2 = 27
IN3 = 26
IN4 = 25

PAS           = 1024   # 1024 = 180°, 2048 = 360°
STEPS_PER_REV = 2048
VITESSE_STEP  = 0.001  # secondes entre chaque pas (plus petit = plus rapide)

GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

# Séquence demi-pas pour 28BYJ-48
sequence = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1],
]

pins = [IN1, IN2, IN3, IN4]
step_index = 0

def moteur_pas(nombre_pas, direction=1):
    global step_index
    for _ in range(abs(nombre_pas)):
        step_index = (step_index + direction) % len(sequence)
        for i, pin in enumerate(pins):
            GPIO.output(pin, sequence[step_index][i])
        time.sleep(VITESSE_STEP)

def moteur_stop():
    for pin in pins:
        GPIO.output(pin, 0)

# ═══════════════════════════════
# PARTIE SERVO SG90
# ═══════════════════════════════
PIN_SG90    = 33  # ⚠️ adaptez selon votre brochage RPi (GPIO BCM)
ANGLE_CIBLE = 48
VITESSE     = 0.001  # secondes entre chaque degré

# Conversion angle → duty cycle pour RPi PWM
# SG90 : 500µs (0°) à 2400µs (180°) sur période 20ms (50Hz)
def angle_vers_duty(angle):
    pulse_min = 0.5   # ms
    pulse_max = 2.4   # ms
    pulse = pulse_min + (pulse_max - pulse_min) * angle / 180
    return pulse / 20.0 * 100  # % duty cycle

pwm_servo = GPIO.PWM(PIN_SG90, 50)  # 50Hz
pwm_servo.start(angle_vers_duty(18))
position_actuelle = 18
time.sleep(0.5)

print(f"Prêt — servo à 18°, cible : {ANGLE_CIBLE}°")

def aller_vers(angle_cible):
    global position_actuelle
    direction = 1 if angle_cible > position_actuelle else -1

    while position_actuelle != angle_cible:
        position_actuelle += direction
        pwm_servo.ChangeDutyCycle(angle_vers_duty(position_actuelle))
        print(f"Angle : {position_actuelle}°")
        time.sleep(VITESSE)

    print(f"Position atteinte : {position_actuelle}°")

# ═══════════════════════════════
# BOUCLE PRINCIPALE
# ═══════════════════════════════
try:
    while True:
        # Stepper aller
        print("Stepper → sens horaire")
        moteur_pas(PAS, direction=1)
        moteur_stop()
        time.sleep(0.1)

        # Stepper retour
        print("Stepper → sens anti-horaire")
        moteur_pas(PAS, direction=-1)
        moteur_stop()
        time.sleep(0.1)

        # Servo
        if position_actuelle == 0:
            print(f"→ Aller à {ANGLE_CIBLE}°")
            aller_vers(ANGLE_CIBLE)
        else:
            print("→ Retour à 0°")
            aller_vers(0)

        time.sleep(0.02)

except KeyboardInterrupt:
    print("Arrêt du programme")

finally:
    pwm_servo.stop()
    moteur_stop()
    GPIO.cleanup()
    print("GPIO nettoyé")