# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render, render_to_response
from django.shortcuts import redirect

from django.core.paginator import Paginator

from .models import User
from .models import Tweet
from .models import Hashtag
from .models import Url
from .models import HashtagLog
from .models import UrlLog

from datetime import datetime, timedelta

import tweepy

# Create your views here.

consumer_key = "065p3Ddh3T1rxoAbhsNQKTT0r"
consumer_secret = "qHTYc1aLUfVFCezVLz1U0yPphthRM0DevNL2AKSxG4LTrzWiWA"

access_token = "1176877630382985217-qFO9wveUf0LycpO8cP23ISSVMr1U3g"
access_token_secret = "1zr5Guity4uffdYKQ9XCfP6M1r1e8VmeLd6y3Cm9wzoBk"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)
twitterSearchQueries = []

def buildTwitterSearchQuery():
    global twitterSearchQueries
    twitterSearchQueries = []
    # build queries based on dictionary from view class and appends them to self.twitterSearchQueries
    searchDict = {}
    searchDict['hashtags'] = ["scotus", 'supremecourt', 'ussc', 'chiefjustice']
    searchDict['andHashtags'] = False
    searchDict['accounts'] = ['stevenmazie', 'JeffreyToobin', 'DCCIR']
    searchDict['notAccounts'] = ['John_Scotus', 'ScotusCC']
    searchDict['fromDate'] = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
    searchDict['toDate'] = datetime.strftime(datetime.now(), '%Y-%m-%d')

    hashtagQuery = ""
    for i in range(len(searchDict['hashtags'])):
        hashtagQuery += "#" + searchDict['hashtags'][i]
        if i < len(searchDict['hashtags']) - 1:
            if searchDict['andHashtags']:
                hashtagQuery += " AND "
            else:
                hashtagQuery += " OR "

    for i in range(len(searchDict['notAccounts'])):
        hashtagQuery += " -from:" + searchDict['notAccounts'][i]

    twitterSearchQueries.append(hashtagQuery)

    accountsQuery = ""
    for i in range(len(searchDict['accounts'])):
        accountsQuery += "from:" + searchDict['accounts'][i] + " OR "
    for i in range(len(searchDict['accounts'])):
        accountsQuery += "to:" + searchDict['accounts'][i] + " OR "
    for i in range(len(searchDict['accounts'])):
        accountsQuery += "@" + searchDict['accounts'][i]
        if i < len(searchDict['accounts']) - 1:
            accountsQuery += " OR "
    twitterSearchQueries.append(accountsQuery)

    if searchDict['fromDate'] != "":
        fromDateQuery = " since:" + searchDict['fromDate']
        for i in range(len(twitterSearchQueries)):
            twitterSearchQueries[i] += fromDateQuery
    if searchDict['toDate'] != "":
        toDateQuery = " until:" + searchDict['toDate']
        for i in range(len(twitterSearchQueries)):
            twitterSearchQueries[i] += toDateQuery

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
        tweet['username'] = t.user.screen_name.replace("\'", "\\\'")
        tweet['screenName'] = t.user.name.replace("\'", "\\\'")
        tweet['userLocation'] = t.user.location.replace("\'", "\\\'")
        tweet['isVerified'] = t.user.verified
        tweet['createdAt'] = t.created_at
        tweet['isRetweet'] = isRetweet
        tweet['originalText'] = originalText.replace("\'", "\\\'")
        tweet['commentText'] = commentText
        if commentText != None:
            tweet['commentText'] = tweet['commentText'].replace("\'", "\\\'")
        tweet['hashtags'] = hashtags
        tweet['urls'] = urls
        tweet['numRetweetsOriginal'] = numRetweetsOriginal
        tweet['numRetweetsNew'] = numRetweetsNew
        tweet['numFavoritesOriginal'] = numFavoritesOriginal
        tweet['numFavoritesNew'] = numFavoritesNew

        tweets.append(tweet)

    return tweets

def separateNewFromExisting(tweets):
    new = []
    existing = []
    for tweet in tweets:
        if Tweet.objects.filter(user__username=tweet['username'], createdAt=tweet['createdAt']).exists():
            existing.append(tweet)
        else:
            new.append(tweet)

    return existing, new

# separates tweets into list of existing (already in db) and new
# return existing, new

def insert(tweets):

    for tweet in tweets:

        if not User.objects.filter(username=tweet['username']).exists():
            user = User(username=tweet['username'], screenName=tweet['screenName'], location=tweet['userLocation'], isVerified=tweet['isVerified'])
            user.save()
        # else:
        #     user = User.objects.filter(username=tweet['username'])
        hashtags = []
        for h in tweet['hashtags']:
            if not Hashtag.objects.filter(hashtagText=h).exists():
                hashtag = Hashtag(hashtagText=h)
                hashtag.save()
            # else:
            #     hashtag = Hashtag.objects.filter(hashtagText=h)
            # hashtags.append(hashtag)

        urls = []
        for u in tweet['urls']:
            if not Url.objects.filter(urlText=u).exists():
                url = Url(urlText=u)
                url.save()
                urls.append(url)
            # else:
            #     url = Url.objects.filter(urlText=u)
            # urls.append(url)

        t = Tweet(user=user, createdAt=tweet['createdAt'], isRetweet=tweet['isRetweet'], originalText=tweet['originalText'], commentText=tweet['commentText'], numRetweetsOriginal=tweet['numRetweetsOriginal'], numRetweetsNew=tweet['numRetweetsNew'], numFavoritesOriginal=tweet['numFavoritesOriginal'], numFavoritesNew=tweet['numFavoritesNew'])
        t.save()

        for hashtag in hashtags:
            hlog = HashtagLog(tweet=t, hashtag=hashtag)
            hlog.save()

        for url in urls:
            ulog = UrlLog(tweet=t, url=url)
            ulog.save()

# def update(self, tweets):
#     # TODO: fix for new db structure and using tweet obj instead of dict?
#     for tweet in tweets:
#         updateQuery = "UPDATE tweet SET num_retweets=" + tweet['numRetweets'] + ", num_favorites=" + tweet[
#             'num_favorites'] + " WHERE username=\'" + tweet['username'] + "\' and created_at=" + tweet['createdAt']
#         self.cursor.execute(updateQuery)
#         self.database.commit()


def searchTwitter():
    global twitterSearchQueries, api
    allSearchResults = []
    for query in twitterSearchQueries:
        response = api.search(q=query, count=25, tweet_mode='extended')
        tweets = parseTwitterResponse(response)
        for tweetDict in [i for n, i in enumerate(tweets) if i not in tweets[n + 1:]]:
            allSearchResults.append(tweetDict)
    return allSearchResults

def pull():
    searchResults = searchTwitter()
    existing, new = separateNewFromExisting(searchResults)
    # self.update(existing)
    insert(new)

def index(request):
    global twitterSearchQueries
    tweetsList = Tweet.objects.all()
    paginator = Paginator(tweetsList, 24)
    page = request.GET.get('page')
    tweets = paginator.get_page(page)
    if request.GET.get("pull"):
        if request.GET.get("pull") == "true":
            buildTwitterSearchQuery() #in future this should be called whenever api pull parameters changed in ui
            pull()
            return redirect('/')
    return render(request, 'index.html', {'tweets':tweets})



