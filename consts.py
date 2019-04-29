import argparse


class ConstList():
    def get_var_list(self):
        return [x for x in dir(self) if not x.startswith('__') and x != 'get_var_list']


class Format(ConstList):
    any_format = 'all'
    digital = 'digital'
    vinyl = 'vinyl'
    compact_disc = 'cd'
    cassette = 'cassette'


class Genre(ConstList):
    all = 'all'
    electronic = 'electronic'
    rock = 'rock'
    metal = 'metal'
    alternative = 'alternative'
    hip_hop_rap = 'hip-hop-rap'
    experimental = 'experimental'
    punk = 'punk'
    folk = 'folk'
    pop = 'pop'
    ambient = 'ambient'
    soundtrack = 'soundtrack'
    world = 'world'
    jazz = 'jazz'
    acoustic = 'acoustic'
    funk = 'funk'
    r_b_soul = 'r-b-soul'
    devotional = 'devotional'
    classical = 'classical'
    raggae = 'raggae'
    podcasts = 'podcasts'
    country = 'country'
    spoken_word = 'spoken-word'
    comedy = 'comedy'
    blues = 'blues'
    kids = 'kids'
    audiobooks = 'audiobooks'
    latin = 'latin'


class SortOrder(ConstList):
    best_selling = 'top'
    new_arrivals = 'new'
    artist_recommended = 'rec'


class TimeFilter(ConstList):
    today = -1
    this_week = 0
    last_week = 557
    two_weeks_ago = 556
    three_weeks_ago = 555
    four_weeks_ago = 554
    five_weeks_ago = 553
    six_weeks_ago = 552


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Shows Bandcamp constants.')
    parser.add_argument('-c', dest='c', nargs=1, type=str, default=None,
                        help="Specifies the class to show.")

    args = parser.parse_args()

    classes = [x for x in dir() if x[0].isupper() and x != 'ConstList']
    if not args.c:
        print("ConstList members (use -c argument to specify ConstList (case-sensitive):")
        for c in classes:
            print(f" - {c}: {eval(f'{c}().get_var_list()')}")
    else:
        user_class = args.c[0]
        if user_class not in classes:
            print("Please specify a valid class (case-sensitive):")
            for c in classes:
                print(f' - {c}')
        else:
            print(f'{user_class} members:')
            for item in eval(f'{user_class}().get_var_list()'):
                print(f' - {item}')
