from threading import Thread, Condition

import json

CACHE_FILE = 'song_data.json'


class SongDataCacheThread(Thread):
    cv = Condition()

    def __init__(self, song_data):
        Thread.__init__(self)
        self.cache_file = CACHE_FILE
        self.song_data = song_data

    def run(self):
        try:
            with open(self.cache_file, 'r') as f:
                cached_song_data = json.load(f)
        except FileNotFoundError:
            cached_song_data = {"cache": []}
        for cached_song in cached_song_data["cache"]:
            if cached_song["album_url"] == self.song_data["album_url"]:
                break
        else:
            with self.cv:
                cached_song_data["cache"].append(self.song_data)
                with open(self.cache_file, 'w+') as f:
                    json.dump(cached_song_data, f)

    def get_cached_data(self, url):
        with self.cv:
            try:

                with open(self.cache_file, 'r') as f:
                    cached_song_data = json.load(f)
                for cached_song in cached_song_data["cache"]:
                    if cached_song["album_url"] == url:
                        return cached_song
                else:
                    return None
            except FileNotFoundError:
                return None
            except KeyError:
                return None
