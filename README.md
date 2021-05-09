# Plex Playlist to Collection

This script imports an existing playlist to a new or existing collection.

## Usage

`python PlexPlaylistToCollection.py [args]`

## Requirements

Requirements are outlined in requirements.txt, and can be installed via `pip install -r requirements.txt`

## Configuration

There are several required arguments, outlined below. If an argument is not passed in from the command line, it looks in the config file. If the argument is still not found, the script will interactively ask the user to provide the required values.

### Arguments

Value | Command line | Description
---|---|---
token | `-t`, `--token` | Your Plex token.
host | `--host` | The host of the Plex server. Defaults to http://localhost:32400.
section | `-s`, `--section` | The id of the library section to add the collection to.
playlist | `-p`, `--playlist` | The name of the playlist to pull items from
collection | `-c`, `--collection` | The name of the collection to create/add to
