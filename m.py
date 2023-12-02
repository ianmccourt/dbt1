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


# Your Spotify API credentials (note: it's not secure to include your credentials in the code)
client_id = '8cfa81fbc4074f3aad32716a36044864'
client_secret = 'a64ec813eaa24d19a42c694dbc61ba35'
redirect_uri = 'https://vibifytest01.streamlit.app'

# Set up the Spotify client credentials manager and Spotipy client
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri,
                        scope="user-library-read playlist-read-private")

class Playlist:
    def __init__(self, playlist_name):

        self._playlist_id = playlist_name  # done
        self._playlist = sp.playlist(self._playlist_id)  # done
        self._playlist_name = self._playlist['name']  # done
        self._playlist_image = self._playlist['images'][0]['url']  # done
        self._playlist_desc = self._playlist['description']  # done
        # self._broad_track_info = self._playlist['tracks']['items']
        self._broad_track_info = []
        results = sp.playlist_tracks(self._playlist_id)
        while results:
            self._broad_track_info.extend(results['items'])
            if results['next']:
                results = sp.next(results)
            else:
                break

        Playlist.set_track_info(self)
        self._tracks = [i for i in self.track_info]
        self._artists = [i['artist'] for i in self.track_info.values()]
        self._popularities = [i['popularity'] for i in self.track_info.values()]
        self._durations = [i['duration'] for i in self.track_info.values()]
        self._combined_durations = sum(self.durations)
        self._albums = [i['album'] for i in self.track_info.values()]
        self._release_dates = [i['release date'] for i in self.track_info.values()]

        # NEW
        self._track_durations_formatted = []
        for duration_ms in self._durations:
            duration_seconds = duration_ms / 1000
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            formatted_duration = f"{int(minutes)}:{int(seconds):02d}"  # Format seconds to have leading zero if < 10
            self._track_durations_formatted.append(formatted_duration)

        # END
        self.fetch_audio_features(sp)
        self.set_mood_ratings()

        Playlist.set_df(self)
        Playlist.set_recommendations(self, sp)
        Playlist.fetch_genres(self, sp)

    # Function to extract the ID and type (e.g., playlist, track) from a Spotify URL using regex
    @staticmethod
    def id_from_url(url) -> tuple[str, str]:
        try:
            url_regex = re.search(
                r"^https?:\/\/(?:open\.)?spotify.com\/(user|episode|playlist|track|album)\/(?:spotify\/playlist\/)?(\w*)",
                url)
            return url_regex.group(2)
        except AttributeError:
            st.error("Invalid URL")  # Display an error message in the Streamlit app if the URL is invalid


    @property
    def playlist_id(self):
        return self._playlist_id

    @property
    def playlist(self) -> dict[dict]:
        return self._playlist

    @property
    def playlist_name(self):
        return self._playlist_name

    @property
    def playlist_image(self):
        return self._playlist_image

    @property
    def playlist_desc(self):
        return self._playlist_desc

    @property
    def broad_track_info(self):
        return self._broad_track_info

    def set_track_info(self):
        self._track_info = {}
        # print(self._track_info)
        for track in self._broad_track_info:
            self._track_info.update({track["track"]["name"]: {
                'artist': (", ".join([artist["name"] for artist in track["track"]["artists"]])),
                'popularity': track["track"]["popularity"],
                'duration': track["track"]["duration_ms"],
                'album': track["track"]["album"]["name"],
                'release date': track["track"]["album"]["release_date"]
            }})
        # print(self._track_info)

    @property
    def track_info(self):
        return self._track_info

    @property
    def tracks(self):
        return self._tracks

    @property
    def artists(self):
        return self._artists

    @property
    def popularities(self):
        return self._popularities

    @property
    def albums(self):
        return self._albums

    @property
    def durations(self):
        return self._durations

    @property
    def release_dates(self):
        return self._release_dates

    @property
    def track_durations_formatted(self):
        return self._track_durations_formatted

    def set_df(self):
        # Numeric and formatted durations
        numeric_durations = [duration_ms / 60000 for duration_ms in self._durations]  # Duration in minutes
        formatted_durations = []
        for duration_ms in self._durations:
            minutes = duration_ms // 60000
            seconds = (duration_ms % 60000) // 1000
            formatted_duration = f"{minutes}m {seconds}s"
            formatted_durations.append(formatted_duration)

        popularity_ranges = pd.cut(self._popularities, bins=[-1, 30, 60, 101],
                                   labels=['Hidden Gems (0-30%)', 'Common (30-60%)', 'Popular (60-100%)'])

        data = {
            "Name": self.tracks,
            "Artist": self.artists,
            "Album": self.albums,
            "Release Date": self.release_dates,
            "Popularity": self.popularities,
            "Popularity Range": popularity_ranges,
            "Duration (min)": numeric_durations,  # Numeric duration for sorting and plotting
            "Duration": formatted_durations  # Formatted duration for display
        }

        self._df = pd.DataFrame(data)

    # def set_df(self):
    # # Numeric and formatted durations
    #     numeric_durations = [duration_ms / 60000 for duration_ms in self._durations]  # Duration in minutes
    #     formatted_durations = []
    #     for duration_ms in self._durations:
    #         minutes = duration_ms // 60000
    #         seconds = (duration_ms % 60000) // 1000
    #         formatted_duration = f"{minutes}m {seconds}s"
    #         formatted_durations.append(formatted_duration)

    #     data = {
    #         "Name": self.tracks,
    #         "Artist": self.artists,
    #         "Album": self.albums,
    #         "Release Date": self.release_dates,
    #         "Popularity": self.popularities,
    #         "Duration (min)": numeric_durations,  # Numeric duration for sorting and plotting
    #         "Duration": formatted_durations  # Formatted duration for display
    #     }

    #     self._df = pd.DataFrame(data)

    @property
    def df(self):
        return self._df

    # def set_recommendations(self, sp):
    #     # Get track URI and fetch recommendations from Spotify
    #     results = sp.search(q=self.playlist, type='track')
    #     track_uri = results['tracks']['items'][0]['uri']
    #     self._recommendations = sp.recommendations(seed_tracks=[track_uri], limit=20)['tracks']

    def get_track_uris(self, sp):
        # Assume self.playlist is a dictionary containing the playlist ID
        playlist_id = self.playlist.get('id')

        if playlist_id:
            # Fetch the tracks from the playlist using the correct playlist ID
            playlist = sp.playlist_tracks(playlist_id)

            # Extract track URIs from the playlist
            track_uris = [item['track']['uri'] for item in playlist['items']]

            return track_uris
        else:
            print("No playlist ID found.")
            return []

    def set_recommendations(self, sp, limit=20):
        # Get track URIs from the playlist
        playlist_tracks = self.get_track_uris(sp)

        # Fetch recommendations from Spotify using multiple seed tracks
        if playlist_tracks:
            # Use multiple tracks as seeds for diversity
            seed_tracks = playlist_tracks[:min(5, len(playlist_tracks))]
            recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=limit)['tracks']

            # Update the recommendations attribute
            self._recommendations = recommendations
        else:
            print(f"No tracks found in the playlist. Unable to fetch recommendations.")



    @property
    def recommendations(self):
        return self._recommendations

    # def fetch_genres(self, sp):
    #     self._genres = {}
    #     for track in self._broad_track_info:
    #         for artist in track["track"]["artists"]:
    #             artist_id = artist["id"]
    #             if artist_id not in self._genres:
    #                 artist_info = sp.artist(artist_id)
    #                 self._genres[artist_id] = {
    #                     'name': artist_info['name'],
    #                     'genres': artist_info['genres']
    #                 }

    # def fetch_genres(self, sp):
    #     self._genres = {}  # to store artist's genres
    #     genre_count = {}
    #     total_tracks = 0

    #     for track in self._broad_track_info:
    #         total_tracks += 1
    #         artist_genres = set()  # To avoid counting the same genre multiple times for one track
    #         for artist in track["track"]["artists"]:
    #             artist_id = artist["id"]
    #             if artist_id not in self._genres:  # Cache the artist's genres to avoid repeated API calls
    #                 artist_info = sp.artist(artist_id)
    #                 self._genres[artist_id] = {
    #                     'name': artist_info['name'],
    #                     'genres': artist_info['genres']
    #                 }
    #             for genre in self._genres[artist_id]['genres']:
    #                 artist_genres.add(genre)

    #         for genre in artist_genres:
    #             genre_count[genre] = genre_count.get(genre, 0) + 1

    #     # Calculate the percentage of each genre
    #     self._genre_percentages = {genre: (count / total_tracks) * 100 for genre, count in genre_count.items()}

    # THIS WORKS
    def fetch_genres(self, sp):
        genre_count = {}
        total_tracks = len(self._broad_track_info)
        self._genres = {}

        for track in self._broad_track_info:
            artist_genres = set()  # Collect all unique genres for this track
            for artist in track["track"]["artists"]:
                artist_id = artist["id"]
                if artist_id not in self._genres:  # Cache the artist's genres to avoid repeated API calls
                    artist_info = sp.artist(artist_id)
                    self._genres[artist_id] = {
                        'name': artist_info['name'],
                        'genres': artist_info['genres']
                    }
                for genre in self._genres[artist_id]['genres']:

                    if 'country' in genre:
                        genre = 'Country'
                    elif 'rock' in genre:
                        genre = 'Rock'
                    elif 'rap' in genre:
                        genre = 'Rap'
                    elif 'pop' in genre:
                        genre = 'Pop'
                    elif 'hip hop' in genre:
                        genre = 'Hip hop'
                    elif 'jazz' in genre:
                        genre = 'Jazz'
                    elif 'soul' in genre:
                        genre = 'Soul'
                    elif 'metal' in genre:
                        genre = 'Metal'
                    elif 'funk' in genre:
                        genre = 'Funk'
                    elif 'indie' in genre:
                        genre = 'Indie'
                    elif 'techno' in genre:
                        genre = 'Techno'
                    elif 'dubstep' in genre:
                        genre = 'Dubstep'
                    elif 'alternative' in genre:
                        genre = 'Alt'
                    elif 'folk' in genre:
                        genre = 'Folk'
                    else:
                        genre = 'Other'
                    artist_genres.add(genre)

            # Distribute the count equally among the genres for this track
            count_per_genre = 1 / len(artist_genres) if artist_genres else 0
            for genre in artist_genres:
                genre_count[genre] = genre_count.get(genre, 0) + count_per_genre

        self._genre_percentages = {genre: (count / total_tracks) * 100 for genre, count in genre_count.items()}

    def fetch_audio_features(self, sp):
        # Filter out None or empty track IDs
        valid_track_ids = [track['track']['id'] for track in self._broad_track_info if track['track']['id']]

        # Fetch audio features in batches if necessary
        self._audio_features = {}
        for i in range(0, len(valid_track_ids), 50):  # Spotify API limits to 50 IDs per request
            batch_ids = valid_track_ids[i:i+50]
            audio_features = sp.audio_features(batch_ids)
            for track, features in zip(self._broad_track_info[i:i+50], audio_features):
                if features:
                    self._audio_features[track['track']['name']] = features

    def set_mood_ratings(self):
        # Set mood ratings based on audio features
        self._mood_ratings = {}
        for track_name, features in self._audio_features.items():
            mood = self.determine_mood(features)
            self._mood_ratings[track_name] = mood

    @staticmethod
    def determine_mood(features):
        # This is a simplistic approach; modify as needed
        if features['valence'] > 0.7 and features['energy'] > 0.6:
            return 'Happy'
        elif features['valence'] < 0.3 and features['energy'] < 0.4:
            return 'Sad'
        elif features['energy'] > 0.7:
            return 'Energetic'
        elif features['tempo'] < 100:
            return 'Chill'
        else:
            return 'Neutral'

    def calculate_mood_percentages(self):
        mood_counts = {}
        total_tracks = len(self._mood_ratings)

        # Count each mood occurrence
        for mood in self._mood_ratings.values():
            if mood in mood_counts:
                mood_counts[mood] += 1
            else:
                mood_counts[mood] = 1

        # Calculate percentages
        mood_percentages = {mood: (count / total_tracks) * 100 for mood, count in mood_counts.items()}
        return mood_percentages



