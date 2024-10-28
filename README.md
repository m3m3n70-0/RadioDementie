# Spotify Radio Controller

This project is a custom Spotify-based radio station controller, enabling users to select playlists, issue commands to run after a song ends, and automatically shuffle through playlists. The project uses the Spotify API, Python, and Flask to build a backend and web interface for configuring and managing the "radio station."

### Features
- **Playlist Selection**: Choose playlists from your Spotify account to queue up for radio playback.
- **Custom Commands**: Enter a custom command that will execute after each song ends.
- **Automatic Playback Monitoring**: Automatically detects when a song is ending and displays the custom command if set.
- **Web Interface**: Allows for playlist selection and command setting via a web page.

### Prerequisites
- Python 3.6+
- Spotify Developer account (needed to obtain API keys)
- Spotify Premium account (required for playback control)
- `spotipy`, `pynput`, `flask`, `pygame`, `dotenv` Python libraries

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/spotify-radio-controller.git
   cd spotify-radio-controller
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Spotify Developer Account Setup**:
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications).
   - Create a new application and add `http://localhost:5001/callback` as the redirect URI.
   - Copy the **Client ID** and **Client Secret** from your Spotify app into a `.env` file in the project root as shown below.

4. **Configure the `.env` file**:
   Create a `.env` file and add the following:
   ```plaintext
   SPOTIPY_CLIENT_ID=your_client_id
   SPOTIPY_CLIENT_SECRET=your_client_secret
   SPOTIPY_REDIRECT_URI=http://localhost:5001/callback
   ```

### Usage

1. **Start the Flask Server**:
   - Start the Flask server for the web interface:
   ```bash
   python playlist_control.py
   ```

   - Visit `http://localhost:5001` in a browser, log in to Spotify, and select your playlists and set commands.

2. **Start the Radio Control**:
   - Open a new terminal and run:
   ```bash
   python radio_control.py
   ```
   - The `radio_control.py` script manages the playback, shuffles through playlists, and triggers commands after each song ends.

3. **Interacting with the Radio**:
   - Press `-` to zap to the next channel (next playlist in the queue).
   - Press `=` to toggle play/pause.

### Files Overview

- **`playlist_control.py`**: Flask-based backend handling playlist selection and command setup.
- **`radio_control.py`**: Script for controlling Spotify playback, monitoring song progress, and triggering commands.
- **Web Interface HTML files**:
  - `index.html`: Redirects users to the Spotify login page.
  - `login.html`: Informs users they are being redirected to Spotify.
  - `playlists.html`: Main interface to select playlists and set custom commands.
- **JSON Files**:
  - `command.json`: Stores the custom command to be run after each song.
  - `playlists.json`: Stores selected playlists for radio playback.

### Key Functions

- **Play Channel**: Starts playback of the selected playlist channel with shuffling enabled.
- **Fetch and Display Command**: Checks `command.json` for any commands to display and execute after each song ends.
- **Monitor Playback**: Monitors playback progress to detect when a song is about to end and triggers the command.

### Example Workflow
1. **Select Playlists**: Choose playlists from your Spotify account.
2. **Set Commands**: Enter any custom command to be executed after each song.
3. **Playback Management**: Start `radio_control.py`, which will:
   - Automatically play selected playlists on shuffle.
   - Detect when a song ends, display, and execute the command (if any).
4. **Adjust Settings**: Modify playlists or commands in real-time via the web interface.

### Troubleshooting

- **Playback Errors**: Ensure you are logged into a Spotify Premium account and the Spotify app is open.
- **Authentication Issues**: If the script fails to authenticate, try refreshing your Spotify Developer app credentials or ensure the `.env` variables are correctly set.

### License
This project is licensed under the MIT License.

### Contributing
Feel free to submit issues or pull requests.
