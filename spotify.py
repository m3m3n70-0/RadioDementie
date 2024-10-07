from flask import Flask, request, jsonify, redirect, session, render_template, url_for
from spotify_integration import SpotifyIntegration
import os
import spotipy
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Load the secret key from the .env file
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Load Spotify credentials from environment variables
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

# Initialize Spotify integration with OAuth
spotify = SpotifyIntegration(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)

# List to store the playlists set via webhook
radio_channels = []
current_channel = 0  # Index of the currently playing playlist

@app.route('/')
def login():
    """Redirect to Spotify for authentication if not logged in."""
    # Check if the user is already authenticated by checking the session
    if 'token_info' not in session:
        # Redirect to Spotify authorization URL
        auth_url = spotify.get_authorize_url()
        return redirect(auth_url)
    else:
        # Show a page telling the user that they are already authenticated
        return render_template('logged_in.html')  # A page that tells the user they're logged in and can set up the radio

@app.route('/callback')
def callback():
    """Handle Spotify authentication callback and store token."""
    code = request.args.get('code')
    if not code:
        print("Missing authorization code")
        return "Error: Missing authorization code", 400

    try:
        # Exchange the code for an access token
        token_info = spotify.get_access_token(code)
        # Store token information in the session
        session['token_info'] = token_info

        # After successful login, redirect to the radio page
        return redirect('/radio')
    except Exception as e:
        print(f"Error during token exchange: {e}")  # Log any token exchange errors
        return f"Error during token exchange: {e}", 500

def get_spotify_client():
    """Retrieve the authenticated Spotify client, refresh token if needed."""
    token_info = session.get('token_info', None)
    if not token_info:
        return None

    # Check if token is expired and refresh it if necessary
    if spotify.is_token_expired(token_info):
        print("Token expired, refreshing...")
        token_info = spotify.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    access_token = token_info['access_token']
    sp = spotipy.Spotify(auth=access_token)
    return sp

@app.route('/get_playlists', methods=['GET'])
def get_playlists():
    """Fetch the current user's playlists from Spotify, including images."""
    try:
        sp = get_spotify_client()
        if sp:
            playlists = sp.current_user_playlists(limit=50)  # Fetch the user's playlists
            playlist_data = []
            for playlist in playlists['items']:
                playlist_data.append({
                    'name': playlist['name'],
                    'uri': playlist['uri'],
                    'image_url': playlist['images'][0]['url'] if playlist['images'] else None  # Fetch the first image
                })
            return jsonify(playlist_data), 200
        else:
            print("Error: Unable to fetch playlists. User not authenticated.")
            return jsonify({"error": "Unable to fetch playlists. Please login to Spotify."}), 401
    except Exception as e:
        print(f"Error fetching playlists: {e}")
        return jsonify({"error": f"Error fetching playlists: {e}"}), 500

@app.route('/set_playlists', methods=['POST'])
def set_playlists():
    """Webhook endpoint to receive the list of playlists."""
    global radio_channels
    data = request.get_json()

    if 'playlists' in data:
        # Update the radio_channels with the received playlist URIs
        radio_channels = data['playlists']
        print(f"Received playlists: {radio_channels}")  # Log the received playlists
        return jsonify({"message": "Playlists set successfully", "playlists": radio_channels}), 200
    else:
        print("Error: No playlists provided.")
        return jsonify({"error": "No playlists provided"}), 400

@app.route('/radio')
def radio_page():
    """Radio page where users can zap between playlists."""
    if 'token_info' not in session:
        # If the user is not authenticated, redirect to the login page
        return redirect('/')
    
    return render_template('radio.html')  # Replace with your radio page that shows the playlist zapping functionality

def play_channel(channel_index):
    """Play the selected channel (playlist)."""
    sp = get_spotify_client()
    if sp:
        devices = sp.devices()  # Fetch available devices
        if devices['devices']:
            device_id = devices['devices'][0]['id']  # Use the first available device
            playlist_uri = radio_channels[channel_index]  # Get the playlist URI
            try:
                sp.start_playback(device_id=device_id, context_uri=playlist_uri)
                print(f"Playing playlist: {playlist_uri} on device: {device_id}")  # Log the playlist and device
            except Exception as e:
                print(f"Error starting playback: {e}")  # Log any playback errors
        else:
            print("No active devices found!")
            # Log available devices for debugging
            print(f"Available devices: {devices}")
    else:
        print("Spotify client not available or token expired.")

def zap_next_channel():
    """Zap to the next playlist."""
    global current_channel
    if len(radio_channels) == 0:
        print("No playlists available. Use the webhook to set playlists.")
        return

    current_channel = (current_channel + 1) % len(radio_channels)
    print(f"Zapping to next channel: {current_channel}")  # Log current channel
    play_channel(current_channel)

def play_pause():
    """Toggle play/pause for the current playlist."""
    sp = get_spotify_client()
    if sp:
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            sp.pause_playback()
            print("Playback paused")
        else:
            sp.start_playback()
            print("Playback started")
    else:
        print("Spotify client not available.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
