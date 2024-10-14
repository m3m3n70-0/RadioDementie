from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import json
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Spotify credentials from environment variables
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

app = Flask(__name__)
app.secret_key = os.urandom(24)  # A secure random key for session management

# Path to the JSON file where playlists are stored
PLAYLIST_FILE = 'playlists.json'

# Spotify OAuth object using credentials from environment variables
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope="user-library-read playlist-read-private playlist-modify-public playlist-modify-private")

# Load playlists from the JSON file if it exists
def load_playlists():
    if os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, 'r') as file:
            return json.load(file)
    return []

# Save playlists to the JSON file
def save_playlists(playlists):
    with open(PLAYLIST_FILE, 'w') as file:
        json.dump(playlists, file)

# Global list to store radio channels (playlists)
radio_channels = load_playlists()

# Variable to store the custom command
custom_command = None

# Auto-redirect to login if not logged in
@app.before_request
def require_login():
    if request.endpoint in ['login', 'callback']:
        return
    if 'token_info' not in session:
        print("User not logged in. Redirecting to Spotify login.")
        return redirect(url_for('login'))

@app.route('/')
def index():
    if 'token_info' in session:
        print("User already logged in. Redirecting to /playlists.")
        return redirect(url_for('playlists'))
    return render_template('login.html')

@app.route('/login')
def login():
    try:
        auth_url = sp_oauth.get_authorize_url()
        print(f"Redirecting user to Spotify login: {auth_url}")
        return redirect(auth_url)
    except Exception as e:
        print(f"Error generating Spotify login URL: {e}")
        return "Error generating Spotify login URL", 500

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    print("Session token info after login:", session['token_info'])
    return redirect(url_for('playlists'))

@app.route('/playlists')
def playlists():
    if 'token_info' not in session:
        print("Token info missing in session. Redirecting to login.")
        return redirect(url_for('index'))

    token_info = session.get('token_info')
    print("Token Info in session:", token_info)

    sp = spotipy.Spotify(auth=token_info['access_token'])

    try:
        user_playlists = sp.current_user_playlists(limit=50)['items']
        print("Playlists fetched successfully!")
    except Exception as e:
        print(f"Error fetching playlists from Spotify: {e}")
        return "Error fetching playlists", 500

    return render_template('playlists.html', playlists=user_playlists, selected_playlists=radio_channels, custom_command=custom_command)

@app.route('/set_playlists', methods=['POST'])
def set_playlists():
    global radio_channels
    data = request.get_json()

    if 'playlists' in data:
        radio_channels = data['playlists']
        save_playlists(radio_channels)
        print(f"Received playlists: {radio_channels}")
        return jsonify({"message": "Playlists updated successfully!"}), 200
    else:
        return jsonify({"error": "No playlists provided"}), 400

@app.route('/get_playlists', methods=['GET'])
def get_playlists():
    return jsonify({"playlists": radio_channels}), 200

# Route for setting the custom command
@app.route('/set_command', methods=['POST'])
def set_command():
    global custom_command
    data = request.form
    custom_command = data.get('command')  # Get the command from the input field
    print(f"Custom command set to: {custom_command}")
    return jsonify({"message": "Command set successfully!"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)
