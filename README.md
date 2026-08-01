The target is to create a dog which can see, listen, bark and move

About the design:

The head was print with 3D printer,
The CPU is from Rapsberrypi 4B,
The code is programming with python3 

About the components:

-P5V04A Sunny Camera
-Stepper 28BYJ-48-08 5 Vcc
-Servo Moteur DS-S014M 9KG
-Microphone USB LYMISPIYA
-LED 2xRed 1xRGB

About the launcher:

/etc/systemd/system
sudo nano chien.service
sudo systemctl enable chien.service
sudo systemctl start chien.service
raspi-config - boot - CLI 

[Unit]
Description=Programme Chien
After=network.target

[Service]
ExecStart=/home/dorian/Documents/vvirtual/bin/python3 /home/dorian/Documents/vvirtual/Dobermann/moteur_&_camera.py
WorkingDirectory=/home/dorian/Documents/vvirtual/Dobermann
Restart=always
User=dorian

[Install]
WantedBy=multi-user.target

