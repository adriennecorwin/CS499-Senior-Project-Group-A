from .models import User
from .models import Tweet
from .models import Hashtag
from .models import Url
from .models import HashtagLog
from .models import UrlLog
from django.shortcuts import redirect


from datetime import datetime, timedelta
from django.utils import timezone
import pytz
from threading import Thread

import tweepy
import os
import time
import random

consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']
access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

#initial twitter search criteria
initialSearchDict = {}
initialSearchDict['hashtags'] = ["scotus", 'supremecourt', 'ussc', 'chiefjustice', 'billofrights', 'constitution', 'ussupremecourt', 'highcourt', 'abortion']
initialSearchDict['accounts'] = ['stevenmazie', 'JeffreyToobin', 'DCCIR', 'GregStohr', 'AlisonFrankel']
initialSearchDict['notAccounts'] = ['John_Scotus', 'ScotusCC']
initialSearchDict['fromDate'] = datetime.strftime(timezone.now() - timedelta(1), '%Y-%m-%d')
initialSearchDict['toDate'] = datetime.strftime(timezone.now(), '%Y-%m-%d')
initialSearchDict['keywords'] = []

twitterSearchQueries = []
pullParameters = {} #dictionary with parameters to search twitter by in string form (to display in website)
done = True #true if gone through all results from search request, else false
pulling = {'pulling': True} #if user has started pulling tweets, dict (mutable) so it can be accessed from view.py
MAX_PARAMETERS = 50 #max before Twitter API errors bc of too complex query
# convert the array value of a given dictionary key to a string with elements separated by spaces

# input:dictionary and key in dictionary that should be converted
# output: the string
def searchListToString(d, key):
    string = ""
    for i in range(len(d[key])):
        if i == len(d[key]) - 1:
            string += d[key][i]
        else:
            string += d[key][i] + " "
    return string

# set the pull parameters dictionary (to display on website)
# input: a search dictionary of paramters to search twitter by
# output: none
def getPullParametersAsStrings(searchDict):
    #get number of days between today and given from date
    if searchDict["fromDate"] != "":
        delta = timezone.now()-datetime.strptime(searchDict["fromDate"], '%Y-%m-%d').replace(tzinfo=pytz.UTC)
        fromDateVal = delta.days
        if fromDateVal > 0:
            fromDateString = str(fromDateVal) + " days ago"
        elif fromDateVal == 0:
            fromDateString = "Today"
    else:
        fromDateVal = 0
        fromDateString = ""


    #get number of days between today and given to date
    if searchDict["toDate"] != "":
        delta = timezone.now()-datetime.strptime(searchDict["toDate"], '%Y-%m-%d').replace(tzinfo=pytz.UTC)
        toDateVal = delta.days
        if toDateVal > 0:
            toDateString = str(toDateVal) + " days ago"
        elif toDateVal == 0:
            toDateString = "Today"
        else:
            toDateString = "Tomorrow"
    else:
        toDateVal = 0
        toDateString = ""

    #set dictionary to string conversions of dict array values (and # days between today and from/to dates)
    return {
        "usersString": searchListToString(searchDict, "accounts"),
        "notUsersString": searchListToString(searchDict, "notAccounts"),
        "hashtagsString": searchListToString(searchDict, "hashtags"),
        "keywordsString": searchListToString(searchDict, "keywords"),
        "fromDateVal": fromDateVal,
        "toDateVal": toDateVal,
        "fromDateString": fromDateString,
        "toDateString": toDateString
    }

