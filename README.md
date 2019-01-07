# Is It Filler?
There's a lot of filler in Naruto. Like. A lot.  
### Have you ever asked yourself, "How many episodes of this will I need to skip to get back to the canon stuff?"  
**Wonder no more.**

Just tweet at this bot with an episode number to see if it's filler or not!  
&nbsp;  
Also, feel free to snag the `TwitterBot` class I wrote—it's pretty simply and I've used the same template 
for other bots that have very simple response patterns (check out [@theDNABot](https://twitter.com/theDNABot)!).

## Requirements
* Python 3
* Tweepy module
* Twitter API credentials

### Twitter API credentials
In order to make a bot, you must have your own credentials from
[Twitter's developer site](https://dev.twitter.com) and place them in a file called
`api_key.py` as a dictionary object called key. Additionally, you'll need the `tweepy` module.
See below for that.

```python
# API_KEY.py
key = {
    "consumer_key": "Nequeporroquisquamestquidolorem",
    "consumer_secret": "abcdefghijklmnopqrstuvwxyz",
    "access_token": "ipsumquiadolorsitamet",
    "access_token_secret": "1234567890"
}
```

### Installing `tweepy`
```bash
$ pip install tweepy
```

### To run, clone the repo and execute the following:
```bash
$ python run_bot.py
```
