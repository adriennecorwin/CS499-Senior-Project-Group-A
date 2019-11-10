from .models import User
from .models import Tweet
from .models import Hashtag
from .models import Url
from .models import HashtagLog
from .models import UrlLog

from datetime import datetime, timedelta
from django.utils import timezone
import pytz
import threading

import tweepy

consumer_key = "#####"
consumer_secret = "#####"

access_token = "#####"
access_token_secret = "#####"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

initialSearchDict = {}
initialSearchDict['hashtags'] = ["scotus", 'supremecourt', 'ussc', 'chiefjustice']
initialSearchDict['andHashtags'] = False
initialSearchDict['accounts'] = ['stevenmazie', 'JeffreyToobin', 'DCCIR']
initialSearchDict['notAccounts'] = ['John_Scotus', 'ScotusCC']
initialSearchDict['fromDate'] = datetime.strftime(timezone.now() - timedelta(1), '%Y-%m-%d')
initialSearchDict['toDate'] = datetime.strftime(timezone.now(), '%Y-%m-%d')
initialSearchDict['keywords'] = []
twitterSearchQueries = []

# build queries based on dictionary from view class and appends them to self.twitterSearchQueries
def buildTwitterSearchQuery(searchDict):
    global twitterSearchQueries
    twitterSearchQueries = []
    keywordQuery = ""
    for i in range(len(searchDict['keywords'])):
        keywordQuery += searchDict['keywords'][i]
        if i < len(searchDict['keywords']) - 1:
            if searchDict['andKeywords']:
                keywordQuery += " AND "
            else:
                keywordQuery += " OR "

    hashtagQuery = ""
    for i in range(len(searchDict['hashtags'])):
        hashtagQuery += "#" + searchDict['hashtags'][i]
        if i < len(searchDict['hashtags']) - 1:
            if searchDict['andHashtags']:
                hashtagQuery += " AND "
            else:
                hashtagQuery += " OR "

    if hashtagQuery != "":
        twitterSearchQueries.append(hashtagQuery)
    if keywordQuery != "":
        twitterSearchQueries.append(keywordQuery)

    for i in range(len(twitterSearchQueries)):
        for j in range(len(searchDict['notAccounts'])):
            twitterSearchQueries[i] += " -from:" + searchDict['notAccounts'][j]

    accountsQuery = ""
    for i in range(len(searchDict['accounts'])):
        accountsQuery += "from:" + searchDict['accounts'][i] + " OR "
    for i in range(len(searchDict['accounts'])):
        accountsQuery += "to:" + searchDict['accounts'][i] + " OR "
    for i in range(len(searchDict['accounts'])):
        accountsQuery += "@" + searchDict['accounts'][i]
        if i < len(searchDict['accounts']) - 1:
            accountsQuery += " OR "

    if accountsQuery != "":
        twitterSearchQueries.append(accountsQuery)

    if searchDict['fromDate'] != "":
        fromDateQuery = " since:" + searchDict['fromDate']
        for i in range(len(twitterSearchQueries)):
            twitterSearchQueries[i] += fromDateQuery
    if searchDict['toDate'] != "":
        toDateQuery = " until:" + searchDict['toDate']
        for i in range(len(twitterSearchQueries)):
            twitterSearchQueries[i] += toDateQuery

    print(twitterSearchQueries)

def parseTwitterResponse(response):
    tweets = []
    for t in response:
        isRetweet = False
        commentText = None
        originalText = t.full_text
        numRetweetsNew = None
        numFavoritesNew = None
        numRetweetsOriginal = t.retweet_count
        numFavoritesOriginal = t.favorite_count
        if hasattr(t, 'retweeted_status'):
            isRetweet = True
            originalText = t.retweeted_status.full_text
            numRetweetsOriginal = t.retweeted_status.retweet_count
            numFavoritesOriginal = t.retweeted_status.favorite_count
            numRetweetsNew = t.retweet_count
            numFavoritesNew = t.favorite_count

        elif hasattr(t, 'quoted_status'):
            isRetweet = True
            originalText = t.quoted_status.full_text
            commentText = t.full_text
            numRetweetsOriginal = t.quoted_status.retweet_count
            numFavoritesOriginal = t.quoted_status.favorite_count
            numRetweetsNew = t.retweet_count
            numFavoritesNew = t.favorite_count

        h = t.entities.get('hashtags')
        hashtags = []
        for hDict in h:
            hashtags.append(hDict['text'])
        u = t.entities.get('urls')
        urls = []
        for uDict in u:
            urls.append(uDict['url'])

        tweet = {}
        tweet['username'] = t.user.screen_name
        tweet['screenName'] = t.user.name
        tweet['userLocation'] = t.user.location
        tweet['isVerified'] = t.user.verified
        tweet['userUrl'] = t.user.url
        # tweet['createdAt'] = datetime.strptime(t.created_at, '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=pytz.UTC)
        tweet['createdAt'] = t.created_at.replace(tzinfo=pytz.UTC)
        print(tweet['createdAt'])
        tweet['isRetweet'] = isRetweet

        tweet['originalText'] = originalText
        tweet['commentText'] = commentText
        if commentText != None:
            tweet['commentText'] = tweet['commentText']
        tweet['hashtags'] = hashtags
        tweet['urls'] = urls
        tweet['numRetweetsOriginal'] = numRetweetsOriginal

        tweet['numRetweetsNew'] = numRetweetsNew
        tweet['numFavoritesOriginal'] = numFavoritesOriginal
        tweet['numFavoritesNew'] = numFavoritesNew

        tweets.append(tweet)

    return tweets

