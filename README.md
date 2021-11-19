# micropython_pranje_laktofriza

to install micropython on teensy follow the procedure

git clone https://github.com/micropython/micropython
cd micropython
make -C mpy-cross
cd ports/teensy
trizen -S teensyduino --noconfirm
sudo ARDUINO=/usr/share/arduino make
press the upload button
sudo ARDUINO=/usr/share/arduino make deploy
