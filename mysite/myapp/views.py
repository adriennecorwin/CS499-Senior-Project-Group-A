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
from datetime import datetime
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
    return render(request, 'index.html', {'tweets':tweets})

def search(request):
    searchDict = {}
    searchDict['accounts'] = request.POST['users'].split(" ")
    searchDict['hashtags'] = request.POST['hashtags'].split(" ")
    searchDict['keywords'] = request.POST['keywords'].split(" ")

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