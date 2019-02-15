# kankun-magictimer
My replacement timer system for the KK-sp3 timer

# what is this?
This repo contains my replacement timer system for the KK SP3. 
Instead of pinging some server in china my timers now ping a local server running the backend.py
which tells the timer to turn on/off.

# The directory structure
www/ Basically empty directory where the www frontend will eventually live
backend/ Server python script which runs always and acts as a http server
kk-sp3/ the files that need to be replaced on the device.

# Other stuff
Ive replaced the button handling so the button will act as a toggle for ON/OFF/AUTO modes
The blue LED indicates that the timer is in auto mode, RED means on.
Can turn on/off based on the sunset/sunrise time at your location(!)

# how to configure
backend/config.json has a listing of all the times for each of your timers. 
e.g "Fri": [ {"1830": "ON"}, {"2030": "OFF"} ] means on fridays, turn on at 18:30 and off at 20:30
"Sun": [ {"$sunset - 120": "ON"}, {"$sunrise + 90": "OFF"}] means on sundays, turn on 120min before sunset and off 90min after sunrise.

In kk-sp3/root/light.sh and do_button.sh you need to change the server that is running the magictimer.py script (10.0.0.2:8100 is my local machine obviously)

On the machine youll be using as the server run "python /path/to/magictimer.py <port number>&" so it stays running in the background.

PULL REQUESTS WELCOME ESPECIALY FOR A FRONTEND

# TODO
* switch to a database instead of JSON config
* probably switch to django or some other proper server framework
* a frontend!
