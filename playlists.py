import streamlit as st
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from spotipy.oauth2 import SpotifyPKCE
import webbrowser
import threading
import spotipy

# Spotify API credentials
CLIENT_ID = "8cfa81fbc4074f3aad32716a36044864"
REDIRECT_URI = "http://localhost:8080"  # Set the redirect URI to your local server

# Create a Spotipy client with PKCE authorization
sp_oauth = SpotifyPKCE(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI)

# Simple HTTP request handler
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Get authorization code from the callback URL
        code = self.path.split("code=")[1] if "code=" in self.path else None

        # Exchange authorization code for access token
        if code:
            token_info = sp_oauth.get_access_token(code)
            st.session_state.token_info = token_info

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Authentication successful. You can close this tab.")

# Streamlit app
def main():
    st.title("Spotify Playlist Viewer")

    # Check if the user is authenticated
    if "token_info" not in st.session_state:
        authenticate()

    # Display user's playlists
    if "token_info" in st.session_state:
        display_playlists()

# Authenticate the user
def authenticate():
    st.sidebar.header("Authentication")

    # Generate authorization URL
    auth_url = sp_oauth.get_authorize_url()
    st.sidebar.write("Click the link below to authenticate:")
    st.sidebar.markdown(f"[Authenticate]({auth_url})")

    # Start local server to handle callback
    start_local_server()

# Display user's playlists
def display_playlists():
    st.header("Your Playlists")

    # Create Spotipy client with access token
    sp = spotipy.Spotify(auth=st.session_state.token_info["access_token"])

    # Get user's playlists
    playlists = sp.current_user_playlists()

    # Display playlists
    for playlist in playlists["items"]:
        st.write(f"- {playlist['name']}")

# Start local server in a separate thread
def start_local_server():
    server_address = ("", 5000)
    httpd = ThreadingHTTPServer(server_address, RequestHandler)

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.start()

    # Open the authentication URL in the default web browser
    webbrowser.open(sp_oauth.get_authorize_url())

# Threading HTTP server
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

# Run the Streamlit app
if __name__ == "__main__":
    main()