# builds queries for twitter search api based on input dictionary
# input:search dict
# output: None
def buildTwitterSearchQuery(searchDict):
    global twitterSearchQueries #global so that the pull function always uses the most up to date queries
    global done
    global pullParameters

    twitterSearchQueries = [] #clear previous queries
    keywordParameters = []
    hashtagParameters = []
    accountParameters = []

    for keyword in searchDict['keywords']:
        keywordParameters.append(keyword)
    for hashtag in searchDict['hashtags']:
        hashtagParameters.append("#" + hashtag)
    for account in searchDict['accounts']:
        accountParameters.append("to:"+account)
        accountParameters.append("from:"+account)
        accountParameters.append("@"+account)

    numDates = 0 # number of dates to append to end of each query

    if searchDict['fromDate'] != "":
        numDates += 1
    if searchDict['toDate'] != "":
        numDates += 1

    #build queries with randomly selected keywords, hashtags, and accounts until there are no more parameters or the query has gotten too complex (then start new one)
    while len(keywordParameters) + len(hashtagParameters) + len(accountParameters) != 0:
        query = ""
        while len(query.split(" ")) < MAX_PARAMETERS - len(searchDict['notAccounts']) - numDates - 1 and len(keywordParameters) + len(hashtagParameters) + len(accountParameters) != 0:
            if keywordParameters:
                parameter = random.choice(keywordParameters)
                query += parameter + " OR "
                keywordParameters.remove(parameter)
            if hashtagParameters:
                parameter = random.choice(hashtagParameters)
                query += parameter + " OR "
                hashtagParameters.remove(parameter)
            if accountParameters:
                parameter = random.choice(accountParameters)
                query += parameter + " OR "
                accountParameters.remove(parameter)

        #eliminate last OR
        if numDates + len(searchDict['notAccounts']) != 0:
            query = query[:len(query)-3]
        else:
            query = query[:len(query)-4]

        #add accounts to be excluded from search parameter to query
        for i in range(len(searchDict['notAccounts'])):
            query += "-from:" + searchDict['notAccounts'][i]
            if i != len(searchDict['notAccounts']) -1:
                query += " "

        #add to and from dates parameters to query
        if searchDict['fromDate'] != "":
            query += " since:" + searchDict['fromDate']
        if searchDict['toDate'] != "":
            query += " until:" + searchDict['toDate']
        twitterSearchQueries.append(query)

    pullParameters = getPullParametersAsStrings(searchDict)
    done = True #so new queries will immediately be searched for

    #if any queries are too long, return False
    for query in twitterSearchQueries:
        if len(query.split(" ")) >= MAX_PARAMETERS:
            return False
    return True

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

        #if tweet is a retweet
        if hasattr(t, 'retweeted_status'):
            isRetweet = True
            originalText = t.retweeted_status.full_text
            h = t.retweeted_status.entities.get('hashtags')
            u = t.retweeted_status.entities.get('urls')
            numRetweetsOriginal = t.retweeted_status.retweet_count
            numFavoritesOriginal = t.retweeted_status.favorite_count
            # numRetweetsNew = t.retweet_count
            # numFavoritesNew = t.favorite_count

            originalUsername = t.retweeted_status.user.screen_name
            originalScreenName = t.retweeted_status.user.name
            originalLocation = t.retweeted_status.user.location
            originalVerified = t.retweeted_status.user.verified
            newUsername = t.user.screen_name
            newScreenName = t.user.name
            newLocation = t.user.location
            newVerified = t.user.verified

        #if tweet is quote tweet
        elif hasattr(t, 'quoted_status'):
            isRetweet = True
            originalText = t.quoted_status.full_text
            commentText = t.full_text
            h = t.quoted_status.entities.get('hashtags')
            u = t.quoted_status.entities.get('urls')
            numRetweetsOriginal = t.quoted_status.retweet_count
            numFavoritesOriginal = t.quoted_status.favorite_count
            # numRetweetsNew = t.retweet_count
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

# inserts tweet into db
# input: tweet dictionary
# output: None
def insert(tweet):
    global pullParameters
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
    # TODO: make case insensitive??
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
              numFavoritesNew=tweet['numFavoritesNew'], lastUpdated=timezone.now().strftime("%Y-%m-%d %H:%M"), twitterQueryUsers=pullParameters['usersString'],
              twitterQueryNotUsers=pullParameters['notUsersString'], twitterQueryHashtags=pullParameters['hashtagsString'], twitterQueryKeywords=pullParameters['keywordsString'],
              twitterQueryFromDate=pullParameters['fromDateString'], twitterQueryToDate=pullParameters['toDateString'])

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

        #if tweet is retweet exists in db or original tweet exists in db, update it in the db
        if tweet['newUsername']:
            if Tweet.objects.filter(newUser__username=tweet['newUsername'], createdAt=tweet['createdAt']).exists():
                t = Tweet.objects.get(newUser__username=tweet['newUsername'], createdAt=tweet['createdAt'])
                update(t, tweet)
        elif Tweet.objects.filter(originalUser__username=tweet['originalUsername'], createdAt=tweet['createdAt']).exists():
            t = Tweet.objects.get(originalUser__username=tweet['originalUsername'], createdAt=tweet['createdAt'])
            update(t, tweet)

        #otherwise (neither exist in db) add to db
        else:
            insert(tweet)

# for each search query, uses tweepy to make twitter api search request,
# goes through all pages of result, and adds results to db appropriately
# input: None
# output: None
def searchTwitter():
    global twitterSearchQueries, api, done, pulling
    done = False
    # print("search:", twitterSearchQueries)
    for query in twitterSearchQueries:
        retries = 0
        #iterate through every page (pause if hit rate limit)
        try:
            for page in tweepy.Cursor(api.search, q=query, count=100, tweet_mode='extended', wait_on_rate_limit=True, wait_on_rate_limit_notify=True).pages():
                if done or not pulling['pulling']: #if new twitter search query built, stop this search run
                    break
                searchResults = []
                #parse relevant information from response
                tweets = parseTwitterResponse(page)
                for tweetDict in [i for n, i in enumerate(tweets) if i not in tweets[n + 1:]]: #only add unique tweet to results
                    searchResults.append(tweetDict)
                addToDatabase(searchResults) #add results to db for every page so that db gets updated with new tweets to display often
            if done:
                break
        except tweepy.TweepError as e:
            print(e)
            if retries > 2:
                pulling['pulling'] = False
                redirect("error")
            retries += 1

    done = True

# pulls relevant tweets from twitter by searching twitter and adding results to db (runs as bg task)
# input: None
# output: None
def pull():
    global done, pulling
    while True:
        #continuously try to pull new tweets
        while pulling['pulling']:
            #if done getting all results from a search request
            if done:
                print("pulling")
                #execute search request again
                searchTwitter()
                print("pulled")
            #if not done getting all search results, wait 1 minute and then try again
            else:
                time.sleep(60)

def startStopPull(request):
    global pulling
    pulling['pulling'] = not pulling['pulling']
    return redirect('/')

#start pulling tweets initially with initial search dictionary parameters
pullParameters = getPullParametersAsStrings(initialSearchDict)
buildTwitterSearchQuery(initialSearchDict)

# pullThread = Thread(target=pull) #pull tweets asynchronously so that main thread isn't blocked
# pullThread.start()