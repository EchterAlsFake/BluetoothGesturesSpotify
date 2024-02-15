"""
Copyright (C) 2024 Johannes Habel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import json
import spotipy
import http.server
import webbrowser
import threading
import socketserver

from urllib.parse import urlparse, parse_qs
from spotipy.oauth2 import SpotifyOAuth
from colorama import Fore
from evdev import InputDevice, list_devices as ev_list_devices, ecodes

PORT = 8888
Handler = http.server.SimpleHTTPRequestHandler

scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing"

SPOTIFY_CLIENT_ID = None
SPOTIFY_CLIENT_SECRET = None
SPOTIFY_REDIRECT_URI = None
# These will be containing the information when compiling for release


class SpotifyAuthHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, auth_manager=None, **kwargs):
        self.auth_manager = auth_manager
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        query = urlparse(self.path).query
        code = parse_qs(query).get('code', None)

        if code:
            self.server.auth_code = code[0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("You can close this window now.".encode('utf-8'))
            threading.Thread(target=self.server.shutdown, daemon=True).start()  # Shut down the server
        else:
            self.send_error(400, "Missing code in the request")


def start_local_server(handler_class, auth_manager):
    port = PORT  # or any other free port you wish to use
    server_address = ('', port)
    httpd = socketserver.TCPServer(server_address,
                                   lambda *args, **kwargs: handler_class(*args, auth_manager=auth_manager, **kwargs))

    print(f"Starting local server on port {port}...")
    httpd.serve_forever()  # Start the server
    return httpd.auth_code  # Return the captured code


class EarBudsGestures:
    def __init__(self):
        self.sp = None
        print(f"{Fore.LIGHTGREEN_EX}[+]{Fore.LIGHTCYAN_EX}Scanning for potential AVRCP-related input devices...{Fore.RESET}")
        devices = self.find_potential_avrcp_input_devices()
        selected_device = self.choose_device(devices)
        self.sp = self.spotify()
        print(f"{Fore.LIGHTGREEN_EX}[+]{Fore.LIGHTMAGENTA_EX}Setup Done!")
        print(
            f"{Fore.RED} ! INFO: If it doesn't work now and you had multiple devices to choose from, rerun the script and "
            f"try one of the other devices.{Fore.RESET}")

        print(f"{Fore.LIGHTGREEN_EX}[+]{Fore.LIGHTMAGENTA_EX}Now you can press your gestures to control spotify :)")

        for event in selected_device.read_loop():
            # Respond only to key press events, not releases or autorepeat
            if event.value == 1:  # This ensures actions are only triggered on press
                if event.type == ecodes.EV_KEY:
                    if event.code in [ecodes.KEY_NEXTSONG]:
                        self.next_track()

                    elif event.code in [ecodes.KEY_PREVIOUSSONG]:
                        self.previous_track()

                    elif event.code in [ecodes.KEY_PAUSECD, ecodes.KEY_PLAYCD]:
                        self.toggle_playback()

    @classmethod
    def load_spotify_credentials(cls, json_file_path):
        """Load Spotify credentials from a JSON file."""
        with open(json_file_path, 'r') as file:
            credentials = json.load(file)
        return credentials

    @classmethod
    def drop_to_user(cls, user=None, rundir=None, caps=None):
        """
        Information: This function is needed, because you can't open a webbrowser as root and spotify does that
        automatically for the authorization. This is why I need to search for AVRCP devices with root access and then
        drop permissions as I then don't need it anymore.

        (Just if anyone is confused why this function exists)

        A big thanks to: https://stackoverflow.com/questions/2699907/dropping-root-permissions-in-python
        The answer from Craig McQueen did it :) https://stackoverflow.com/users/60075/craig-mcqueen
        """

        import os
        import pwd

        if caps:
            import prctl

        if os.getuid() != 0:
            # We're not root
            raise PermissionError('Run with sudo or as root user')

        if user is None:
            user = os.getenv('SUDO_USER')
            if user is None:
                raise ValueError('Username not specified')
        if rundir is None:
            rundir = os.getcwd()

        # Get the uid/gid from the name
        pwnam = pwd.getpwnam(user)

        if caps:
            prctl.securebits.keep_caps = True
            prctl.securebits.no_setuid_fixup = True

        # Set user's group privileges
        os.setgroups(os.getgrouplist(pwnam.pw_name, pwnam.pw_gid))

        # Try setting the new uid/gid
        os.setgid(pwnam.pw_gid)
        os.setuid(pwnam.pw_uid)

        os.environ['HOME'] = pwnam.pw_dir

        os.chdir(os.path.expanduser(rundir))

        if caps:
            prctl.capbset.limit(*caps)
            try:
                prctl.cap_permitted.limit(*caps)
            except PermissionError:
                pass
            prctl.cap_effective.limit(*caps)

        # Ensure a reasonable umask
        old_umask = os.umask(0o22)

    def spotify(self):
        self.drop_to_user()

        if SPOTIFY_CLIENT_ID is None and SPOTIFY_CLIENT_SECRET is None and SPOTIFY_REDIRECT_URI is None:
            json_file_path = 'spotify_credentials.json'
            credentials = self.load_spotify_credentials(json_file_path)

            auth_manager = SpotifyOAuth(
                client_id=credentials["SPOTIPY_CLIENT_ID"],
                client_secret=credentials["SPOTIPY_CLIENT_SECRET"],
                redirect_uri=credentials["SPOTIPY_REDIRECT_URI"],
                scope=scope,
                open_browser=False
            )

        else:
            auth_manager = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=scope,
                open_browser=False
            )

        auth_url = auth_manager.get_authorize_url()
        print(f"{Fore.LIGHTGREEN_EX}[+]{Fore.LIGHTYELLOW_EX}Doing authorization flow... Check your browser!")
        print(f"{Fore.RESET}Please open the following URL in your web browser to authorize the application "
              f"(if your browser didn't open automatically) -->:\n{auth_url}")
        webbrowser.open(auth_url)

        # Start the local server and get the authorization code
        auth_code = start_local_server(SpotifyAuthHandler, auth_manager)
        # Exchange the code for a token
        token = auth_manager.get_access_token(auth_code, as_dict=True)  # Now, this directly returns the token string
        print(f"{Fore.LIGHTGREEN_EX}[+]{Fore.LIGHTBLUE_EX}Received Token: {token.get('access_token')}")
        sp = spotipy.Spotify(token.get("access_token"))  # Use the token string directly

        return sp  # Return the authorized Spotify client

    @classmethod
    def find_potential_avrcp_input_devices(cls):
        """Finds potential AVRCP input devices by checking for devices with media keys."""
        potential_devices = []
        for device_path in ev_list_devices():
            try:
                device = InputDevice(device_path)
                capabilities = device.capabilities()
                if ecodes.EV_KEY in capabilities:
                    keys = capabilities[ecodes.EV_KEY]
                    media_keys = {ecodes.KEY_PLAYPAUSE, ecodes.KEY_NEXTSONG, ecodes.KEY_PREVIOUSSONG}
                    if any(key in keys for key in media_keys):
                        potential_devices.append(device.path)
            except Exception as e:
                print(f"Error processing {device_path}: {e}")

        devices = []
        for dev_path in potential_devices:
            devices.append(dev_path)

        return devices

    @classmethod
    def choose_device(cls, devices):
        print(f"{Fore.LIGHTBLUE_EX}[!]{Fore.LIGHTGREEN_EX}Choose your device from the list below. The last device are "
              f"by a high chance your bt (Bluetooth) Ear Buds / headphones. {Fore.LIGHTBLUE_EX}TIP: run the script without your bt device and then again"
              f" with the bt device connected. This makes it easier to find out which of the devices is your bt device {Fore.RESET} ")
        for i, device in enumerate(devices, start=1):
            print(f"{i}. {device}")
        choice = input(f"{Fore.LIGHTGREEN_EX}[+]{Fore.LIGHTYELLOW_EX}Enter the number of your device: ")
        try:
            index = int(choice) - 1
            if 0 <= index < len(devices):
                return InputDevice(devices[index])

            else:
               print(f"{Fore.LIGHTRED_EX}[~]{Fore.RESET}Invalid selection. Please enter a number from the list.")

        except ValueError:
            print(f"{Fore.LIGHTRED_EX}[~]{Fore.RESET}Please enter a number.")

        return None

    def toggle_playback(self):
        playback_state = self.sp.current_playback()
        is_playing = playback_state["is_playing"]
        print(f"{Fore.LIGHTGREEN_EX}[+]{Fore.LIGHTYELLOW_EX}Changing Playback state")

        if is_playing:
            self.sp.pause_playback()

        elif not is_playing:
            self.sp.start_playback()

    def next_track(self):
        self.sp.next_track()
        print(f"{Fore.LIGHTGREEN_EX}[+]{Fore.LIGHTMAGENTA_EX}Next track")

    def previous_track(self):
        self.sp.previous_track()
        print(f"{Fore.LIGHTGREEN_EX}[+]{Fore.LIGHTCYAN_EX}Previous track")


if __name__ == "__main__":
    EarBudsGestures()

