# Playlist Converter
A Python script to convert/copy playlists from Google Play Music to Spotify, and vice versa.

## Description
The script is intended to recreate playlists made in Spotify in Google Play Music, and in reverse. When using Google Play, it is designed to be used with a library of locally uploaded music, and is untested with music from a Google Play Music subscription. The script simply asks for the URL (Spotify) or name (Google Play) of the playlist, and will then recreate it on the other platform. Any titles that cannot be found (that are not available on Spotify or could not be found in the user's Google Play Music library) will be ignored and displayed, to be manually fixed if possible.

## Setup
Other than creating playlists to convert, the only setup this script requires is authenticating Spotify and Google Play Music.
To authenticate Spotify, you will need to create a Spotify Application, and fill in your _Client ID_ and _Client Secret_. (_Redirect URI_ can be left as the default, or can be changed if desired) More details on this process can be found [here](https://spotipy.readthedocs.io/en/latest/#authorized-requests). You will also need to fill in your Spotify username. (this does not need to be a Premium account)
To authenticate Google Play Music, you will need a 16 digit string of hex for an Android MAC address, or an iOS UUID in the form `ios:<uuid>`. More details on the exact requirements for this can be found [here](https://spotipy.readthedocs.io/en/latest/#authorized-requests), but it is worth noting that running the program with an invalid MAC address may prompt a recommended alternative to use.

Once these variables have been filled in, make sure all dependencies are satisfied, then simply run the Python script.
```python
#Fill these in!
SPOTIPY_CLIENT_ID = "XXXX"
SPOTIPY_CLIENT_SECRET = "XXXX"
SPOTIPY_REDIRECT_URI = "http://localhost/"
USERNAME = "user"
ANDROID_MAC_ADDRESS = "XXXX"
```

## Dependencies
The program has been tested with Python 3.7, but is likely to work with other versions as well. The following libraries are required to use this program:
* [spotipy](https://spotipy.readthedocs.io/en/latest/) - A Python wrapper for Spotify's API
* [gmusicapi](https://unofficial-google-music-api.readthedocs.io/en/latest) - An (unofficial) API to interact with Google Play Music through Python
* [requests](http://docs.python-requests.org/en/master/) - Used for requests to Spotify's API
These can be automatically installed by running the below command.
```pip install -r requirements.txt```

## Usage
To use the script, simply run `python playlist.py`, and follow the instructions. You will need to have a Spotify playlist (and its URL), or a Google Play Music playlist created. Plesae note that if this playlist does not have a unique title, it may not be correctly found. Any titles that could not be found on Spotify or in the user's Google Play Music library will be displayed. This may be because they are not present, or that the metadata (track, album or artist name) differs between platforms.

---
This project is licensed under the terms of the MIT license, which can be found in the LICENSE.txt file in the root of the repository.