# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.models import User as account
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage
from django.contrib.auth import login
from .tasks import *
from .forms import SignUpForm, ProfileForm
from datetime import datetime, timedelta
import pytz
import csv
import os
import textstat
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


currentTwitterSearchDict = {} #dictionary with parameters to search twitter by in array form
tweetsList = [] #list of tweets to dispaly on website
dbSearchDict = {} #dictioanry of search fields parameters (so they can be saved and redisplayed when user changes pages or downloads)
pullParameters = {} #dictionary with parameters to search twitter by in string form (to display in website)

# home page controller
def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    global currentTwitterSearchDict, tweetsList, pullParameters

    #get what users entered into search bars (so we can redisplay them in the search bars when a download occurs)
    if request.GET.get("users"):
        dbSearchDict['users'] = request.GET.get("users")
    if request.GET.get("hashtags"):
        dbSearchDict['hashtags'] = request.GET.get("hashtags")
    if request.GET.get("keywords"):
        dbSearchDict['keywords'] = request.GET.get("keywords")
    if request.GET.get("to"):
        dbSearchDict['to'] = request.GET.get("to")
    if request.GET.get("from"):
        dbSearchDict['from'] = request.GET.get("from")

    if request.GET.get("page"):
        paginator = Paginator(tweetsList, 24)
        page = request.GET.get('page')
        tweets = paginator.get_page(page)
        return render(request, 'index.html', {'tweets': tweets, 'twitterSearchDict': pullParameters, 'dbSearchDict':dbSearchDict, 'pulling': pulling['pulling'], 'warning':None, 'error':None})

    if request.GET.get("pull-users") or request.GET.get("pull-not-users") or request.GET.get("pull-hashtags") or request.GET.get("pull-keywords"):
        # get entries from form as list (parse entries by space)
        currentTwitterSearchDict['accounts'] = list(part for part in request.GET['pull-users'].split(" ") if part != '')
        currentTwitterSearchDict['notAccounts'] = list(
            part for part in request.GET['pull-not-users'].split(" ") if part != '')
        currentTwitterSearchDict['hashtags'] = list(
            part for part in request.GET['pull-hashtags'].split(" ") if part != '')
        currentTwitterSearchDict['keywords'] = list(
            part for part in request.GET['pull-keywords'].split(" ") if part != '')

        currentTwitterSearchDict['fromDate'] = request.GET['pull-since']
        # get date of x number of days ago from today as specified user in form
        if request.GET['pull-since'] != "":
            currentTwitterSearchDict['fromDate'] = datetime.strftime(
                timezone.now() - timedelta(int(request.GET['pull-since'])), '%Y-%m-%d')

        currentTwitterSearchDict['toDate'] = request.GET['pull-until']
        if request.GET['pull-until'] != "":
            # if user entered "tomorrow" get date of tomorrow
            if int(request.GET['pull-until']) == 8:
                currentTwitterSearchDict['toDate'] = datetime.strftime(timezone.now() + timedelta(1), '%Y-%m-%d')
            else:
                currentTwitterSearchDict['toDate'] = datetime.strftime(
                    timezone.now() - timedelta(int(request.GET['pull-until'])), '%Y-%m-%d')

        # set twitter search query and string
        pullParameters = getPullParametersAsStrings(currentTwitterSearchDict)

        tweetsList = Tweet.objects.all().order_by('-createdAt')  # get list of all tweets in db most recent to least
        paginator = Paginator(tweetsList, 24)  # only display 24 tweets per page
        page = request.GET.get('page')
        tweets = paginator.get_page(page)

        if not currentTwitterSearchDict['accounts'] and not currentTwitterSearchDict['hashtags'] and not \
                currentTwitterSearchDict['keywords']:
            return render(request, 'index.html',
                          {'tweets': tweets, 'twitterSearchDict': pullParameters, 'dbSearchDict': dbSearchDict,
                           'pulling': pulling['pulling'],
                           'warning': "No tweets will be pulled. Must search by at least on of the user, hashtag, or keyword fields.",
                           'error': None})

        if currentTwitterSearchDict['fromDate'] == currentTwitterSearchDict['toDate'] and currentTwitterSearchDict[
            'fromDate'] != "":
            return render(request, 'index.html',
                          {'tweets': tweets, 'twitterSearchDict': pullParameters, 'dbSearchDict': dbSearchDict,
                           'pulling': pulling['pulling'],
                           'warning': "No tweets will be pulled. From and to dates cannot be the same.",
                           'error': None})
        if (buildTwitterSearchQuery(currentTwitterSearchDict)):
            return redirect('/scotustwitter')
        else:
            return render(request, 'index.html',
                          {'tweets': tweets, 'twitterSearchDict': pullParameters, 'dbSearchDict': dbSearchDict,
                           'pulling': pulling['pulling'],
                           'warning': None,
                           'error': "Too many search parameters. Must be fixed before moving on!"})

    #refresh fields so that old search queries won't show up
    dbSearchDict['users'] = request.GET.get("users")
    dbSearchDict['hashtags'] = request.GET.get("hashtags")
    dbSearchDict['keywords'] = request.GET.get("keywords")
    dbSearchDict['to'] = request.GET.get("to")
    dbSearchDict['from'] = request.GET.get("from")

    #get tweets to display
    tweetsList = Tweet.objects.all().order_by('-createdAt') #get list of all tweets in db most recent to least
    paginator = Paginator(tweetsList, 24) #only display 24 tweets per page
    page = request.GET.get('page')
    tweets = paginator.get_page(page)

    #refresh
    if request.GET.get("refresh"): #refresh page aka display all tweets from db again
        if request.GET.get("refresh") == "true":
            return redirect('/scotustwitter')

    #search
    userQueries = []
    keywordQueries = []
    hashtagResults = []

    fromDate = None
    toDate = None
    search = False #true if user entered something into search bars

    #get entries from search form
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
        keywordQueries = [Q(originalText__icontains=keyword) for keyword in list(part for part in request.GET.get("keywords").split(" ") if part != '')]

    #OR fields
    if request.GET.get("ANDOR") == "OR" or request.GET.get("ANDOR") == None:
        queries = userQueries + keywordQueries

        #if user and keyword entries in search bars
        if queries:
            query = queries.pop()

            for item in queries: #OR all queries together
                query |= item

            tweetsList = list(Tweet.objects.filter(query)) #put result of filter in list

            tweetsList += hashtagResults #add the hashtag results to list

        #if no user or keyword entries but hashtag entries
        elif hashtagResults:
            tweetsList = hashtagResults

    #AND fields
    else:
        usersList = []
        keywordList = []

        #get results of user filter
        if userQueries:
            query = userQueries.pop()
            for item in userQueries:
                query |= item

            usersList = list(Tweet.objects.filter(query))

        #get results of keyword filter
        if keywordQueries:
            query = keywordQueries.pop()
            for item in keywordQueries:
                query |= item

            keywordList = list(Tweet.objects.filter(query))

        #if at least 2 of the user, hashtag, or keyword fields have entries, AND results of users, keywords, hashtags queries
        #if none or 1 of the fields is filled out, treat like OR instead
        if request.GET.get("user") != "" and request.GET.get("hashtags") != "" or request.GET.get("user") != "" and request.GET.get("keywords") != "" or request.GET.get("keywords") != "" and request.GET.get("hashtags") != "":
            tweetsList = list(set.intersection(*(set(x) for x in [usersList, keywordList, hashtagResults] if x)))
        else:
            tweetsList = usersList + keywordList + hashtagResults

    if search: #filter list by desired dates
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

    return render(request, 'index.html', {'tweets':tweets, 'twitterSearchDict':pullParameters, 'dbSearchDict':dbSearchDict, 'pulling':pulling['pulling'], 'warning':None, 'error':None})

