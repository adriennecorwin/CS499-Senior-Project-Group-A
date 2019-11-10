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
# Create your views here.

def index(request):
    tweetsList = Tweet.objects.all().order_by('-createdAt')
    hashtagLog = HashtagLog.objects.all()
    urlLog = UrlLog.objects.all()
    paginator = Paginator(tweetsList, 24)
    page = request.GET.get('page')
    tweets = paginator.get_page(page)
    if request.GET.get("pull"):
        if request.GET.get("pull") == "true":
            return redirect('/')
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
        userQueries = [Q(user__username=user) for user in list(part for part in request.GET.get("users").split(" ") if part != '')]
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

    return render(request, 'index.html', {'tweets':tweets})

def setTwitterSearchQuery(request):
    searchDict = {}
    searchDict['accounts'] = list(part for part in request.GET['pull-users'].split(" ") if part != '')
    searchDict['notAccounts'] = list(part for part in request.GET['pull-not-users'].split(" ") if part != '')
    searchDict['hashtags'] = list(part for part in request.GET['pull-hashtags'].split(" ") if part != '')
    searchDict['keywords'] = list(part for part in request.GET['pull-keywords'].split(" ") if part != '')
    searchDict['fromDate'] = request.GET['pull-since']
    if request.GET['pull-since'] != "":
        searchDict['fromDate'] = datetime.strftime(datetime.strptime(request.GET['pull-since'], '%b %d, %Y'), '%Y-%m-%d')
    searchDict['toDate'] = request.GET['pull-until']
    if request.GET['pull-until'] != "":
        searchDict['toDate'] = datetime.strftime(datetime.strptime(request.GET['pull-until'], '%b %d, %Y'), '%Y-%m-%d')
    searchDict['andHashtags'] = False
    searchDict['andKeywords'] = False
    buildTwitterSearchQuery(searchDict)
    return redirect('/')