import argparse
import time
from io import BytesIO
from threading import Thread

import requests
import vlc
from PIL import Image
from scrapers import ScrapeTopAlbumsThread, ScrapeSongDataThread, ScrapeBookmarkHTMLThread, ScrapeFileThread

SEPARATOR = ' | '

playing_status_codes = {1, 2, 3, 4}


class VLCPlayerThread(Thread):
    def __init__(self, args):
        Thread.__init__(self)
        self.skiplong = args.skiplong
        self.maxlen = args.maxlen
        self.curr_song_data = None

    def run(self):
        while True:
            self.get_new_song_data()

            if self.skiplong and self.curr_song_data['song_len'] > self.maxlen:
                print(f"Skipping song {self.curr_song_data['artist']} - {self.curr_song_data['song_title']} "
                      f"(length longer than max length [{self.song_len_to_timestamp()}>"
                      f"{self.song_len_to_timestamp(self.maxlen)}]).")
                continue
            self.song_data_to_file()
            self.play_song()

    def get_new_song_data(self):
        while True:
            self.curr_song_data = ScrapeSongDataThread().pop_song_data()
            if self.curr_song_data:
                break

    def song_len_to_timestamp(self, total_seconds=None):
        if not total_seconds:
            total_seconds = self.curr_song_data['song_len']
        song_min, song_sec = total_seconds // 60, total_seconds % 60
        return f"{song_min:02}:{song_sec:02}"

    def play_song(self):
        print(f"playing {self.curr_song_data['artist']} - {self.curr_song_data['song_title']} "
              f"({self.song_len_to_timestamp()})")
        try:
            r = requests.get(self.curr_song_data['song_url'], stream=True)
            found = r.ok
        except ConnectionError as e:
            print(f'failed to get stream: {e}')
            return

        if found:
            player = vlc.MediaPlayer(self.curr_song_data['song_url'])
            player.play()

            time.sleep(5)  # Give it time to get going
            while True:
                curr_time = player.get_time() // 1000
                if curr_time > self.maxlen:
                    break

                state = player.get_state()
                if state not in playing_status_codes:
                    break
            player.stop()

    def song_data_to_file(self):
        out = f"{self.curr_song_data['artist']} - {self.curr_song_data['song_title']}{SEPARATOR}"
        with open('curr_song.txt', 'w+') as f:
            f.write(out)

        out = f"{self.curr_song_data['album_url']}\n"
        with open('history.txt', 'a+') as f:
            f.write(out)

        img = Image.open(BytesIO(requests.get(self.curr_song_data['img']).content))
        if img:
            img = img.resize((256, 256), Image.ANTIALIAS)
            img.save('curr_album.png')


def init_threads(args):
    get_album_urls_threads = 2 * [None]
    for i in range(len(get_album_urls_threads)):
        get_album_urls_threads[i] = ScrapeSongDataThread()
        get_album_urls_threads[i].start()

    if args.bookmark:
        bookmark_thread = ScrapeBookmarkHTMLThread(args)
        bookmark_thread.start()
    elif args.file:
        file_thread = ScrapeFileThread(args)
        file_thread.start()
    else:
        top_songs_thread = ScrapeTopAlbumsThread(args)
        top_songs_thread.start()

    vlc_player_thread = VLCPlayerThread(args)
    vlc_player_thread.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plays music from Bandcamp.')
    parser.add_argument('--bookmark', dest='bookmark', nargs=1, type=str, default=None,
                        help="Play Bandcamp albums from list of bookmarks.")
    parser.add_argument('--file', dest='file', nargs=1, type=str, default=None,
                        help="Play Bandcamp albums from a txt file.")
    parser.add_argument('--shuffle', dest='shuffle', action='store_true',
                        help='Shuffles the order of albums in bookmark or file mode.')
    parser.add_argument('--skiplong', dest='skiplong', action='store_true',
                        help='Skips long songs instead of truncating them.')
    parser.add_argument('--maxlen', dest='maxlen', type=int, nargs=1, default=360,
                        help='Max length in seconds for each song. (Default: 360).')
    parser.add_argument('-g', dest='g', nargs=1, default='all',
                        help="Genre filter (Default: 'all' ).")
    parser.add_argument('-s', dest='s', nargs=1, default='best_selling',
                        help="Sort order (Default: 'best_selling').")
    parser.add_argument('-p', dest='p', nargs=1, default=0, help='Starting page number (Default: 0).')
    parser.add_argument('-gn', dest='gn', nargs=1, default=0, help='GeoName tag filer (Default: 0).')
    parser.add_argument('-f', dest='f', nargs=1, default='any_format',
                        help="Format filter (Default: 'any_format').")
    parser.add_argument('-w', dest='w', nargs=1, default='this_week',
                        help="Time filter (Default: 'this_week').")
    parser.add_argument('-u', dest='u', nargs='+', default=None,
                        help="Combines the previous 6 arguments (-g, -s, -p, -gn, -f, -w).")
    args = parser.parse_args()

    init_threads(args)