# performs language processing and downloads all tweets currently being displayed in all pages into a csv file
# input:name of csv to download to
# output: None
def download(request):
    global tweetsList

    response = HttpResponse(content_type='application/x-download')
    response['Content-Disposition'] = 'attachment; filename="tweets.csv"'

    #set headers of csv
    fieldnames = ['datetime', 'last updated', 'original username', 'original screen name',
                  'original user location', 'original user verified', 'retweet', 'retweeter username',
                  'retweeter screen name', 'retweeter location', 'retweeter verified', 'text', 'comment',
                  # 'hashtags', 'urls', '#retweets','#favorites', '#retweets of retweet',
                  'hashtags', 'urls', '#retweets', '#favorites',
                  '#favorites of retweet', 'original syllable count', 'original lexicon count',
                  'original sentence count', 'original flesch reading ease score', 'original flesch-kincaid grade level',
                  'original fog scale', 'original smog index', 'original automated readability index', 'original coleman-liau index',
                  'original linsear write level', 'original dale-chall readability score', 'original difficult words',
                  'original readability consensus', 'original neg sentiment', 'original neu sentiment', 'original pos sentiment',
                  'original overall sentiment', 'comment syllable count', 'comment lexicon count',
                  'comment sentence count', 'comment flesch reading ease score', 'comment flesch-kincaid grade level',
                  'comment fog scale', 'comment smog index', 'comment automated readability index', 'comment coleman-liau index',
                  'comment linsear write level', 'comment dale-chall readability score', 'comment difficult words',
                  'comment readability consensus', 'comment neg sentiment', 'comment neu sentiment', 'comment pos sentiment',
                  'comment overall sentiment', 'combined syllable count', 'combined lexicon count',
                  'combined sentence count', 'combined flesch reading ease score', 'combined flesch-kincaid grade level',
                  'combined fog scale', 'combined smog index', 'combined automated readability index', 'combined coleman-liau index',
                  'combined linsear write level', 'combined dale-chall readability score', 'combined difficult words',
                  'combined readability consensus', 'combined neg sentiment', 'combined neu sentiment', 'combined pos sentiment',
                  'combined overall sentiment', 'twitter users query', 'twitter excluded users query', 'twitter hashtags query', 'twitter keywords query',
                  'twitter from date query', 'twitter to date query']

    writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(fieldnames)

    for tweet in tweetsList:
        #combine hashtags of tweet into string separated by commas
        hashtagString = ""
        tweetHashtags = HashtagLog.objects.filter(tweet__id=tweet.id)
        for i in range(len(tweetHashtags)):
            if i == 0:
                hashtagString += tweetHashtags[i].hashtag.hashtagText
            else:
                hashtagString += ", " + tweetHashtags[i].hashtag.hashtagText

        #combine urls of tweet into string separated by commas
        urlString = ""
        tweetUrls = UrlLog.objects.filter(tweet__id=tweet.id)
        for i in range(len(tweetUrls)):
            if i == 0:
                urlString += tweetUrls[i].url.urlText
            else:
                urlString += ", " + tweetUrls[i].url.urlText

        #display yes or no in verified column for original user
        if tweet.originalUser.isVerified:
            originalVerifiedString = "yes"
        else:
            originalVerifiedString = "no"

        #if not a retweet, new user fields should be empty
        newUsername = None
        newScreenName = None
        newLocation = None
        newVerifiedString = None

        #if retweet:
        #display yes or no in verified column for new user
        if tweet.newUser:
            if tweet.newUser.isVerified:
                newVerifiedString = "yes"
            else:
                newVerifiedString = "no"

            #set retweet fields
            newUsername = tweet.newUser.username
            newScreenName = tweet.newUser.screenName
            newLocation = tweet.newUser.location

        #display yes or no in retweet column
        if tweet.isRetweet:
            isRetweetString = "yes"
        else:
            isRetweetString = "no"

        #get sentiment scores of original text
        sid_obj = SentimentIntensityAnalyzer()
        sentiment_dict_original = sid_obj.polarity_scores(tweet.originalText)

        #combine comment text and original tezt and get sentiment scores for the combination
        commentText = ""
        if tweet.commentText:
            commentText = tweet.commentText
        sentiment_dict_combined = sid_obj.polarity_scores(tweet.originalText + commentText)

        #intialize all comment word processing to empty strings in case there is no comment text
        cSyllableCount = ""
        cLexiconCount = ""
        cSentenceCount = ""
        cFleschReadingEase = ""
        cFleschKincaidGrade = ""
        cGunningFog = ""
        cSmogIndex = ""
        cAutomatedReadabilityIndex = ""
        cColemanLiauIndex = ""
        cLinsearWriteFormula = ""
        cDaleChallReadabilityScore = ""
        cDifficultWords = ""
        cTextStandard = ""

        #if there is comment text, get language processing stats for comment text
        if tweet.commentText != None:
            cSyllableCount = textstat.syllable_count(tweet.commentText, lang='en_US')
            cLexiconCount = textstat.lexicon_count(tweet.commentText, removepunct=True)
            cSentenceCount = textstat.sentence_count(tweet.commentText)
            cFleschReadingEase = textstat.flesch_reading_ease(tweet.commentText)
            cFleschKincaidGrade = textstat.flesch_kincaid_grade(tweet.commentText)
            cGunningFog = textstat.gunning_fog(tweet.commentText)
            cSmogIndex = textstat.smog_index(tweet.commentText)
            cAutomatedReadabilityIndex = textstat.automated_readability_index(tweet.commentText)
            cColemanLiauIndex = textstat.coleman_liau_index(tweet.commentText)
            cLinsearWriteFormula = textstat.linsear_write_formula(tweet.commentText)
            cDaleChallReadabilityScore = textstat.dale_chall_readability_score(tweet.commentText)
            cDifficultWords = textstat.difficult_words(tweet.commentText)
            cTextStandard = textstat.text_standard(tweet.commentText, float_output=False)

        #get sentiment scores for comment text
        cNegSent = ""
        cNeuSent = ""
        cPosSent = ""
        cCompoundSent = ""
        if tweet.commentText:
            sentiment_dict_comment = sid_obj.polarity_scores(tweet.commentText)
            cNegSent = sentiment_dict_comment['neg']
            cNeuSent = sentiment_dict_comment['neu']
            cPosSent = sentiment_dict_comment['pos']
            cCompoundSent = sentiment_dict_comment['compound']

        #write all information about the tweet, and its language processing stats to row in csv
        writer.writerow(
            [tweet.createdAt, tweet.lastUpdated, tweet.originalUser.username,
             tweet.originalUser.screenName, tweet.originalUser.location, originalVerifiedString,
             isRetweetString, newUsername, newScreenName, newLocation, newVerifiedString,
             tweet.originalText, tweet.commentText, hashtagString, urlString, tweet.numRetweetsOriginal,
             # tweet.numFavoritesOriginal, tweet.numRetweetsNew, tweet.numFavoritesNew,
             tweet.numFavoritesOriginal, tweet.numFavoritesNew,
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
             sentiment_dict_original['neg'], sentiment_dict_original['neu'],
             sentiment_dict_original['pos'], sentiment_dict_original['compound'], cSyllableCount,
             cLexiconCount, cSentenceCount, cFleschReadingEase, cFleschKincaidGrade, cGunningFog,
             cSmogIndex, cAutomatedReadabilityIndex, cColemanLiauIndex, cLinsearWriteFormula, cDaleChallReadabilityScore,
             cDifficultWords, cTextStandard, cNegSent, cNeuSent, cPosSent, cCompoundSent,
             textstat.syllable_count(tweet.originalText + commentText, lang='en_US'),
             textstat.lexicon_count(tweet.originalText + commentText, removepunct=True),
             textstat.sentence_count(tweet.originalText + commentText),
             textstat.flesch_reading_ease(tweet.originalText + commentText),
             textstat.flesch_kincaid_grade(tweet.originalText + commentText),
             textstat.gunning_fog(tweet.originalText + commentText),
             textstat.smog_index(tweet.originalText + commentText),
             textstat.automated_readability_index(tweet.originalText + commentText),
             textstat.coleman_liau_index(tweet.originalText + commentText),
             textstat.linsear_write_formula(tweet.originalText + commentText),
             textstat.dale_chall_readability_score(tweet.originalText + commentText),
             textstat.difficult_words(tweet.originalText + commentText),
             textstat.text_standard(tweet.originalText + commentText, float_output=False),
             sentiment_dict_combined['neg'], sentiment_dict_combined['neu'],
             sentiment_dict_combined['pos'], sentiment_dict_combined['compound'],
             tweet.twitterQueryUsers, tweet.twitterQueryNotUsers,
             tweet.twitterQueryHashtags, tweet.twitterQueryKeywords,
             tweet.twitterQueryFromDate, tweet.twitterQueryToDate]
        )

    return response

