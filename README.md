# rasppi5-pir-wake
PIR Wake and MQTT sensor for digital dashboard.
This will use an AM312 Mini PIR detactor module in order to wake the monitor connected to a Raspberry PI5. This will also send the motion data to a sensor on your MQTT server for use in other automations.
The sensor I use is this one: https://amzn.to/45sbFjG

##AI DISCLAIMER
This was essentially "vibe-coded". While I am not worried about any implications of a small amount of code to control a PIR sensor, there may be issues with this code. I am an amateur coder at best which is why I used AI in the first place.

## How to use
1. Download to the Raspberry PI5 (Raspberry OS) that you want to use this on.
2. Change out the MQTT IP, MQTT port if necessary, MQTT username, and MQTT password. You may also need to change the XAUTHORITY path if not using the default pi username/home path.
3. You can run as a test "python3 pir_wake.py" or setup as a service to start when the PI boots.
4. You can also adjust the timing by playing with the timeout and screen off variables if you wish.
