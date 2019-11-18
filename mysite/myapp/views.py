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

from .tasks import buildTwitterSearchQuery
from django.db.models import Q
from datetime import datetime
import pytz
import csv
import textstat
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from django.utils import timezone
import os

currentTwitterSearchDict = {}
tweetsList = []
# home page controller
def index(request):
    global currentTwitterSearchDict, tweetsList
    #get tweets to display

    tweetsList = Tweet.objects.all().order_by('-createdAt') #get list of all tweets in db most recent to least
    paginator = Paginator(tweetsList, 24) #only display 24 tweets per page
    page = request.GET.get('page')
    tweets = paginator.get_page(page)

    #refresh
    if request.GET.get("refresh"): #refresh page aka display all tweets from db again
        if request.GET.get("refresh") == "true":
            return redirect('/')

    #download
    if request.GET.get("csv-name"):
        download(request.GET.get("csv-name"))

    #search
    userQueries = []
    keywordQueryies = []
    hashtagResults = []

    fromDate = None
    toDate = None
    search = False

    if request.GET.get("from"):
        search = True
        fromDate = datetime.strptime(request.GET.get("from"), '%b %d, %Y').replace(tzinfo=pytz.UTC)
    if request.GET.get("to"):
        search = True
        toDate = datetime.strptime(request.GET.get("to"), '%b %d, %Y').replace(tzinfo=pytz.UTC)
    if request.GET.get("users"):
        search = True
        userQueries = [Q(originalUser__username=user) for user in list(part for part in request.GET.get("users").split(" ") if part != '')]
    if request.GET.get("hashtags"):
        search = True
        for hashtag in list(part for part in request.GET.get("hashtags").split(" ") if part != ''):
            hashtagResults += [r.tweet for r in HashtagLog.objects.all().select_related('tweet').select_related('hashtag').filter(hashtag__hashtagText=hashtag)]
    if request.GET.get("keywords"):
        search = True
        keywordQueryies = [Q(originalText__icontains=keyword) for keyword in list(part for part in request.GET.get("keywords").split(" ") if part != '')]

    queries = userQueries + keywordQueryies

    if queries:
        query = queries.pop()

        for item in queries:
            query |= item

        tweetsList = list(Tweet.objects.filter(query))

        tweetsList += hashtagResults
    elif hashtagResults:
        tweetsList = hashtagResults
    if search:
        tweetsList = sorted(tweetsList, key=lambda k: k.createdAt, reverse=True)

        if fromDate and toDate:
            tweetsList = [x for x in tweetsList if x.createdAt >= fromDate and x.createdAt <= toDate]
        elif fromDate:
            tweetsList = [x for x in tweetsList if x.createdAt >= fromDate]
        elif toDate:
            tweetsList = [x for x in tweetsList if x.createdAt <= toDate]

        paginator = Paginator(tweetsList, 24)
        page = request.GET.get('page')
        tweets = paginator.get_page(page)

    return render(request, 'index.html', {'tweets':tweets, 'twitterSearchDict': currentTwitterSearchDict})

def setTwitterSearchQuery(request):
    global currentTwitterSearchDict
    currentTwitterSearchDict['accounts'] = list(part for part in request.GET['pull-users'].split(" ") if part != '')
    currentTwitterSearchDict['notAccounts'] = list(part for part in request.GET['pull-not-users'].split(" ") if part != '')
    currentTwitterSearchDict['hashtags'] = list(part for part in request.GET['pull-hashtags'].split(" ") if part != '')
    currentTwitterSearchDict['keywords'] = list(part for part in request.GET['pull-keywords'].split(" ") if part != '')
    currentTwitterSearchDict['fromDate'] = request.GET['pull-since']
    if request.GET['pull-since'] != "":
        currentTwitterSearchDict['fromDate'] = datetime.strftime(datetime.strptime(request.GET['pull-since'], '%b %d, %Y'), '%Y-%m-%d')
    currentTwitterSearchDict['toDate'] = request.GET['pull-until']
    if request.GET['pull-until'] != "":
        currentTwitterSearchDict['toDate'] = datetime.strftime(datetime.strptime(request.GET['pull-until'], '%b %d, %Y'), '%Y-%m-%d')
    currentTwitterSearchDict['andHashtags'] = False
    currentTwitterSearchDict['andKeywords'] = False
    buildTwitterSearchQuery(currentTwitterSearchDict)

    return redirect('/')

