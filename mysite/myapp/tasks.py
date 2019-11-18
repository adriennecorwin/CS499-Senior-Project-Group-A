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

#initial twitter search criteria
initialSearchDict = {}
initialSearchDict['hashtags'] = ["scotus", 'supremecourt', 'ussc', 'chiefjustice']
initialSearchDict['andHashtags'] = False
initialSearchDict['accounts'] = ['stevenmazie', 'JeffreyToobin', 'DCCIR']
initialSearchDict['notAccounts'] = ['John_Scotus', 'ScotusCC']
initialSearchDict['fromDate'] = datetime.strftime(timezone.now() - timedelta(1), '%Y-%m-%d')
initialSearchDict['toDate'] = datetime.strftime(timezone.now(), '%Y-%m-%d')
initialSearchDict['keywords'] = []
twitterSearchQueries = []

# builds queries for twitter search api based on input dictionary
# input:search dict
# output: None
def buildTwitterSearchQuery(searchDict):
    global twitterSearchQueries #global so that the pull function always uses the most up to date queries
    twitterSearchQueries = []

    #build query for keywords
    keywordQuery = ""
    for i in range(len(searchDict['keywords'])):
        keywordQuery += searchDict['keywords'][i]
        if i < len(searchDict['keywords']) - 1:
            if searchDict['andKeywords']:
                keywordQuery += " AND "
            else:
                keywordQuery += " OR "

    #build query for hashtags
    hashtagQuery = ""
    for i in range(len(searchDict['hashtags'])):
        hashtagQuery += "#" + searchDict['hashtags'][i]
        if i < len(searchDict['hashtags']) - 1:
            if searchDict['andHashtags']:
                hashtagQuery += " AND "
            else:
                hashtagQuery += " OR "

    #add keyword and hashtag queries to list
    if hashtagQuery != "":
        twitterSearchQueries.append(hashtagQuery)
    if keywordQuery != "":
        twitterSearchQueries.append(keywordQuery)

    #add user blacklist to hashtag and keyword queries
    #done after they are added to list to ensure blacklist only added if query exists
    for i in range(len(twitterSearchQueries)):
        for j in range(len(searchDict['notAccounts'])):
            twitterSearchQueries[i] += " -from:" + searchDict['notAccounts'][j]

    #build query for accounts
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

    #add date range constraint on all queries
    if searchDict['fromDate'] != "":
        fromDateQuery = " since:" + searchDict['fromDate']
        for i in range(len(twitterSearchQueries)):
            twitterSearchQueries[i] += fromDateQuery
    if searchDict['toDate'] != "":
        toDateQuery = " until:" + searchDict['toDate']
        for i in range(len(twitterSearchQueries)):
            twitterSearchQueries[i] += toDateQuery

# retrieves and stores only relevant information from tweepy tweet responses
# input: tweepy response from search api call
# output: list of all tweets from response stored as dictionaries with only relevant information about the tweet
def parseTwitterResponse(response):
    tweets = []
    for t in response:
        #set tweet information that will depend on whether the tweet is a retweet
        isRetweet = False
        commentText = None
        originalText = t.full_text
        h = t.entities.get('hashtags')
        u = t.entities.get('urls')
        numRetweetsNew = None
        numFavoritesNew = None
        numRetweetsOriginal = t.retweet_count
        numFavoritesOriginal = t.favorite_count
        originalUsername = t.user.screen_name
        originalScreenName = t.user.name
        originalLocation = t.user.location
        originalVerified = t.user.verified
        newUsername = None
        newScreenName = None
        newLocation = None
        newVerified = None

        if hasattr(t, 'retweeted_status'):
            isRetweet = True
            originalText = t.retweeted_status.full_text
            h = t.retweeted_status.entities.get('hashtags')
            u = t.retweeted_status.entities.get('urls')
            numRetweetsOriginal = t.retweeted_status.retweet_count
            numFavoritesOriginal = t.retweeted_status.favorite_count
            numRetweetsNew = t.retweet_count
            numFavoritesNew = t.favorite_count

            originalUsername = t.retweeted_status.user.screen_name
            originalScreenName = t.retweeted_status.user.name
            originalLocation = t.retweeted_status.user.location
            originalVerified = t.retweeted_status.user.verified
            newUsername = t.user.screen_name
            newScreenName = t.user.name
            newLocation = t.user.location
            newVerified = t.user.verified

        elif hasattr(t, 'quoted_status'):
            isRetweet = True
            originalText = t.quoted_status.full_text
            commentText = t.full_text
            h = t.quoted_status.entities.get('hashtags')
            u = t.quoted_status.entities.get('urls')
            numRetweetsOriginal = t.quoted_status.retweet_count
            numFavoritesOriginal = t.quoted_status.favorite_count
            numRetweetsNew = t.retweet_count
            numFavoritesNew = t.favorite_count

            originalUsername = t.quoted_status.user.screen_name
            originalScreenName = t.quoted_status.user.name
            originalLocation = t.quoted_status.user.location
            originalVerified = t.quoted_status.user.verified
            newUsername = t.user.screen_name
            newScreenName = t.user.name
            newLocation = t.user.location
            newVerified = t.user.verified

        #get hashtags in tweet
        hashtags = []
        for hDict in h:
            hashtags.append(hDict['text'])

        #get urls in tweet
        urls = []
        for uDict in u:
            urls.append(uDict['url'])

        #create tweet dictionary storing only relevant information
        tweet = {}
        tweet['originalUsername'] = originalUsername
        tweet['originalScreenName'] = originalScreenName
        tweet['originalLocation'] = originalLocation
        tweet['originalIsVerified'] = originalVerified

        tweet['newUsername'] = newUsername
        tweet['newScreenName'] = newScreenName
        tweet['newLocation'] = newLocation
        tweet['newIsVerified'] = newVerified

        # tweet['createdAt'] = datetime.strptime(t.created_at, '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=pytz.UTC)
        tweet['createdAt'] = t.created_at.replace(tzinfo=pytz.UTC)
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