@st.cache_data(show_spinner=False)
def fetch_playlists(token_info):
    sp = spotipy.Spotify(auth=token_info["access_token"])
    return sp.current_user_playlists()


def login():
    # Get the access token or redirect to Spotify login page
    token_info = sp_oauth.get_cached_token()

    # Check if the URL contains the authorization code
    url_params = st.experimental_get_query_params()
    code = url_params.get("code", None)

    if not token_info and not code:
        auth_url = sp_oauth.get_authorize_url()
        st.info("Please log in to Spotify.")
        st.markdown(f"Click [here]({auth_url}) to log in.")

    # If the URL contains the authorization code, get the access token
    if code:
        try:
            token_info = sp_oauth.get_access_token(code)
            st.success("Successfully authenticated! You can now fetch your playlists.")
        except spotipy.SpotifyException as e:
            st.error(f"Error authenticating: {e}")

    if token_info:
        # Refresh the access token if it's expired
        if sp_oauth.is_token_expired(token_info):
            try:
                token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                st.success("Successfully refreshed access token.")
            except spotipy.SpotifyException as e:
                st.error(f"Error refreshing access token: {e}")

        # Display user information
        sp = spotipy.Spotify(auth=token_info["access_token"])
        user_info = sp.me()

        if 'images' in user_info and user_info['images']:
            profile_picture_url = user_info['images'][0]['url']
            st.image(profile_picture_url, caption=user_info['display_name'], width=75)
        else:
            st.warning("User profile picture not available.")

        # Fetch and display user playlists
        playlists = fetch_playlists(token_info)

        # Create a dropdown to select a playlist
        selected_playlist_name = st.selectbox("Select a playlist:",
                                              [playlist['name'] for playlist in playlists['items']])

        return sp, selected_playlist_name  # Return the Spotify client and selected playlist name


