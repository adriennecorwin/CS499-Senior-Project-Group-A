from .models import User
from .models import Tweet
from .models import Hashtag
from .models import Url
from .models import HashtagLog
from .models import UrlLog

from datetime import datetime, timedelta
from django.utils import timezone
import pytz
from threading import Thread

import tweepy

consumer_key = "065p3Ddh3T1rxoAbhsNQKTT0r"
consumer_secret = "qHTYc1aLUfVFCezVLz1U0yPphthRM0DevNL2AKSxG4LTrzWiWA"

access_token = "1176877630382985217-qFO9wveUf0LycpO8cP23ISSVMr1U3g"
access_token_secret = "1zr5Guity4uffdYKQ9XCfP6M1r1e8VmeLd6y3Cm9wzoBk"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

#initial twitter search criteria
initialSearchDict = {}
initialSearchDict['hashtags'] = ["scotus", 'supremecourt', 'ussc', 'chiefjustice', 'billofrights', 'constitution', 'ussupremecourt', 'highcourt', 'abortion']
initialSearchDict['andHashtags'] = False
initialSearchDict['accounts'] = ['stevenmazie', 'JeffreyToobin', 'DCCIR', 'GregStohr', 'AlisonFrankel']
initialSearchDict['notAccounts'] = ['John_Scotus', 'ScotusCC']
initialSearchDict['fromDate'] = datetime.strftime(timezone.now() - timedelta(1), '%Y-%m-%d')
initialSearchDict['toDate'] = datetime.strftime(timezone.now(), '%Y-%m-%d')
initialSearchDict['keywords'] = []

twitterSearchQueries = []
pullParameters = {} #dictionary with parameters to search twitter by in string form (to display in website)
done = True #true if gone through all results from search request, else false

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
    global pullParameters

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
    pullParameters = {
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

        #if tweet is a retweet
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

        #if tweet is quote tweet
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
    global twitterSearchQueries, api, bigQuery, done
    done = False
    # print("search:", twitterSearchQueries)
    for query in twitterSearchQueries:
        #iterate through every page (pause if hit rate limit)
        for page in tweepy.Cursor(api.search, q=query, count=100, tweet_mode='extended', wait_on_rate_limit=True, wait_on_rate_limit_notify=True).pages():
            searchResults = []
            #parse relevant information from response
            tweets = parseTwitterResponse(page)
            for tweetDict in [i for n, i in enumerate(tweets) if i not in tweets[n + 1:]]: #only add unique tweet to results
                searchResults.append(tweetDict)
            addToDatabase(searchResults) #add results to db for every page so that db gets updated with new tweets to display often
    done = True

# pulls relevant tweets from twitter by searching twitter and adding results to db (runs as bg task)
# input: None
# output: None
def pull():
    import time
    global done

    #continuously try to pull new tweets
    while True:
        #if done getting all results from a search request
        if done:
            print("pulling")
            #execute search request again
            searchTwitter()
            print("pulled")
        #if not done getting all search results, wait 1 minute and then try again
        else:
            time.sleep(60)

#start pulling tweets initially with initial search dictionary parameters
getPullParametersAsStrings(initialSearchDict)
buildTwitterSearchQuery(initialSearchDict)
#
# pullThread = Thread(target=pull) #pull tweets asynchronously so that main thread isn't blocked
# pullThread.start()