import re
from time import sleep
from functools import reduce
from operator import add

from TwitterBot import TwitterBot
from api_key import key


def check_if_filler(tweet_text):
    """
    Given a tweet with number(s) in it, return a tweet indicating if the episode(s) is/are filler
    :param tweet_text:
    :return: text for a response tweet
    """

    def extract_episodes(canon_text):
        canon_numbers = [int(n) for n in re.findall("[0-9]+", canon_text)]
        canon_ranges = [list(range(s, t + 1)) for s, t in zip(canon_numbers[::2], canon_numbers[1::2])]
        canon_episodes = reduce(add, canon_ranges) if len(canon_ranges) is not 0 else ""
        return canon_episodes

    # sanitize -- remove floats and negatives
    tweet_text = re.sub("^-[0-9]+| -[0-9]+|[0-9]+\.[0-9]+", "", tweet_text)

    # https://www.animefillerlist.com/shows/naruto
    naruto_text = "1-25, 27-52, 54-56, 58-96, 98-98, 100-100, 107-135, 220-220"  # 220 is filler
    og_canon = extract_episodes(naruto_text)  # lol wow, it ends with a shit-ton of filler

    # source: https://www.animefillerlist.com/shows/naruto-shippuden
    shippuden_text = "1-56, 72-89, 113-143, 152-169, 172-175," \
                     " 197-222, 243-256, 261-270, 272-278," \
                     " 282-283, 296-302, 321-346, 362-375," \
                     " 378-393, 414-415, 417-421, 424-426," \
                     " 451-463, 469-479, 484-500"
    s_canon = extract_episodes(shippuden_text)

    # ranges
    tweet_ranges = re.findall("[0-9]+[-—–]+[0-9]+", tweet_text)  # find ranges
    tweet_numbers = list(extract_episodes(", ".join(tweet_ranges)))
    tweet_text = re.sub("[0-9]+[-—–]+[0-9]+", "", tweet_text)  # remove them so they aren't picked out as episodes

    # actual numbers
    tweet_raw_numbers = re.findall("[0-9]+", tweet_text)
    tweet_numbers += [int(n) for n in tweet_raw_numbers]
    tweet_numbers.sort()

    series, canon_set = ("#shippuden", s_canon) if "shippuden" in tweet_text.lower() else ("(original)", og_canon)

    def verify(ep_num):
        if series == "(original)" and ep_num is 220:
            verdict = f"Ep. {ep_num} is filler!"  # lol hardcoded
        elif ep_num > canon_set[-1] or ep_num < 1:
            verdict = f"Ep. {ep_num} doesn't exist!"
        elif ep_num in canon_set:
            verdict = f"Ep. {ep_num} is canon!"
        else:
            verdict = f"Ep. {ep_num} is filler!"
        return verdict

    if len(tweet_numbers) is 0:
        response = "Sorry, I don't see any (natural) episode numbers in your tweet. Believe it :("
    else:
        response = "\n".join([f"For #Naruto {series}:"] + [verify(episode) for episode in tweet_numbers])

    return response


if __name__ == "__main__":
    bot = TwitterBot(key)
    bot.activate(response_method=check_if_filler)