def display_page():
    pass


def display_playlist_info(p: Playlist):
    # # Display the playlist information and cover image
    # st.write(f"## {p.playlist_name}")
    # st.image(p.playlist_image, width=250)
    # st.write(f"Description: {p.playlist_desc}")
    # st.write(f"Number of tracks: {len(p.track_info)}")
    # st.write("### Tracklist")

    # Display the playlist information and cover image
    # st.markdown(f"# {p.playlist_name}")
    # st.image(p.playlist_image, width=250)
    # st.markdown(f"**Description:** {p.playlist_desc}")
    # st.markdown(f"**Number of tracks:** {len(p.track_info)}")
    # st.markdown("## Tracklist")

    total_duration_hours = p._combined_durations // (1000 * 60 * 60)
    remaining_ms = p._combined_durations % (1000 * 60 * 60)
    remaining_minutes = remaining_ms // (1000 * 60)

    p.df.index = range(1, len(p.df) + 1)

    # Create two columns for layout
    col1, _, col2, _ = st.columns([1, 1, 2, 1])

    # Display the playlist cover and title in the left column
    with col1:
        st.image(p.playlist_image, width=250)
    # Display the rest of the information on the right column
    with col2:
        st.markdown(f"<div class='bubble' style='font-size: 24px; text-align: center;'>{p.playlist_name}</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='bubble'>Description: {p.playlist_desc}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='bubble'>Number of tracks: {len(p.track_info)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='bubble'>Total Time: {total_duration_hours} hours {remaining_minutes} minutes</div>",
                    unsafe_allow_html=True)

    # Use CSS to style text bubbles
    st.markdown(
        """
        <style>
            .bubble {
                background-color: #262730; /* Light grey background color */
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 16px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Display the interactive table
    st.markdown("<div style='font-size: 24px; text-align: center;'><div class='bubble'>Tracklist</div></div>",
                unsafe_allow_html=True)
    st.dataframe(p.df)


def display_pop_chart(p):
    # Create and display a histogram of track popularity
    popularity_percentage = p.df['Popularity Range'].value_counts(normalize=True) * 100
    fig_popularity = px.bar(
        x=popularity_percentage.index,  # Specify the x-axis variable
        y=popularity_percentage.values,  # Specify the y-axis variable
        labels={'y': 'Percentage of Songs (%)', 'x': 'Popularity Range'},
        category_orders={'x': ['Hidden Gems (0-30%)', 'Common (30-60%)', 'Popular (60-100%)']}
    )

    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Track Popularity Distribution</div>",
                unsafe_allow_html=True)

    # Display the popularity chart
    st.plotly_chart(fig_popularity)


def display_bivariate_analysis(p):
    # Set up bivariate analysis with dropdown options for x and y variables
    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Bivariate Analysis</div>",
                unsafe_allow_html=True)
    x_axis = "Duration (min)"
    y_axis = "Popularity"
    fig_bivariate = px.scatter(p.df, x=x_axis, y=y_axis, title=f"{x_axis} vs. {y_axis}", hover_name='Name',
                               hover_data={"Duration (min)": False, "Duration": True})
    st.plotly_chart(fig_bivariate)


def display_multivariate_analysis(p):
    # Set up multivariate analysis with dropdown options for color and size variables
    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Multivariate Analysis</div>",unsafe_allow_html=True)
    color_by = st.selectbox("Select a variable to color by:", ["Artist", "Album", "Release Date"])
    size_by = st.selectbox("Select a variable to size by:", ["Popularity", "Duration (min)"])
    fig_multivariate = px.scatter(p.df, x="Duration (min)", y="Popularity", color=color_by, size=size_by,
                                  hover_name="Name", title="Duration vs. Popularity Colored by Artist",
                                  hover_data={"Duration (min)": False, "Duration": True})
    st.plotly_chart(fig_multivariate)


def display_playlist_summary(p):
    # Provide a summary of the playlist, showing the most and least popular tracks
    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Playlist Summary</div>",unsafe_allow_html=True)
    st.write(
        f"**Most popular track:** {p.df.iloc[p.df['Popularity'].idxmax()]['Name']} by {p.df.iloc[p.df['Popularity'].idxmax()]['Artist']} ({p.df['Popularity'].max()} popularity)")
    st.write(
        f"**Least popular track:** {p.df.iloc[p.df['Popularity'].idxmin()]['Name']} by {p.df.iloc[p.df['Popularity'].idxmin()]['Artist']} ({p.df['Popularity'].min()} popularity)")


# def display_recommendations(p):
#     st.write("Recommended songs:")
#
#     for track in p.recommendations:
#         # Display the song name
#         st.write(track['name'])
#
#         # Create a clickable link to the Spotify song
#         spotify_url = track['external_urls']['spotify']
#         st.markdown(f"[Listen on Spotify]({spotify_url})")
#
#         # Display the image
#         st.image(track['album']['images'][0]['url'], width=120)

def display_recommendations(p):
    st.write("Recommended songs:")

    # Set the width and spacing for each column (adjust as needed)
    col_width = 300
    spacing = 20

    for i in range(0, len(p.recommendations), 2):
        # Create two columns for layout
        col1, col2 = st.columns(2)

        # Display the first song in the row
        with col1:
            display_song(p.recommendations[i], col_width, spacing)

        # Display the second song in the row if it exists
        with col2:
            if i + 1 < len(p.recommendations):
                display_song(p.recommendations[i + 1], col_width, spacing)

def display_song(track, col_width, spacing):
    # Display the song cover as a clickable image with custom HTML and CSS
    spotify_url = track['external_urls']['spotify']
    image_html = f'<a href="{spotify_url}" target="_blank"><img src="{track["album"]["images"][0]["url"]}" width="{col_width - spacing}" style="cursor:pointer;"></a>'
    st.write(f'{image_html}', unsafe_allow_html=True)

    # Display the wrapped song title starting from the left
    st.markdown(
        f"<p style='word-wrap: break-word;'>{track['name']} - {track['artists'][0]['name']}</p>",
        unsafe_allow_html=True
    )



def display_genre_pi(p):
    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Genre Percentages</div>",unsafe_allow_html=True)
    # Creating a pie chart
    fig = px.pie(
        names=p._genre_percentages.keys(),
        values=p._genre_percentages.values(),
    )

    # Showing the pie chart
    st.plotly_chart(fig)


def display_mood_pi(p):
    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Mood Percentages</div>",unsafe_allow_html=True)
    percentages = p.calculate_mood_percentages()
    # Creating a pie chart
    fig = px.pie(
        names=percentages.keys(),
        values=percentages.values(),
    )

    #Showing the pie chart
    st.plotly_chart(fig)

def display_top10_artists(p):
    artist_popularity = {}
    for track_info in p.track_info.values():
        artists = track_info['artist'].split(", ")
        for artist in artists:
            if artist in artist_popularity:
                artist_popularity[artist] += track_info['popularity']
            else:
                artist_popularity[artist] = track_info['popularity']

    max_popularity = max(artist_popularity.values())
    artist_popularity = {artist: (popularity / max_popularity) * 100 for artist, popularity in
                         artist_popularity.items()}

    sorted_artists = sorted(artist_popularity.items(), key=lambda x: x[1], reverse=True)[:10]

    top_artists, top_popularity = zip(*sorted_artists)

    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Top 10 Artists by Popularity</div>",unsafe_allow_html=True)
    df_top_artists = pd.DataFrame({'Artist': top_artists[::-1], 'Popularity': top_popularity[::-1]})
    fig = px.bar(df_top_artists, x='Popularity', y='Artist', orientation='h')
    fig.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                      marker_line_width=1.5, opacity=0.6)
    st.plotly_chart(fig)


def display_top10_songs(p):
    max_popularity = p.df['Popularity'].max()
    p.df['Popularity'] = (p.df['Popularity'] / max_popularity) * 100

    top_songs = p.df.nlargest(10, 'Popularity')

    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Top 10 Songs by Popularity</div>",unsafe_allow_html=True)
    fig = px.bar(top_songs[::-1], x='Popularity', y='Name', orientation='h')
    fig.update_traces(marker_color='rgb(255, 123, 127)', marker_line_color='rgb(165, 38, 42)',
                      marker_line_width=1.5, opacity=0.6)
    st.plotly_chart(fig)


def run(p):
    display_playlist_info(p)
    display_playlist_summary(p)
    display_pop_chart(p)
    display_bivariate_analysis(p)
    display_multivariate_analysis(p)
    display_genre_pi(p)
    display_mood_pi(p)
    display_top10_artists(p)
    display_top10_songs(p)
    display_recommendations(p)


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
        Playlist(playlist_id1)
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
        run(c.Playlist(playlist_id))
        st.success('Got playlist!')
    else:
        st.warning(f"Playlist with name '{st.session_state.selected_playlist_name}' not found.")


if __name__ == '__main__':
    main()