def searchTwitter():
    global twitterSearchQueries, api
    allSearchResults = []
    print("search:", twitterSearchQueries)
    for query in twitterSearchQueries:
        response = api.search(q=query, count=25, tweet_mode='extended')
        tweets = parseTwitterResponse(response)
        for tweetDict in [i for n, i in enumerate(tweets) if i not in tweets[n + 1:]]:
            allSearchResults.append(tweetDict)
    return allSearchResults


def insert(tweet):
    print("insert")
    if not User.objects.filter(username=tweet['username']).exists():
        user = User(username=tweet['username'], screenName=tweet['screenName'], location=tweet['userLocation'],
                    isVerified=tweet['isVerified'])
        user.save()
    else:
        user = User.objects.filter(username=tweet['username'])[0]
    hashtags = []
    for h in tweet['hashtags']:
        if not Hashtag.objects.filter(hashtagText=h).exists():
            hashtag = Hashtag(hashtagText=h)
            hashtag.save()
        else:
            hashtag = Hashtag.objects.filter(hashtagText=h)[0]
        hashtags.append(hashtag)

    urls = []
    for u in tweet['urls']:
        if not Url.objects.filter(urlText=u).exists():
            url = Url(urlText=u)
            url.save()
            urls.append(url)
        else:
            url = Url.objects.filter(urlText=u)[0]
        urls.append(url)

    t = Tweet(user=user, createdAt=tweet['createdAt'], isRetweet=tweet['isRetweet'], originalText=tweet['originalText'],
              commentText=tweet['commentText'], numRetweetsOriginal=tweet['numRetweetsOriginal'],
              numRetweetsNew=tweet['numRetweetsNew'], numFavoritesOriginal=tweet['numFavoritesOriginal'],
              numFavoritesNew=tweet['numFavoritesNew'], lastUpdated=timezone.now().strftime("%Y-%m-%d %H:%M"))

    t.save()

    for hashtag in hashtags:
        hlog = HashtagLog(tweet=t, hashtag=hashtag)
        hlog.save()

    for url in urls:
        ulog = UrlLog(tweet=t, url=url)
        ulog.save()


def update(oldTweet, newTweet):
    if oldTweet.numRetweetsOriginal != newTweet['numRetweetsOriginal']:
        oldTweet.numRetweetsOriginal = newTweet['numRetweetsOriginal']

    if oldTweet.numRetweetsNew != newTweet['numRetweetsNew']:
        oldTweet.numRetweetsNew = newTweet['numRetweetsNew']

    if oldTweet.numFavoritesOriginal != newTweet['numFavoritesOriginal']:
        oldTweet.numFavoritesOriginal = newTweet['numFavoritesOriginal']

    if oldTweet.numFavoritesNew != newTweet['numFavoritesNew']:
        oldTweet.numFavoritesNew = newTweet['numFavoritesNew']

    oldTweet.lastUpdated = timezone.now().strftime("%Y-%m-%d %H:%M")
    print("update")
    print(oldTweet)
    oldTweet.save()
    print("saved")

# separates tweets into list of existing (already in db) and new
# return existing, new
def addToDatabase(tweets):
    for tweet in tweets:
        if Tweet.objects.filter(user__username=tweet['username'], createdAt=tweet['createdAt']).exists():
            t = Tweet.objects.get(user__username=tweet['username'], createdAt=tweet['createdAt'])
            update(t, tweet)
        else:
            insert(tweet)

def pull():
    searchResults = searchTwitter()
    print(searchResults)
    addToDatabase(searchResults)
    print("pulled")

#https://stackoverflow.com/questions/2223157/how-to-execute-a-function-asynchronously-every-60-seconds-in-python/2223182
def runPull(pullEvent):
    print("pulling")
    pull()
    if not pullEvent.is_set():
        threading.Timer(120, runPull, [pullEvent]).start()

# buildTwitterSearchQuery(initialSearchDict)
# pullEvent = threading.Event()
# runPull(pullEvent)