import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pynput import keyboard  # Use pynput for cross-platform keyboard controls
import json  # For loading playlists from playlists.json
from dotenv import load_dotenv
import time  # For delay

# Load environment variables from .env file
load_dotenv()

# Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

# Spotify authentication and initialization
scope = "user-library-read user-read-playback-state user-modify-playback-state playlist-read-private"
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope)

# Path to the JSON file where playlists are stored
PLAYLIST_FILE = 'playlists.json'

# Global variables
radio_channels = []  # List of Spotify playlist URIs
current_channel = 0  # Current channel index

# Load playlists from the JSON file dynamically
def load_playlists():
    global radio_channels
    if os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, 'r') as file:
            radio_channels = json.load(file)
            print(f"Loaded playlists: {radio_channels}")
    else:
        print("No playlists found. Please add playlists via the web interface.")
    
    return radio_channels

# Authenticate and get Spotify client (automatically handles callback URL)
def get_spotify_client():
    token_info = sp_oauth.get_cached_token()
    
    if not token_info:
        # This will automatically open the browser, handle the callback, and return the token
        token_info = sp_oauth.get_access_token()
    
    return spotipy.Spotify(auth=token_info['access_token'])

sp = get_spotify_client()  # Get the authenticated Spotify client

# Play the current channel (playlist)
def play_channel(channel_index):
    global sp
    devices = sp.devices()  # Get available devices
    
    # Load the updated playlists every time a channel is played
    radio_channels = load_playlists()
    
    if devices['devices'] and radio_channels:
        device_id = devices['devices'][0]['id']  # Use the first available device
        playlist_uri = radio_channels[channel_index]  # Get the playlist URI

        try:
            sp.shuffle(True, device_id=device_id)  # Enable shuffle mode
            sp.start_playback(device_id=device_id, context_uri=playlist_uri)
            print(f"Playing (shuffled) playlist: {playlist_uri} on device: {device_id}")
        except Exception as e:
            print(f"Error starting playback: {e}")
    else:
        print("No active devices found or no playlists available!")

# Toggle play/pause for the current channel
def play_pause():
    global sp  # Make sure to declare this inside the function
    
    # Fetch the current playback status
    playback = sp.current_playback()
    print(f"Playback state: {playback}")  # Debugging line
    
    # If there's no playback (Spotify isn't playing anything)
    if playback is None or playback['item'] is None:
        print("No current playback. Starting the first playlist.")
        play_channel(0)  # Start playing the first playlist (index 0)
    else:
        # If Spotify is playing something, toggle play/pause
        if playback['is_playing']:
            sp.pause_playback()
            print("Playback paused.")
        else:
            sp.start_playback()
            print("Playback resumed.")

# Zap to the next channel (playlist)
def zap_next_channel():
    global current_channel
    
    # Reload playlists every time a channel is zapped
    radio_channels = load_playlists()
    
    if len(radio_channels) == 0:
        print("No playlists available. Please set some playlists.")
        return

    current_channel = (current_channel + 1) % len(radio_channels)
    print(f"Zapping to channel {current_channel}")
    play_channel(current_channel)

# Handle key presses
def on_press(key):
    try:
        if key.char == 'n':  # Next channel
            zap_next_channel()
        elif key.char == 'm':  # Play/Pause
            play_pause()
    except AttributeError:
        pass

if __name__ == "__main__":
    print("Press 'n' to zap channels and 'm' to play/pause.")
    
    # Listen for key presses using pynput
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
