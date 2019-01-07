import sys
from datetime import datetime
from threading import Thread
from time import sleep, strftime

import tweepy
from tweepy import TweepError

# CONSTANTS
TWEET_MAX_LENGTH = 280


class TwitterBot:
    def __init__(self, api_keys, active_hours=range(24)):
        self.keys = api_keys
        self.active = active_hours
        self.api, self.me = self._verify()
        self.log_file = f"{self.me}.log"

    def _verify(self):
        """
        Verifies that the user has valid credentials for accessing Tweepy API
        :return: a tuple containing an API object and the handle of the bot
        """

        def loading():
            for _ in range(3):
                print(Colors.yellow("."), end="")
                sys.stdout.flush()
                sleep(0.5)

        sys.stdout.write(Colors.yellow("verifying credentials"))
        thread = Thread(target=loading())  # lol
        thread.daemon = True  # kill this thread if program exits
        thread.start()

        api = self._authorize()
        try:
            me = api.me().screen_name
        except TweepError as e:
            raise ValueError("API might be disabled or you have invalid keys:"
                             f"\n\t{self._extract_tweepy_error(e)}")

        thread.join()  # lol
        print(Colors.white(" verified\n") +
              Colors.cyan("starting up bot ") + Colors.white(f"@{me}!\n"))
        return api, me  # api, the bot's handle

    def _authorize(self):
        """
        Uses keys to create an API accessor and returns it
        :return: an API object used to access the Twitter API
        """
        auth = tweepy.OAuthHandler(self.keys["consumer_key"], self.keys["consumer_secret"])
        auth.set_access_token(self.keys["access_token"], self.keys["access_token_secret"])
        return tweepy.API(auth)

    def _is_replied(self, tweet):
        """
        Check if a tweet has been replied to (favorite'd)
        :param tweet: the status object to check the reply status of
        :return: a boolean value indicating if the status has been replied to
        """
        favorites = [x.id for x in self.api.favorites()]
        return tweet.id in favorites

    def _mark_replied(self, tweet_id):
        """
        Favorites a tweet to mark it "replied" to. This prevents the bot from replying more than once
        :param tweet_id: the tweet that has been addressed
        """
        self.api.create_favorite(tweet_id)

    def clear_tweets(self):
        """
        DANGER: removes all tweets from current bot account
        """
        response = None
        while response != "y":
            response = input(Colors.red("ARE YOU SURE YOU WANT TO ERASE ALL TWEETS? (y/n)"))

        for status in tweepy.Cursor(self.api.user_timeline).items():
            try:
                self.api.destroy_status(status.id)
                print(Colors.white("deleted successfully"))
            except TweepError:
                print(Colors.red(f"failed to delete: {status.id}"))

    def clear_favorites(self):
        """
        DANGER: removes all favorites from current bot account
        """
        response = None
        while response != "y":
            response = input(Colors.red("ARE YOU SURE YOU WANT TO ERASE ALL FAVORITES? (y/n)"))
        [self.api.destroy_favorite(x.id) for x in self.api.favorites()]
        print(Colors.white("erased all favorites"))

    def is_active(self):
        """
        The bot tries not to tweet at times when no one will see
        :return: whether the bot is in its active period
        """
        current_time = datetime.now().hour
        early = self.active[0]
        late = self.active[-1]
        return early <= current_time < late

    @staticmethod
    def _divide_tweet(long_tweet, at=None):
        """
        A method for exceptionally long tweets
        :rtype: the number of tweets, followed by the tweets
        :param at: the person you're responding to/at
        :param long_tweet: the long-ass tweet you're trying to make
        :return: the number of tweets and an array of tweets
        """

        # too big!
        if len(long_tweet) > 1400:
            return 0, None

        handle = f"@{at} " if at else ""

        def make_new_tweet(sentence_list):
            tweet = list()
            while len(sentence_list) > 0 and len("\n".join(tweet)) + len(sentence_list[0] + " ") <= TWEET_MAX_LENGTH:
                tweet.append(sentence_list.pop(0))
            return "\n".join(tweet)

        tweets = list()
        verdicts = long_tweet.split("\n")
        verdicts[0] = handle + verdicts[0]
        while len(verdicts) > 0:
            tweets.append(make_new_tweet(verdicts))
        return len(tweets), tweets

    def activate(self, response_method, sleep_interval=60):
        """polls for tweets at self and tries to respond to them"""
        if not callable(response_method):
            raise ValueError("response_method must be a function that "
                             "takes a body of text as input and returns"
                             " an body of text to tweet back as output")
        print(Colors.cyan("Beginning polling..."), end="\n\n")
        while True:
            self._poll(response_method)
            sleep(sleep_interval)

    def _poll(self, response_method):
        """
        Check API for any tweets at self. If a tweet directed at the bot is found,
        use the response_method to formulate a response
        :param response_method: a user-provided method for formulating responses
        """
        try:
            for tweet in tweepy.Cursor(self.api.search, q=f"@{self.me} -filter:retweets",
                                       tweet_mode="extended").items():
                if not self._is_replied(tweet):
                    self._mark_replied(tweet.id)  # mark replied before responding in case of error
                    self.respond(response_method, tweet)

        except TweepError as err:
            self.log_error(self._extract_tweepy_error(err))
            raise TweepError(err)

    def tweet(self, tweet, at=None):
        """
        General tweeting method. It will divide up long bits of text into multiple messages,
        and return the first tweet that it makes. Multi-tweets (including to other people)
        will have second and third messages made in response to self.
        :param at: who the user is tweeting at
        :param tweet: the text to tweet
        :return: the first tweet, if successful; else, none
        """
        if tweet.strip() == "":
            return

        num_tweets, tweets = self._divide_tweet(tweet, at)
        if num_tweets > 0:
            # replace @'s with #'s and convert unicode emojis before tweeting
            [self.api.update_status(tw.replace("@", "#").encode("utf-8")) for tw in tweets]
            self.log(f"Tweeted: {' '.join(tweets)}")
            return tweets[0]

    def respond(self, response_method, tweet):
        # formulate response
        print(f"responding to @{tweet.user.screen_name}")
        if tweet.user.screen_name == self.me:
            return
        response = response_method(tweet.full_text)
        num_tweets, to_tweet = self._divide_tweet(response, tweet.user.screen_name)

        if num_tweets < 1:  # too long!
            to_tweet = [
                f"Sorry, @{tweet.user.screen_name}! That's too many"
                f" episodes to check. Try a smaller number! Kyah!"
            ]

        # iterate through and make response tweets
        last_tweet = None
        for i, new_tweet in enumerate(to_tweet):
            last_tweet = self.api.update_status(status=new_tweet,
                                                in_reply_to_status_id=(
                                                    tweet.id if last_tweet is None else last_tweet.id
                                                ))
            if i is 0:
                first_tweet_id = last_tweet.id
        self.log(f"Responded to {tweet.user.screen_name}. Tweet ID @{first_tweet_id}")
        return to_tweet[0]

    @staticmethod
    def _extract_tweepy_error(e):
        return e.response.reason

    def log(self, activity):
        with open(self.log_file, "a") as l:
            l.write(f"{strftime('[%Y-%m-%d] @ %H:%M:%S')} {activity}\n")

    def log_error(self, error_msg):
        self.log(Colors.red(f"ERROR => {error_msg}"))


class Colors:
    _RED = "\033[31m"
    _RESET = "\033[0m"
    _BOLDWHITE = "\033[1m\033[37m"
    _YELLOW = "\033[33m"
    _CYAN = "\033[36m"
    _PURPLE = "\033[35m"
    _CLEAR = "\033[2J"  # clears the terminal screen

    @staticmethod
    def red(s):
        return Colors._RED + s + Colors._RESET

    @staticmethod
    def cyan(s):
        return Colors._CYAN + s + Colors._RESET

    @staticmethod
    def yellow(s):
        return Colors._YELLOW + s + Colors._RESET

    @staticmethod
    def purple(s):
        return Colors._PURPLE + s + Colors._RESET

    @staticmethod
    def white(s):
        return Colors._BOLDWHITE + s + Colors._RESET
