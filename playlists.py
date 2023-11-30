import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import re
from spotipy.oauth2 import SpotifyOAuth


client_id = '8cfa81fbc4074f3aad32716a36044864'
client_secret = 'a64ec813eaa24d19a42c694dbc61ba35'
redirect_uri = 'http://localhost:8080'

SPOTIPY_SCOPE = 'user-library-read playlist-read-private'

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri,
                        scope="user-library-read playlist-read-private")


def id_from_url(url):
    try:
        url_regex = re.search(
            r"^https?:\/\/(?:open\.)?spotify.com\/(user|episode|playlist|track|album)\/(?:spotify\/playlist\/)?(\w*)",
            url)
        st.write(f'{url_regex.group(1)} {url_regex.group(2)}')
        return url_regex.group(1), url_regex.group(2)

    except AttributeError:
        st.error('Invalid URL', icon="🚨")


def login():
    # Check if the URL contains the authorization code
    url_params = st.experimental_get_query_params()
    code = url_params.get("code", None)

    # If the URL contains the authorization code, get the access token
    if code:
        token_info = sp_oauth.get_access_token(code)
        st.success("Successfully authenticated! You can now fetch your playlists.")
        return token_info

    # If there's no token, redirect to Spotify login
    auth_url = sp_oauth.get_authorize_url()
    st.warning(f"Please log in to Spotify: [Click here to log in]({auth_url})")
    return None

def function(playlist_id):
    st.balloons()
    # st.snow()
    playlist = sp.playlist(playlist_id)
    tracks = playlist["tracks"]["items"]
    track_names = [track["track"]["name"] for track in tracks]
    # audio_features = [sp.audio_features(tracks=track_names)]
    track_artists = [", ".join([artist["name"] for artist in track["track"]["artists"]]) for track in tracks]
    track_popularity = [track["track"]["popularity"] for track in tracks]
    # track_valence = [audio_features[track["track"]["valence"]] for track in tracks]
    track_duration = [track["track"]["duration_ms"] for track in tracks]
    track_album = [track["track"]["album"]["name"] for track in tracks]
    track_release_date = [track["track"]["album"]["release_date"] for track in tracks]
    # track_image = [track['album']['images'][0]['url'] for track in tracks]

    # display the playlist data in a table

    st.write(f"## {playlist['name']}")
    st.image(playlist['images'][0]['url'], width=250)
    st.write(f"**Description:** {playlist['description']}")
    st.write(f"**Number of tracks:** {len(tracks)}")
    st.write("")
    st.write("### Tracklist")
    st.write("| Name | Artist | Album | Release Date | Popularity | Duration (ms) | Mood")
    # st.write("| ---- | ------ | ----- | ------------ | ---------- | -------------- |")
    for i in range(len(tracks)):
        st.write(f"| {track_names[i]} | {track_artists[i]} | {track_album[i]} | {track_release_date[i]} |"
                 f" {track_popularity[i]} | {track_duration[i]}")

    # create a dataframe from the playlist data
    data = {"Name": track_names, "Artist": track_artists, "Album": track_album, "Release Date": track_release_date,
            "Popularity": track_popularity, "Duration (ms)": track_duration}
    df = pd.DataFrame(data)

    # display a histogram of track popularity
    fig_popularity = px.histogram(df, x="Popularity", nbins=20, title="Track Popularity Distribution")
    st.plotly_chart(fig_popularity)

    # add a dropdown menu for bivariate analysis
    st.write("#### Bivariate Analysis")
    x_axis = st.selectbox("Select a variable for the x-axis:", ["Popularity", "Duration (ms)"])
    y_axis = st.selectbox("Select a variable for the y-axis:", ["Popularity", "Duration (ms)"])
    fig_bivariate = px.scatter(df, x=x_axis, y=y_axis, title=f"{x_axis} vs. {y_axis}")
    st.plotly_chart(fig_bivariate)

    # add a dropdown menu for multivariate analysis
    st.write("#### Multivariate Analysis")
    color_by = st.selectbox("Select a variable to color by:", ["Artist", "Album", "Release Date"])
    size_by = st.selectbox("Select a variable to size by:", ["Popularity", "Duration (ms)"])
    fig_multivariate = px.scatter(df, x="Duration (ms)", y="Popularity", color=color_by, size=size_by,
                                  hover_name="Name", title="Duration vs. Popularity Colored by Artist")
    st.plotly_chart(fig_multivariate)

    '''
    # add a summary of the playlist data
    st.write("")
    st.write("### Playlist Summary")
    st.write(
        f"**Most popular track:** {df.iloc[df['Popularity'].idxmax()]['Name']} by {df.iloc[df['Popularity'].idxmax()]['Artist']} ({df['Popularity'].max()} popularity)")
    st.write(
        f"**Least popular track:** {df.iloc[df['Popularity'].idxmin()]['Name']} by {df.iloc[df['Popularity'].idxmin()]['Artist']} ({df['Popularity'].min()} popularity)")

    # display a bar chart of the top 10 most popular artists in the playlist
    st.write("#### Top 10 Artists")
    st.write("The bar chart below shows the top 10 most popular artists in the playlist.")
    top_artists = df.groupby(['Artist']).by("Popularity", ascending=False).head(10)
    fig_top_artists = px.bar(top_artists, x=top_artists.index, y="Popularity", title="Top 10 Artists")
    st.plotly_chart(fig_top_artists)

    # display a bar chart of the top 10 most popular songs in the playlist
    st.write("#### Top 10 Songs")
    st.write("The bar chart below shows the top 10 most popular songs in the playlist.")
    top_artistss = df.groupby("Name").mean().sort_values("Popularity", ascending=False).head(10)
    fig_top_artistss = px.bar(top_artistss, x=top_artistss.index, y="Popularity", title="Top 10 Songs")
    st.plotly_chart(fig_top_artistss)
    '''

