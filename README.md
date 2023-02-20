# Plex Playlist to Collection

Import an existing playlist to a new or existing collection.

## Requirements

[Python 3.10](https://www.python.org/downloads/) or later.

Python package requirements are outlined in requirements.txt, and can be installed via `pip install -r requirements.txt`

## Usage
`python PlexPlaylistToCollection.py [args]`

### Arguments

There are three ways to specify arguments:

1. As command line arguments, outlined in the table below
2. From config.yml, outlined in the table below
3. Interactively when running the script

If the arguments are not found in the command line, it will look in config.yml. If it's still not found, the script will ask you to provide the values. Additionally, for `section` and `playlist`, if no value is provided, the script will print a list of available values for you to choose from.

Value | Command line | config.yaml |Description
---|---|---|---
token | `-t`, `--token` | `token` | Your Plex token (see [finding an authentication token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)).
host | `--host` | `host` | The host of the Plex server. Defaults to http://localhost:32400.
section | `-s`, `--section` | `section` | The id of the library section to add the collection to.
playlist | `-p`, `--playlist` | `playlist` | The name of the playlist to pull items from
collection | `-c`, `--collection` | `collection` | The name of the collection to create/add to
filter-to  | `--filter-to` | `filter_to` | Optionally filter existing playlists based on their type. Can either be `video` or `audio`.

<br>

<details><summary>Expand to view example console output</summary>

```
> git clone https://github.com/danrahn/PlexPlaylistToCollection.git
Cloning into 'PlexPlaylistToCollection'...
...
> cd PlexPlaylistToCollection
> python PlexPlaylistToCollection.py

Enter your Plex token: XYZ

Available Playlists:

[1] MyPlaylist1
[2] MyPlaylist2
[3] MyPlaylist3

Select a playlist (-1 to cancel, prepend 'L' to list the items in the playlist): L2

Items in "MyPlaylist2":
    MyMovie1
    MyMovie2
    MyMovie3

[1] MyPlaylist1
[2] MyPlaylist2
[3] MyPlaylist3

Select a playlist (-1 to cancel, prepend 'L' to list the items in the playlist): 2

Selected MyPlaylist2

Choose a library to add the collection to.
NOTE: Only playlist items part of the chosen library will be added to the collection.

Available Libraries:

[1] Movies
[3] TV Shows

Enter the library number (-1 to cancel): 1

Selected "Movies"

Enter the collection name: MyCollection

Create a new collection "MyCollection" and add all applicable items from your playlist to it (y/n)? y

Adding 3 items to collection "MyCollection"

Added "MyMovie1" to "MyCollection"
Added "MyMovie2" to "MyCollection"
Added "MyMovie3" to "MyCollection"

Done!
>
```

</details>
