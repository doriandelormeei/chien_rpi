'''
 #     #                                             
 ##    #   ##   #####   ####  #  ####   ####  ###### 
 # #   #  #  #  #    # #    # # #      #      #      
 #  #  # #    # #    # #      #  ####   ####  #####  
 #   # # ###### #####  #      #      #      # #      
 #    ## #    # #   #  #    # # #    # #    # #      
 #     # #    # #    #  ####  #  ####   ####  ###### 
                                                                                
Créé le 01/07/2026
Chien-robot
'''
#Servo+Camera+StepMoteur+LED
import cv2
from picamera2 import Picamera2
import numpy as np
import pigpio
import time
import sounddevice as sd
import soundfile as sf
import random

# ═══════════════════════════════
# CONFIGURATION GPIO VIA PIGPIO
# ═══════════════════════════════
pi = pigpio.pi() #connexion locale au raspberry et à ses pins

if not pi.connected:
    print("Erreur : impossible de se connecter au démon pigpiod. Essayez de voir 'sudo systemctl start pigpiod'")
    exit()

#LED
p_red = 17
p_blue = 27
p_green = 22

pi.set_mode(p_red, pigpio.OUTPUT)
pi.set_mode(p_blue, pigpio.OUTPUT)
pi.set_mode(p_green, pigpio.OUTPUT)

#Microphone
DEVICE = "hw:3,0"  
BLOCK_SIZE = 1024        # taille des blocs lus (samples)
seuil = 0.11         # seuil sur amplitude RMS normalisée (0.0 à 1.0), à ajuster
limite = False

def audio_callback(indata, frames, time_info, status):
    """
    if status:
        print("Status:", status)
    """   
    rms = np.sqrt(np.mean(indata**2)) # Calcul du niveau racine carrée de la moyenne des carrés
    global limite
    print(f"RMS = {rms:.4f}", end="\r")
    if rms > seuil:
        limite = True
        print(f"[DEPASSEMENT]", end="\r")
    else:
        limite = False
        
flux_audio = sd.InputStream(device=DEVICE,channels=1,samplerate= 48000,
        blocksize=BLOCK_SIZE,dtype="float32",callback=audio_callback,)

#Speaker
def wouaf():
    chiffre = random.randint(1,9)
    schiffre = str(chiffre)
    data, samplerate = sf.read('audio/aboiement_5' + schiffre + '.wav')
    sd.play(data,samplerate)

# Minuteur
minuteur = 0
temps = time.time()
sablier = 0
temps_alerte = 0
fin_alerte = 0
mouv = 0
calm = 0


# STEPPER
IN1 = 23
IN2 = 18
IN3 = 24
IN4 = 25
PAS = 30
VITESSE_STEP = 0.005 #seconde de pause entre step

pins = [IN1, IN2, IN3, IN4]

# Configuration de l'action des pins du stepper
for pin in pins:
    pi.set_mode(pin, pigpio.OUTPUT)

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

step_index = 0

def moteur_pas(nombre_pas, direction=1):
    global step_index
    if direction == 0:
        time.sleep(0.01)
        return
    for _ in range(nombre_pas):
        step_index = (step_index + direction) % len(sequence)
        for i, pin in enumerate(pins):
            pi.write(pin, sequence[step_index][i])
        time.sleep(VITESSE_STEP)

def moteur_stop():
    for pin in pins:
        pi.write(pin, 0)

# SERVO
PIN_SG90 = 12
VITESSE  = 0.01
bark=0 #autorisation de mouvement

def angle_vers_us(angle):
    # pigpio utilise les microsecondes directement
    # 0° = 500us, 180° = 2500us
    pulse_min = 500
    pulse_max = 2500
    return int(pulse_min + (pulse_max - pulse_min) * angle / 180)

# Initialisation du servo avec un signal propre
position_actuelle = 54
pi.set_servo_pulsewidth(PIN_SG90, angle_vers_us(position_actuelle))
time.sleep(0.5)

def aller_vers(angle_cible):
    global position_actuelle
    direction = 1 if angle_cible > position_actuelle else -1
    while position_actuelle != angle_cible:
        position_actuelle += direction
        pi.set_servo_pulsewidth(PIN_SG90, angle_vers_us(position_actuelle))
        time.sleep(VITESSE)
    print(f"Servo — position atteinte : {position_actuelle}°")

# ═══════════════════════════════
# CONFIGURATION CAMÉRA
# ═══════════════════════════════
width  = 800
height = 600
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"format": "RGB888", "size": (width, height)}
)
picam2.configure(config)
picam2.start()

# Zone d'exclusion centrale
exclusion_w = int(width * 0.5)
exclusion_h = height
x_min = (width - exclusion_w) // 2
x_max = x_min + exclusion_w
y_min = 0
y_max = exclusion_h
centre_frame = width // 2
ZONE_MORTE   = 50  # pixels autour du centre sans correction

# Première frame
frame1 = picam2.capture_array()
frame2 = frame1.copy()
print("Détection démarrée — 'q' pour quitter")