def signup(request):
    if request.method == 'POST':
        userForm = SignUpForm(request.POST)
        profileForm = ProfileForm(request.POST)
        if userForm.is_valid() and profileForm.is_valid():
            user = userForm.save(commit=False)
            user.is_active = False
            user.save()
            profile = profileForm.save(commit=False)
            profile.user = account.objects.get(id=user.id)
            profile.save()
            current_site = get_current_site(request)
            subject = 'Activate SCOTUS Twitter Website Account'
            message = render_to_string('account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'reason': profile.reason,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })

            email = EmailMessage(
                subject, message, to=os.environ['ADMIN_EMAILS'].split(",")
            )
            email.send()
            return HttpResponse('Your access request has been sent to an administrator.\nYou will be emailed once you accound has been approved.\nAfter that you will be able to sign into the website.')
    else:
        userForm = SignUpForm()
        profileForm = ProfileForm(request.POST)
    return render(request, 'signup.html', {'userForm': userForm, 'profileForm': profileForm})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = account.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, account.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        current_site = get_current_site(request)
        subject = 'Your SCOTUS Twitter website account has been activated'
        message = user.first_name + " " + user.last_name + ",\n\nYour SCOTUS Twitter accout has been activated. You can now login to the website.\n\nhttp://" + current_site.domain + "/login"

        email = EmailMessage(
            subject, message, to=[user.email]
        )
        email.send()
        return HttpResponse('Thank you for your email confirmation. The new user can now login to their account.')
    else:
        return HttpResponse('Activation link is invalid!')
def error(request):
    return render(request, 'error.html')



pullParameters = getPullParametersAsStrings(initialSearchDict)