# uses tweepy to make twitter api search request
# input: None
# output: list of distinct tweet dictionaries from api response
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

# inserts tweet into db
# input: tweet dictionary
# output: None
def insert(tweet):
    print("insert")
    newUser = None
    #if user is not already in db, add them to db
    if not User.objects.filter(username=tweet['originalUsername']).exists():
        originalUser = User(username=tweet['originalUsername'], screenName=tweet['originalScreenName'], location=tweet['originalLocation'],
                    isVerified=tweet['originalIsVerified'])
        originalUser.save()
    else:
        originalUser = User.objects.filter(username=tweet['originalUsername'])[0]

    if tweet['newUsername'] != None:
        if not User.objects.filter(username=tweet['newUsername']).exists():
            newUser = User(username=tweet['newUsername'], screenName=tweet['newScreenName'], location=tweet['newLocation'],
                    isVerified=tweet['newIsVerified'])
            newUser.save()

        else:
            if User.objects.filter(username=tweet['newUsername']).exists():
                newUser = User.objects.filter(username=tweet['newUsername'])[0]

    #if hashtag not already in db, add it to db
    # TODO: make case insensitive
    hashtags = []
    for h in tweet['hashtags']:
        if not Hashtag.objects.filter(hashtagText=h).exists():
            hashtag = Hashtag(hashtagText=h)
            hashtag.save()
        else:
            hashtag = Hashtag.objects.filter(hashtagText=h)[0]
        hashtags.append(hashtag)

    #if url not already in db, add it to db
    urls = []
    for u in tweet['urls']:
        if not Url.objects.filter(urlText=u).exists():
            url = Url(urlText=u)
            url.save()
        else:
            url = Url.objects.filter(urlText=u)[0]
        urls.append(url)

    #create tweet object and add to db
    t = Tweet(originalUser=originalUser, newUser=newUser, createdAt=tweet['createdAt'], isRetweet=tweet['isRetweet'], originalText=tweet['originalText'],
              commentText=tweet['commentText'], numRetweetsOriginal=tweet['numRetweetsOriginal'],
              numRetweetsNew=tweet['numRetweetsNew'], numFavoritesOriginal=tweet['numFavoritesOriginal'],
              numFavoritesNew=tweet['numFavoritesNew'], lastUpdated=timezone.now().strftime("%Y-%m-%d %H:%M"))

    t.save()

    #add tweet and all of its hashtags to log in db
    for hashtag in hashtags:
        hlog = HashtagLog(tweet=t, hashtag=hashtag)
        hlog.save()

    # add tweet and all of its urls to log in db
    for url in urls:
        ulog = UrlLog(tweet=t, url=url)
        ulog.save()

# updates tweet in db with new information (only updates retweet and favorites metrics
# input: existing tweet, tweet object with potentially new information
# output: None
def update(oldTweet, newTweet):
    print("update")

    #if number of retweets or favorites is different between existing and new, update

    if oldTweet.numRetweetsOriginal != newTweet['numRetweetsOriginal']:
        oldTweet.numRetweetsOriginal = newTweet['numRetweetsOriginal']

    if oldTweet.numRetweetsNew != newTweet['numRetweetsNew']:
        oldTweet.numRetweetsNew = newTweet['numRetweetsNew']

    if oldTweet.numFavoritesOriginal != newTweet['numFavoritesOriginal']:
        oldTweet.numFavoritesOriginal = newTweet['numFavoritesOriginal']

    if oldTweet.numFavoritesNew != newTweet['numFavoritesNew']:
        oldTweet.numFavoritesNew = newTweet['numFavoritesNew']

    oldTweet.lastUpdated = timezone.now().strftime("%Y-%m-%d %H:%M")
    oldTweet.save()

# inserts new tweets and updates existing tweets in db
# input: list of distinct tweet dictionaries
# output: None
def addToDatabase(tweets):
    for tweet in tweets:
        if tweet['newUsername']:
            if Tweet.objects.filter(newUser__username=tweet['newUsername'], createdAt=tweet['createdAt']).exists():
                t = Tweet.objects.get(newUser__username=tweet['newUsername'], createdAt=tweet['createdAt'])
                update(t, tweet)
        elif Tweet.objects.filter(originalUser__username=tweet['originalUsername'], createdAt=tweet['createdAt']).exists():
            t = Tweet.objects.get(originalUser__username=tweet['originalUsername'], createdAt=tweet['createdAt'])
            update(t, tweet)
        else:
            insert(tweet)

# pulls relevant tweets from twitter by searching twitter and adding results to db (runs as bg task)
# input: None
# output: None
def pull():
    searchResults = searchTwitter()
    addToDatabase(searchResults)
    print("pulled")

#https://stackoverflow.com/questions/2223157/how-to-execute-a-function-asynchronously-every-60-seconds-in-python/2223182
# runs pull function as bg task every 120 seconds (2 minutes)
def runPull(pullEvent):
    print("pulling")
    pull()
    if not pullEvent.is_set():
        threading.Timer(120, runPull, [pullEvent]).start()

buildTwitterSearchQuery(initialSearchDict)
pullEvent = threading.Event()
runPull(pullEvent)