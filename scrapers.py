import os
import random
import re
from threading import Thread, Condition


from bs4 import BeautifulSoup
import consts
from cacher import SongDataCacheThread
from pageloader import HTMLScraperThread

unparsed_album_urls = []
album_urls_cv = Condition()

song_data = []
song_data_cv = Condition()


class ScrapeTopAlbumsThread(Thread):
    def __init__(self, args):
        """ Initialization for ScrapeTopAlbumsThread. Full lists for the values of parameters can be found in consts.py.

        :param g: Genre.
        :param s: Sort order.
        :param p: Page number.
        :param gn: Location filter. Uses GeoNames ID number.
        :param f: Format filter.
        :param w: Time filter.
        """
        Thread.__init__(self)
        if args.u:
            if len(args.u) != 6:
                raise ValueError(f"Expected 6 values, got {len(args.u)} instead.")
            try:
                self.g = eval(f"consts.Genre().{args.u[0]}")
                self.s = eval(f"consts.SortOrder().{args.u[1]}")
                self.p = int(args.u[2])
                self.gn = int(args.u[3])
                self.f = eval(f"consts.Format().{args.u[4]}")
                self.w = eval(f"consts.TimeFilter().{args.u[5]}")
            except Exception as e:
                print(e)
                exit(1)
        else:
            try:
                self.g = eval(f"consts.Genre().{args.g}")
                self.s = eval(f"consts.SortOrder().{args.s}")
                self.p = args.p
                self.gn = args.gn
                self.f = eval(f"consts.Format().{args.f}")
                self.w = eval(f"consts.TimeFilter().{args.w}")
            except Exception as e:
                print(e)
                exit(1)

    def gen_url(self):
        return f'https://bandcamp.com/?g={self.g}&&s={self.s}&p={self.p}&gn={self.gn}&f={self.f}&w={self.w}'

    def run(self):
        while True:
            if not unparsed_album_urls and not song_data:
                html_scraper_thread = HTMLScraperThread(self.gen_url(),
                                                        css_selector=".discover-result.client-rendered.result-current")
                html_scraper_thread.start()
                with html_scraper_thread.cv:
                    if not html_scraper_thread.html_str:
                        html_scraper_thread.cv.wait()
                html_str = html_scraper_thread.html_str
                self.p += 1
                album_urls = get_album_urls(html_str)
                with album_urls_cv:
                    unparsed_album_urls.extend(album_urls)
                    album_urls_cv.notify()


class ScrapeSongDataThread(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        while True:
            with album_urls_cv:
                while not unparsed_album_urls:
                    album_urls_cv.wait()
                album_url = unparsed_album_urls.pop(0)
            print("parsing " + album_url)
            curr_song_data = get_song_data(album_url)
            if curr_song_data:
                with song_data_cv:
                    song_data.append(curr_song_data)

    def pop_song_data(self):
        if song_data:
            with song_data_cv:
                curr_song_data = song_data.pop(0)
            return curr_song_data
        else:
            return None


class ScrapeBookmarkHTMLThread(Thread):
    def __init__(self, args):
        Thread.__init__(self)
        self.filename = args.bookmark[0]
        self.shuffle = args.shuffle
        if not os.path.isfile(self.filename):
            print(f"Bookmark file {self.filename} not found.")
            exit(1)
        with open(self.filename, 'r') as f:
            self.html_str = f.read()

    def run(self):
        soup = BeautifulSoup(self.html_str, 'html.parser')
        a_tags = soup.find_all('a')
        for a_tag in a_tags:
            url_str = str(a_tag['href'])
            if 'bandcamp.com/album/' in url_str:
                with album_urls_cv:
                    unparsed_album_urls.append(url_str)
        if self.shuffle:
            with album_urls_cv:
                random.shuffle(unparsed_album_urls)
        with album_urls_cv:
            album_urls_cv.notify()


class ScrapeFileThread(Thread):
    def __init__(self, args):
        Thread.__init__(self)
        self.filename = args.file[0]
        self.shuffle = args.shuffle
        if not os.path.isfile(self.filename):
            print(f"Text file {self.filename} not found.")
            exit(1)

    def run(self):
        with open(self.filename, 'r') as f:
            urls = f.read().splitlines()
        for url in urls:
            if 'bandcamp.com/album/' in url:
                with album_urls_cv:
                    unparsed_album_urls.append(url)
        if self.shuffle:
            with album_urls_cv:
                random.shuffle(unparsed_album_urls)
        with album_urls_cv:
            album_urls_cv.notify()


def get_album_urls(html_str: str):
    soup = BeautifulSoup(html_str, 'html.parser')
    album_links = soup.find_all('a', class_='item-title')
    urls = []
    for link in album_links:
        # Remove queries from url before appending.
        url = str(link['href']).split('?')[0]
        urls.append(url)
    return urls


def get_song_data(url):
    cached_data = SongDataCacheThread(None).get_cached_data(url)
    if cached_data:
        return cached_data

    song_data = {'album_url': url}

    html_scraper_thread = HTMLScraperThread(url)
    html_scraper_thread.start()
    with html_scraper_thread.cv:
        if not html_scraper_thread.html_str:
            html_scraper_thread.cv.wait()
    html_str = html_scraper_thread.html_str

    try:
        song_data['song_url'] = re.search(r'(?<=\"mp3-128\":\")(\\?.)*?(?=\")', html_str).group(0)
    except AttributeError:
        return None

    soup = BeautifulSoup(html_str, 'html.parser')

    song_title_link = soup.find('a', class_='title_link primaryText')
    song_data['song_title'] = str(song_title_link.span.contents[0])

    track_len_span = soup.find('span', class_='time_total')
    song_len_str = str(track_len_span.contents[0])
    try:
        song_mins, song_secs = song_len_str.split(':')
        song_data['song_len'] = int(song_mins) * 60 + int(song_secs)
    except ValueError:
        try:
            song_hrs, song_mins, song_secs = song_len_str.split(':')
            song_data['song_len'] = int(song_hrs) * 3600 + int(song_mins) * 60 + int(song_secs)
        except Exception as e:
            print(e)
            print(song_len_str)
            song_data['song_len'] = 0
    except Exception as e:
        print(e)
        print(song_len_str)
        song_data['song_len'] = 0

    album_info = soup.find('div', id='name-section')
    song_data['album_title'] = album_info.h2.contents[0].strip()
    song_data['artist'] = str(album_info.h3.span.a.contents[0])

    album_img = soup.find('a', class_='popupImage')
    song_data['img'] = album_img['href']

    cache_thread = SongDataCacheThread(song_data)
    cache_thread.start()

    return song_data
