# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.

class User(models.Model):
    username = models.CharField(max_length=20) #Twitter usernames can be no longer than 15 characters
    screenName = models.CharField(max_length=100) #Twitter screen names can be no longer than 50 characters
    location = models.CharField(max_length=200) #Twitter bios can be no longer than 160 characters
    isVerified = models.BooleanField()

class Hashtag(models.Model):
    hashtagText = models.TextField(max_length=500) #Tweet that is just a hashtag

class Url(models.Model):
    urlText = models.TextField() #Tweet that is just a hashtag

class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    createdAt = models.DateTimeField()
    isRetweet = models.BooleanField()
    originalText = models.TextField(max_length=500) #Tweets can be no longer than 246 characters
    commentText = models.TextField(max_length=500, null=True)
    numRetweetsOriginal = models.IntegerField()
    numRetweetsNew = models.IntegerField(null=True)
    numFavoritesOriginal = models.IntegerField()
    numFavoritesNew = models.IntegerField(null=True)
    lastUpdated = models.DateTimeField()

    def getUsername(self):
        return self.user.username

class HashtagLog(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE)

class UrlLog(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    url = models.ForeignKey(Url, on_delete=models.CASCADE)