def get_recommendations(track_name):
    results = sp.search(q=track_name, type='track')
    track_uri = results['tracks']['items'][0]['uri']

    # Get recommended tracks
    recommendations = sp.recommendations(seed_tracks=[track_uri], limit=20)['tracks']
    return recommendations


def main():
    st.title("Spotify Playlist Analyzer")

    image = Image.open('Vibify.png')
    st.sidebar.image(image)

    playlist_name = st.sidebar.text_input("Enter the URL of your Spotify playlist:")
    st.sidebar.write("Or...")
    button = st.sidebar.button("Login with Spotify", use_container_width=True)

    if playlist_name:
        url_type, playlist_id1 = id_from_url(playlist_name)
    else:
        playlist_id1 = None

    if button:
        # Get the access token or redirect to Spotify login page
        token_info = sp_oauth.get_cached_token()

        # Display login button if not authenticated
        if not token_info:
            token_info = login()

        # If authentication is successful, fetch and display playlists
        if token_info:
            sp = spotipy.Spotify(auth=token_info["access_token"])

            # Fetch and display user playlists
            playlists = sp.current_user_playlists()

            # Create a dropdown to select a playlist
            selected_playlist_name = st.selectbox("Select a playlist:",
                                                  [playlist['name'] for playlist in playlists['items']])

            # Display playlist information only when the playlist is selected
            if st.button("Fetch Playlist Data"):
                # Get the selected playlist
                selected_playlist = next(
                    (playlist for playlist in playlists['items'] if playlist['name'] == selected_playlist_name), None)
                playlist_id2 = selected_playlist['id']
    else:
        playlist_id2 = None


    results = []
    if playlist_id1:
        # del results
        results = function(playlist_id1)
        return results
    elif playlist_id2:
        # del results
        results = function(playlist_id2)
        st.success('Got playlist!')

    if results:
        recommendations = get_recommendations(results)
        st.write("Recommended songs:")
        for track in recommendations:
            st.write(f"{track['name']} ---- {track['artists'][0]['name']}")
            st.image(track['album']['images'][0]['url'], width=400)


if __name__ == '__main__':
    main()