def get_download_path():
    """Returns the default downloads path for linux or windows"""
    if os.name == 'nt':
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser('~'), 'downloads')

def download(csvName):
    global tweetsList

    filePath = get_download_path() + "/" + csvName + ".csv"
    with open(filePath, mode='w') as csv_file:
        fieldnames = ['datetime', 'last updated', 'original username', 'original screen name',
                      'original user location', 'original user verified', 'retweet', 'retweeter username',
                      'retweeter screen name', 'retweeter location', 'retweeter verified', 'text', 'comment',
                      'hashtags', 'urls', '#retweets','#favorites', '#retweets of retweet',
                      '#favorites of retweet', 'syllable count', 'lexicon count',
                      'sentence count', 'flesch reading ease score', 'flesch-kincaid grade level',
                      'fog scale', 'smog index', 'automated readability index', 'coleman-liau index',
                      'linsear write level', 'dale-chall readability score', 'difficult words',
                      'readability consensus', 'neg sentiment', 'neu sentiment', 'pos sentiment',
                      'overall sentiment']

        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(fieldnames)

        for tweet in tweetsList:

            hashtagString = ""
            tweetHashtags = HashtagLog.objects.filter(tweet__id=tweet.id)
            for i in range(len(tweetHashtags)):
                if i == 0:
                    hashtagString += tweetHashtags[i].hashtag.hashtagText
                else:
                    hashtagString += ", " + tweetHashtags[i].hashtag.hashtagText

            urlString = ""
            tweetUrls = UrlLog.objects.filter(tweet__id=tweet.id)
            for i in range(len(tweetUrls)):
                if i == 0:
                    urlString += tweetUrls[i].url.urlText
                else:
                    urlString += ", " + tweetUrls[i].url.urlText

            if tweet.originalUser.isVerified:
                originalVerifiedString = "yes"
            else:
                originalVerifiedString = "no"


            newUsername = None
            newScreenName = None
            newLocation = None
            newVerifiedString = None
            if tweet.newUser:
                if tweet.newUser.isVerified:
                    newVerifiedString = "yes"
                else:
                    newVerifiedString = "no"
                newUsername = tweet.newUser.username
                newScreenName = tweet.newUser.screenName
                newLocation = tweet.newUser.location

            if tweet.isRetweet:
                isRetweetString = "yes"
            else:
                isRetweetString = "no"

            sid_obj = SentimentIntensityAnalyzer()
            sentiment_dict = sid_obj.polarity_scores(tweet.originalText)
            writer.writerow(
                [tweet.createdAt, tweet.lastUpdated, tweet.originalUser.username,
                 tweet.originalUser.screenName, tweet.originalUser.location, originalVerifiedString,
                 isRetweetString, newUsername, newScreenName, newLocation, newVerifiedString,
                 tweet.originalText, tweet.commentText, hashtagString, urlString, tweet.numRetweetsOriginal,
                 tweet.numFavoritesOriginal, tweet.numRetweetsNew, tweet.numFavoritesNew,
                 textstat.syllable_count(tweet.originalText, lang='en_US'),
                 textstat.lexicon_count(tweet.originalText, removepunct=True),
                 textstat.sentence_count(tweet.originalText),
                 textstat.flesch_reading_ease(tweet.originalText),
                 textstat.flesch_kincaid_grade(tweet.originalText),
                 textstat.gunning_fog(tweet.originalText),
                 textstat.smog_index(tweet.originalText),
                 textstat.automated_readability_index(tweet.originalText),
                 textstat.coleman_liau_index(tweet.originalText),
                 textstat.linsear_write_formula(tweet.originalText),
                 textstat.dale_chall_readability_score(tweet.originalText),
                 textstat.difficult_words(tweet.originalText),
                 textstat.text_standard(tweet.originalText, float_output=False),
                 sentiment_dict['neg'], sentiment_dict['neu'],
                 sentiment_dict['pos'], sentiment_dict['compound']])
