import sys
import os
import argparse
import requests
import time
from urllib import parse
# import urllib
import urllib3
import yaml
import json

class PlaylistToCollection:
    def __init__(self):
        self.get_config()


    def get_config(self):
        """Reads the config file from disk"""

        self.valid = False
        config_file = self.adjacent_file('config.yml')
        config = None
        if not os.path.exists(config_file):
            print('WARN: Could not find config.yml! Make sure it\'s in the same directory as this script')
        else:
            with open(config_file) as f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
        
        if not config:
            config = {}

        parser = argparse.ArgumentParser()
        parser.add_argument('--host')
        parser.add_argument('-t', '--token')
        parser.add_argument('-p', '--playlist')
        parser.add_argument('-s', '--section')
        parser.add_argument('-c', '--collection')
        self.cmd_args = parser.parse_args()
        self.token = self.get_config_value(config, 'token', prompt='Enter your Plex token')
        self.host = self.get_config_value(config, 'host', 'http://localhost:32400')
        self.section_id = self.get_config_value(config, 'section', default=None)
        if self.section_id.isnumeric():
            self.section_id = int(self.section_id)
        self.playlist_name = self.get_config_value(config, 'playlist', default=None)
        self.collection_name = self.get_config_value(config, 'collection', default=None)
        self.valid = True

    def get_config_value(self, config, key, default='', prompt=''):
        cmd_arg = None
        if key in self.cmd_args:
            cmd_arg = self.cmd_args.__dict__[key]

        if key in config and config[key] != None:
            if cmd_arg != None:
                # Command-line args shadow config file
                print(f'WARN: Duplicate argument "{key}" found in both command-line arguments and config file. Using command-line value ("{self.cmd_args.__dict__[key]}")')
                return cmd_arg
            return config[key]

        if cmd_arg != None:
            return cmd_arg

        if default == None:
            return ''

        if len(default) != 0:
            return default

        if len(prompt) == 0:
            return input(f'\nCould not find "{key}" and no default is available.\n\nPlease enter a value for "{key}": ')
        return input(f'\n{prompt}: ')


    def run(self):
        """Kick off the processing"""

        if not self.valid:
            return

        print()

        if len(self.token) == 0:
            self.token = input('Enter your Plex token: ')
            print('Plex token set!\n')

        if not self.test_plex_connection():
            return

        playlist = self.find_playlist()
        if not playlist:
            print('Unable to find the right playlist, exiting...')
            return

        section = self.get_section()
        if not section:
            print('Unable to find the right library section, exiting...')
            return

        self.collection_name = self.get_collection_name(section)
        if self.collection_name == None:
            print('Unable to get the right collection, exiting...')
            return

        added = self.add_playlist_items_to_collection(section, playlist)
        if not added:
            print('Unable to add items to collection, exiting...')

        print('\nDone!')


    def test_plex_connection(self):
        """
        Does some basic validation to ensure we get a valid response from Plex with the given
        host and token.
        """

        status = None
        try:
            status = requests.get(self.url('/')).status_code
        except requests.exceptions.ConnectionError:
            print(f'Unable to connect to {self.host} ({sys.exc_info()[0].__name__}), exiting...')
            return False
        except:
            print(f'Something went wrong when connecting to Plex ({sys.exc_info()[0].__name__}), exiting...')
            return False

        if status == 200:
            return True

        if status == 401 or status == 403:
            print('Could not connect to Plex with the provided token, exiting...')
        else:
            print(f'Bad response from Plex ({status}), exiting...')
        return False


    def find_playlist(self):
        """
        Checks whether the provided playlist exists and returns it.
        If the playlist does not exist, or none was provided, ask the user to select one
        """

        playlists = self.get_json_response('/playlists', { 'playlistType' : 'video' })
        if not playlists:
            print('Could not get playlists from server.')
            return None
        if 'size' not in playlists or playlists['size'] == 0:
            print('No playlists found.')
            return None
        if 'Metadata' not in playlists:
            print('Error reading playlists from server.')
            return None

        matches = []
        find = self.playlist_name
        if len(find) != 0:
            for playlist in playlists['Metadata']:
                if playlist['title'].lower() == find.lower():
                    matches.append(playlist)

        count = len(matches)
        if count == 1:
            return matches[0]

        if count == 0:
            if len(find) == 0:
                print('Available Playlists:\n')
            else:
                if not self.get_yes_no(f'Sorry, we could not find a playlist by the name of "{find}". List playlists'):
                    return None

            ret = self.select_playlist(playlists['Metadata'], lambda x: x['title'])
            if ret:
                self.playlist_name = ret['title']
                print(f'\nSelected {self.playlist_name}\n')
            return ret

        print('Multiple matching playlists found:\n')
        display_function = lambda x: f'{x["title"]} ({x["leafCount"]} items, created {time.strftime("%Y-%m-%d", time.localtime(int(x["addedAt"])))})'
        ret = self.select_playlist(matches, display_function)
        self.playlist_name = ret['title']
        print(f'\nSelected {self.playlist_name}\n')
        return ret


    def select_playlist(self, items, display_fn):
        """Prompts the user to select a playlist to import from, optionally listing the items in a particular playlist"""
        for i in range(len(items)):
            print(f'[{i + 1}] {display_fn(items[i])}')

        choice = input(f'\nSelect a playlist (-1 to cancel, prepend \'L\' to list the items in the playlist): ')
        while not choice.isnumeric() or int(choice) < 1 or int(choice) > len(items):
            if choice == '-1':
                return None
            elif choice[0].lower() == 'l' and len(choice) > 1:
                choice = choice[1:]
                if choice.isnumeric() and int(choice) > 0 and int(choice) <= len(items):
                    self.print_playlist_items(items[int(choice) - 1])
                    print()
                    for i in range(len(items)):
                        print(f'[{i + 1}] {display_fn(items[i])}')
                    choice = input(f'\nSelect a playlist (-1 to cancel, prepend \'L\' to list the items in the playlist): ')
            else:
                choice = input('Invalid number, please try again (-1 to cancel): ')

        return items[int(choice) - 1]


    def print_playlist_items(self, playlist):
        """Prints all items in the given playlist"""
        print()
        print(f'Items in "{playlist["title"]}":')
        playlist_items = self.get_json_response(playlist['key'])
        if not playlist_items:
            print('\tSomething went wrong. Could not list playlist items\n')
            return

        if 'Metadata' not in playlist_items:
            print('\tNo items found in playlist\n')
            return

        for item in playlist_items['Metadata']:
            print(f'\t{item["title"]}')
        print()


    def get_section(self):
        """Returns the section object that the collection will be added to"""
        sections = self.get_json_response('/library/sections')
        if not sections or 'Directory' not in sections:
            return None

        sections = sections['Directory']
        find = self.section_id
        if type(find) == int:
            for section in sections:
                if int(section['key']) == int(find):
                    print(f'Found section {find}: "{section["title"]}"')
                    return section

            print(f'Provided library section {find} could not be found...\n')

        print('\nChoose a library to add the collection to.\nNOTE: Only playlist items part of the chosen library will be added to the collection.\n\nAvailable Libraries:\n')
        choices = {}
        for section in sections:
            print(f'[{section["key"]}] {section["title"]}')
            choices[int(section['key'])] = section
        print()

        choice = input('Enter the library number (-1 to cancel): ')
        while not choice.isnumeric() or int(choice) not in choices:
            if choice == '-1':
                return None
            choice = input('Invalid section, please try again (-1 to cancel): ')

        self.section_id = int(choice)
        print(f'\nSelected "{choices[int(choice)]["title"]}"\n')
        return choices[int(choice)]


    def get_collection_name(self, section):
        """Gets the collection name to add items to"""
        collection_name = self.collection_name
        if len(collection_name) == 0:
            collection_name = input('Enter the collection name: ')
        collections = self.get_json_response(f'/library/sections/{section["key"]}/collections')
        if not collections:
            return None

        match = None
        if collections['size'] != 0:
            for collection in collections['Metadata']:
                if collection_name.lower() == collection['title'].lower(): # Assume they meant to add to an existing collection if the names are equal, ignoring case
                    match = collection
                    collection_name = collection['title']
                    break

        confirm = False
        print()
        if match == None:
            confirm = self.get_yes_no(f'Create a new collection "{collection_name}" and add all applicable items from your playlist to it')
        else:
            confirm = self.get_yes_no(f'"{collection_name}" already exists. Add applicable items from your playlist to it')

        return collection_name if confirm else None

    def add_playlist_items_to_collection(self, section, playlist):
        """Adds all applicable items from the given playlist to the specificed collection"""
        print(f'\nAdding {playlist["leafCount"]} items to collection "{self.collection_name}"\n')
        playlist_items = self.get_json_response(playlist['key'])
        if not playlist_items or 'Metadata' not in playlist_items:
            return False
        for item in playlist_items['Metadata']:
            if int(item['librarySectionID']) != int(section['key']):
                print(f'Not adding {item["title"]} to collection, as it is not in the library "{section["title"]}" ({item["librarySectionID"]} vs {section["key"]})')
                continue
            current_collections = self.get_item_collections(item)
            if current_collections == None:
                print(f'Error getting existing collections for "{item["title"]}", moving on...')
                continue
            if self.collection_name in current_collections:
                print(f'{item["title"]} already exists in "{self.collection_name}"')
                continue
            if not self.add_item_to_collection(item, current_collections):
                print(f'Unable to add "{item["title"]}" to "{self.collection_name}", moving on...')
                continue

            print(f'Added "{item["title"]}" to "{self.collection_name}"')

        return True

    def get_item_collections(self, item):
        """Returns a list of collections that the given item belongs to"""
        data = self.get_json_response(item['key'])
        if not data:
            return None

        collections = []
        if 'Metadata' not in data:
            return collections
        for metadata in data['Metadata']:
            if 'Collection' not in metadata:
                continue
            for collection in metadata['Collection']:
                collections.append(collection['tag'])
        return collections


    def add_item_to_collection(self, item, collections):
        """Adds the given item to the new collection"""
        key = item['key']
        metadata_id = key[key.rfind('/') + 1:]
        base = f'/library/sections/{self.section_id}/all'
        type_to_int = { 'movie' : '1', 'show' : '2', 'season' : '3', 'episode' : '4' }
        if item['type'] not in type_to_int:
            return False
        params = { 'type' : type_to_int[item['type']], 'id' : metadata_id }
        for index in range(len(collections)):
            params[f'collection%5B{index}%5D.tag.tag'] = collections[index]
        params[f'collection%5B{len(collections)}%5D.tag.tag'] = self.collection_name
        options = requests.options(self.url(base, params))
        put = requests.put(self.url(base, params))
        put.close()
        options.close()
        return True

    def get_json_response(self, url, params={}):
        """Returns the JSON response from the given URL"""
        response = requests.get(self.url(url, params), headers={ 'Accept' : 'application/json' })
        if response.status_code != 200:
            data = None
        else:
            try:
                data = json.loads(response.content)['MediaContainer']
            except:
                print('ERROR: Unexpected JSON response:\n')
                print(response.content)
                print()
                data = None

        response.close()
        return data

    def url(self, base, params={}):
        """Builds and returns a url given a base and optional parameters. Parameter values are URL encoded"""
        real_url = f'{self.host}{base}'
        sep = '?'
        for key, value in params.items():
            real_url += f'{sep}{key}={parse.quote(value)}'
            sep = '&'

        return f'{real_url}{sep}X-Plex-Token={self.token}'

    def get_yes_no(self, prompt):
        """Prompt the user for a yes/no response, continuing to show the prompt until a value that starts with 'y' or 'n' is entered"""

        while True:
            response = input(f'{prompt} (y/n)? ')
            ch = response.lower()[0] if len(response) > 0 else 'x'
            if ch in ['y', 'n']:
                return ch == 'y'

    def adjacent_file(self, filename):
        """Returns the file path for a file that is in the same directory as this script"""

        return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) + os.sep + filename

if __name__ == '__main__':
    runner = PlaylistToCollection()
    runner.run()