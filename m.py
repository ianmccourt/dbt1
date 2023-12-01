"""
Spotify Playlist Analyzer
"""
# Importing Libraries
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import re
import c

@st.cache_resource(show_spinner=False, experimental_allow_widgets=True)
def main():
    st.title("Spotify Playlist Analyzer")
    image = Image.open('Vibify.png')
    st.sidebar.image(image)

    playlist_name = st.sidebar.text_input("Enter the URL of your Spotify playlist:")
    st.sidebar.write("Or...")

    # Use st.button with a specific key
    login_button = st.sidebar.button("Login with Spotify", key="login_button", use_container_width=True)

    # Initialize session state
    if 'selected_playlist_name' not in st.session_state:
        st.session_state.selected_playlist_name = None

    if playlist_name:
        url_type, playlist_id1 = c.Playlist.id_from_url(playlist_name)
        c.Playlist(playlist_id1)
    else:
        playlist_id1 = None

    sp = None  # Initialize Spotify client outside of the if conditions

    # Check if the login button is clicked
    if login_button:
        sp, selected_playlist_name = c.login()

        # Store the selected playlist name in session state
        st.session_state.selected_playlist_name = selected_playlist_name

    if playlist_id1 or (sp and st.session_state.selected_playlist_name):
        # Call a separate function to handle playlist selection
        handle_playlist_selection(sp)


# Function to handle playlist selection
def handle_playlist_selection(sp):
    # Fetch user's playlists
    playlists = sp.current_user_playlists()

    # Create a dropdown to select a playlist
    selected_playlist_name = st.selectbox("Select a playlist:",
                                          [playlist['name'] for playlist in playlists['items']],
                                          key="playlist_dropdown")

    # Store the selected playlist name in session state
    st.session_state.selected_playlist_name = selected_playlist_name

    # Find the playlist with the matching name
    selected_playlist = next(
        (playlist for playlist in playlists['items'] if playlist['name'] == st.session_state.selected_playlist_name),
        None
    )

    if selected_playlist:
        playlist_id = selected_playlist['id']
        c.run(c.Playlist(playlist_id))
        st.success('Got playlist!')
    else:
        st.warning(f"Playlist with name '{st.session_state.selected_playlist_name}' not found.")


if __name__ == '__main__':
    main()
