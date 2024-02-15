<h1 align="center">Bluetooth Gestures for Spotify</h1> 

# Description

This Python script allows you to control the Spotify playback using your gestures from your Ear Buds / Bluetooth headphones
on Linux systems.

# How it Works
Basically, your Ear Buds (or any other bt device) are sending keys to the system when you press gestures. There's a protocol around it called `AVRCP`. 
It is some kind of general standard and these keys can be captured. Now what this script does is, it basically captures the keys and uses the Spotify API
via `Spotipy` and changes your playback.

# Supported devices
- Any Bluetooth device with gestures and the AVRCP protocol
- e.g Ear Buds and headphones

For a list of tested and confirmed devices look [Here](https://github.com/EchterAlsFake/BluetoothGesturesSpotify/blob/master/TESTED_DEVICES.md)

# Requirements
- Bluetooth device with gestures (e.g., buttons or touch) supporting the AVRCP protocol
- Root permissions 
- Linux

# Platforms:
It should work on every Linux distribution. Windows is NOT supported!

# How to use
- Download the binary from releases
- Execute the script with root / admin privileges
- The script will ask you to choose your device from a list. Follow the instructions
- Your web browser will open to authorize the application
- Then you are ready, and you can control your playback with the gestures. Let the script run in the background :) 


# Setup local usage
If you don't want to use the pre-compiled versions for some reason, you can run it locally with your own Spotify API application.
You leave the script how it is, but at the beginning you change the `SPOTIFY_CLIENT_SECRET`, the `SPOTIFY_CLIENT_ID` and the
`SPOTIFY_REDIRECT_URI` to your values you got from the developer's dashboard.

Now you can run the application.

For all other users, you can download the binary file, and it will use my own Spotify Application.

# Future
- [] Support for non-Bluetooth devices
- [] Support for Volume control
- [] Simplifying the process

# License
Copyright (C) 2024 Johannes Habel
<br>Licensed under the GPL 3 license

# Contributions
- To add your tested device into the tested device list, join the Discussion
- Pull Requests / Issues are welcome. Don't hesitate to open it up :) 

# Credits
- https://stackoverflow.com/questions/2699907/dropping-root-permissions-in-python
- ChatGPT
### Libraries:
- Spotipy
- colorama
- evdev