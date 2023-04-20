import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# Spotify API credentials and redirect URI
creds = {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "your_redirect_uri",
    "scope": "playlist-modify-public"
}

# Initialize Spotipy client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(**creds))

# Prompt the user for an artist name
artist_name = input("Enter an artist name: ")

# Find artist
result = sp.search(artist_name, type="artist")
artist_uri = None
for artist in result["artists"]["items"]:
    if artist["name"].lower() == artist_name.lower():
        artist_uri = artist["uri"]
        break

if artist_uri is None:
    print(f"No artist found with the name '{artist_name}'.")
    exit()

# Get all album IDs and release dates for the inputted artist
album_data = {}
offset = 0
while True:
    albums = sp.artist_albums(artist_uri, offset=offset)["items"]
    if len(albums) == 0:
        break
    for album in albums:
        album_data[album["id"]] = {"release_date": album["release_date"], "artist_name": album["artists"][0]["name"]}
    offset += len(albums)
    time.sleep(0.5)  # add a delay to avoid hitting the rate limit

# Sort album IDs based on release dates
sorted_album_ids = [k for k, v in sorted(album_data.items(), key=lambda item: item[1]["release_date"])]

# Get all track IDs for sorted albums
track_ids = []
for album_id in sorted_album_ids:
    album_artists = sp.album(album_id)["artists"]
    if len(album_artists) > 0 and album_artists[0]["name"].lower() == artist_name.lower():
        tracks = sp.album_tracks(album_id)["items"]
        track_ids.extend([track["id"] for track in tracks])

# Check if playlist already exists
playlist_name = f"{artist_name} Complete Spotify Discography"
existing_playlists = sp.current_user_playlists()
for playlist in existing_playlists["items"]:
    if playlist["name"] == playlist_name:
        existing_playlist_id = playlist["id"]
        existing_track_ids = []
        existing_tracks = sp.playlist_tracks(existing_playlist_id)["items"]
        existing_track_ids.extend([track["track"]["id"] for track in existing_tracks])
        # Check for missing tracks and add them to the playlist
        missing_track_ids = list(set(track_ids) - set(existing_track_ids))
        if len(missing_track_ids) > 0:
            sp.playlist_add_items(existing_playlist_id, missing_track_ids)
        print(f"Playlist '{playlist_name}' already exists.")
        exit()

# Create a new playlist and add tracks to it in chunks of 100
playlist = sp.user_playlist_create(sp.current_user()["id"], playlist_name, public=True)
for i in range(0, len(track_ids), 100):
    sp.playlist_add_items(playlist["id"], track_ids[i:i+100])
    time.sleep(1)
