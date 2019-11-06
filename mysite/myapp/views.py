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

from .tasks import pull

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



