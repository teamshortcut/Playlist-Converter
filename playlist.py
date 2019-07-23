import gmusicapi
import spotipy
import spotipy.util as util
import requests
import re
import os
import string
import json

#CONSTANTS
SCOPE = "user-library-read playlist-modify-public playlist-read-collaborative playlist-read-private playlist-modify-private"
URL_REGEX_PATTERN = "^(https://open.spotify.com/playlist/).+$"

#Fill these in!
SPOTIPY_CLIENT_ID = "XXXX"
SPOTIPY_CLIENT_SECRET = "XXXX"
SPOTIPY_REDIRECT_URI = "http://localhost/"
USERNAME = "user"
ANDROID_MAC_ADDRESS = "XXXX"

#Authenticates Spotify and Google Play Music
token = util.prompt_for_user_token(USERNAME, SCOPE, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)
api = gmusicapi.Mobileclient()

#Checks for existing Google Play credentials, using them if found or creating them otherwise
if not(os.path.exists("creds") and os.path.isfile("creds")):
    result = api.perform_oauth("creds", True)
else:
    result = api.oauth_login(oauth_credentials="creds", device_id=ANDROID_MAC_ADDRESS)

if not result:
    print("Google Play authentication error.")
    quit()

#FUNCTIONS
def extractSpotifyIDFromURL(url):
    return url.split("https://open.spotify.com/playlist/")[1]

#Checks for a matching (close enough) title between two strings - e.g. a track name
def matchTitle(string1, string2):
    #Try lowercase matching
    string1 = string1.lower()
    string2 = string2.lower()

    if string1 == string2:
        return True
    #Check for extended title
    if string1 in string2 or string2 in string1:
        return True
    
    #Try removing punctuation
    string1 = string1.translate(str.maketrans(dict.fromkeys(string.punctuation)))
    string2 = string2.translate(str.maketrans(dict.fromkeys(string.punctuation)))

    if string1 == string2:
        return True
    if string1 in string2 or string2 in string1:
        return True

    #Try removing whitespace
    string1 = ''.join(string1.split())
    string2 = ''.join(string2.split())

    if string1 == string2:
        return True
    if string1 in string2 or string2 in string1:
        return True

    return False #no match

#Gets playlist (owned by the user) object from a Spotify URL
#def findOwnedSpotifyPlaylist(url):
    # targetPlaylist = None
    # playlistID = extractSpotifyIDFromURL(url)
    # print(playlistID)

    # #Gets all playlists for user
    # playlists = spotify.user_playlists(USERNAME)

    # #Iterate through all playlists to find one with matching ID
    # for playlist in playlists["items"]:
    #     if playlist["owner"]["id"] == USERNAME:
    #         if playlist["id"] == playlistID:
    #             targetPlaylist = playlist
    #             print(targetPlaylist["name"] + " - " + targetPlaylist["id"])

    # return targetPlaylist

#Gets playlist object from a Spotify URL
def findSpotifyPlaylist(url):
    targetPlaylist = None
    playlistID = extractSpotifyIDFromURL(url)

    auth = util.oauth2.SpotifyClientCredentials(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
    token = auth.get_access_token()
    headers = {"Authorization": "Bearer "+token}
    response = requests.get("https://api.spotify.com/v1/playlists/"+playlistID, headers=headers)
    
    if response.status_code == 200:
        targetPlaylist = response.json()
        return targetPlaylist
    else:
        return None

#Request input for (Spotify) playlist URL and validate it
def acceptPlaylistURL():
    while True: #loop until valid (at which point simply return)
        playlistURL = input("Please enter the URL of the playlist: ")
        if re.match("^(https://open.spotify.com/playlist/).+$", playlistURL): #checks valid playlist URL
            return playlistURL
        else:
            print("Please input a valid Spotify playlist URL.")

#Extracts album, artist and track names for each item in a (Spotify) playlist
def getInfoFromSpotifyPlaylist(targetPlaylist):
    playlistItems = []

    #Get the tracks from the specified playlist
    tracks = spotify.user_playlist_tracks(USERNAME, playlist_id=targetPlaylist["id"])
    length = tracks["total"] #number of tracks
    for i in range(length):
        current = tracks["items"][i]["track"] #current track
        albumName = current["album"]["name"] #dict
        artistName = current["album"]["artists"][0]["name"] #list
        trackName = current["name"]

        #Save album, artist and track name for current track, and add to array of tracks
        playlistItem = [albumName, artistName, trackName]
        playlistItems.append(playlistItem)

    return playlistItems

#Adds a track (array with album, artist and track name) to a Google Play Music playlist with specified ID
def addSongsToGooglePlaylistFromInfo(playlist_id, track):
    #track should be array with 3 elements
    albumName = track[0]
    artistName = track[1]
    trackName = track[2]

    print(albumName + " - " + artistName + " - " + trackName)

    library = api.get_all_songs()
    track_ids = []

    #Looks for matching track in Google Play library
    for track in library:
        if matchTitle(track["album"], albumName) and matchTitle(track["albumArtist"], artistName) and matchTitle(track["title"], trackName):
            track_ids.append(track["id"]) #gets track ID
            api.add_songs_to_playlist(playlist_id, track_ids) #adds track to playlist
            return True
    return False #could not find track in library

#If Spotify successfully authenticated
if token:
    spotify = spotipy.Spotify(auth=token)

    #Gets Spotify playlist from inputted URL
    playlistURL = acceptPlaylistURL()
    targetPlaylist = findSpotifyPlaylist(playlistURL)

    if targetPlaylist == None:
        print("No matching playlist found.")
    else:
        print("Matching playlist found.")

        #Get playlist metadata
        playlistName = targetPlaylist["name"]
        try:
            playlistDescription = targetPlaylist["description"]
        except:
            playlistDescription = ""

        #Get information on tracks in playlist
        playlistItems = getInfoFromSpotifyPlaylist(targetPlaylist)

        #Create new Google Play playlist
        playlist_id = api.create_playlist(name=playlistName, description=playlistDescription)
        failures = [] #Stores the tracks that could not be found in Google Play library
        for i in playlistItems: #add each track to Google Play playlist
            if not addSongsToGooglePlaylistFromInfo(playlist_id, i): #could not find track
                failures.append(i)

        if failures: #output any tracks that could not be found
            print("Certain tracks could not be found in the Google Play library.")
            for i in failures:
                print(failures[i][0] + " - " + failures[i][1] + " - " + failures[i][2])

else:
    print("Spotify authentication error.")
    quit()