# ═══════════════════════════════
# LED
# ═══════════════════════════════
def voyant(led=0):
    if led == 0:	#stop
        pi.write(p_red,0)
        pi.write(p_blue,0)
        pi.write(p_green,0)
    elif led == 1:	#run
        pi.write(p_red,0)
        pi.write(p_blue,0)
        pi.write(p_green,1)
    elif led == 2:	#ready
        pi.write(p_red,0)
        pi.write(p_blue,1)
        pi.write(p_green,0)
    elif led == 3:	#error
        pi.write(p_red,3)
        pi.write(p_blue,0)
        pi.write(p_green,0)



# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# BOUCLE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

try:
    with flux_audio:
        while True:
            #Activation voyant
            led = 2
            voyant(led)
            
            #Audio
            if limite is True:
                data, samplerate = sf.read('audio/aboiement_61.wav')
                sd.play(data,samplerate)
                aller_vers(20)
                aller_vers(54)
            
            #Capture vidéo
            diff      = cv2.absdiff(frame1, frame2)
            gray      = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            blur      = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY) #sensibilité à la luminosité
            dilated   = cv2.dilate(thresh, None, iterations=5)
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # Zone d'exclusion en rouge
            cv2.rectangle(frame1, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
            # Centre de l'image en bleu
            cv2.line(frame1, (centre_frame, 0), (centre_frame, height), (255, 0, 0), 1)

            #temps présent
            sablier = time.time()
            
            gauche = 0
            droite = 0
            # ----------------------boucle FOR de détections
            for contour in contours:
                if cv2.contourArea(contour) < 1500:
                    continue
                    
                #création d'un minuteur qui s'enclenche lorsqu'il n'y a pas de mouvement
                minuteur = sablier - temps
                temps = time.time()
                """print(round(minuteur,3))
                print(round(temps,1),"temps")
                print(round(sablier,1),"sablier")
                print(wait_calm, "wait_calm\n", calm, "calm\n", bark, "bark" )
                #print(round(temps,1),"le temps")"""
                
                        
                x, y, w, h = cv2.boundingRect(contour)
                center_x   = x + w // 2
                center_y   = y + h // 2
                
                # Ignorer si dans la zone d'exclusion
                if (x_min <= center_x <= x_max) and (y_min <= center_y <= y_max):
                    continue
                    
                # Direction basée sur center_x
                if center_x < centre_frame - ZONE_MORTE :
                    gauche =  1  # ← gauche
                elif center_x > centre_frame + ZONE_MORTE and not center_x < centre_frame - ZONE_MORTE:
                    droite = 1    # → droite
                    
                # Rectangle autour du mouvement
                cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(frame1, (center_x, center_y), 5, (0, 255, 255), -1)
                
            # ---------------------fin boucle for
            """
            if gauche == 1 or droite == 1:
                print(round(minuteur,1))
                print(position_actuelle)
                print(wait_calm, "wait_calm", calm, "calm", bark, "bark" )
            """
            # Stepper en action
            if gauche == 1 and droite == 0 and not limite:
                    direction_moteur = 1
                    print("gauche")
            elif gauche == 0 and droite == 1 and not limite:
                    direction_moteur = -1
                    print("droite")
            else:
                    direction_moteur = 0
                    #print("centre")
                    
            moteur_pas(PAS, direction_moteur)
            moteur_stop()
            
            #option d'aboiement du chien en fonction des mouvements
            #option 1 :
            if minuteur > 10 and minuteur < 30 and bark ==0 :
                wouaf()
                aller_vers(30)
                aller_vers(54)
            #option 2 :
            if minuteur > 30 and bark ==0 :  #lancement de l'aboiement après 30s de non mouvement
                    bark = 1  
                    calm = 0
                    mouv = 0
                
            if bark == 1 and position_actuelle <= 54 and mouv == 0: 
                    aller_vers(54)
                    mouv = 1
            elif bark == 1 and position_actuelle >= 54 and mouv == 1:
                    wouaf()
                    aller_vers(0)
                    mouv = 0
                        
            if mouv == 1 and calm == 0:
                    temps_alerte = time.time()
                    calm = 1
                        
            #fin d'aboiement
            if calm ==1 and bark ==1 :
                    fin_alerte = sablier - temps_alerte
                    if fin_alerte > 10:
                        aller_vers(54)
                        bark = 0
                        temps = time.time()
                        calm = 0
                
             
            #cv2.imshow("Motion Detection", frame1)   #<<<<<<<<<<<<<< affichage caméra 
            frame1 = frame2.copy()
            frame2 = picam2.capture_array()
            
            if cv2.waitKey(1) == ord('q'):
                break
                
except KeyboardInterrupt:
    print("Arrêt")
    
finally:
    picam2.stop()
    cv2.destroyAllWindows()
    
    # Coupe les pins
    led = 0
    voyant(led)
    # Coupe proprement le signal PWM du servo (évite qu'il force ou chauffe à l'arrêt)
    pi.set_servo_pulsewidth(PIN_SG90, 0)
    moteur_stop()
    PIN_SG90 = 0
    # Libère les ressources de la connexion pigpio
    pi.stop()
    print("GPIO nettoyé proprement")
    
#>>>FIN>>>>