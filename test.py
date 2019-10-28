import tweepy
import mysql.connector
from datetime import datetime, timedelta
import re

class Tweet:
	def __init__(self, username, screenName, userLocation, isVerified, createdAt, text, hashtags, numRetweets, numFavorites, isQuoteTweet, urls):
		self.username = username.replace("\'", "\\\'")
		self.screenName = screenName.replace("\'", "\\\'")
		self.userLocation = userLocation.replace("\'", "\\\'")
		if isVerified:
			self.isVerified = 1
		else:
			self.isVerified = 0
		self.createdAt = createdAt
		self.text = text.replace("\'", "\\\'")
		self.hashtags = hashtags
		self.numRetweets = numRetweets
		self.numFavorites = numFavorites
		if isQuoteTweet:
			self.isQuoteTweet = 1
		else:
			self.isQuoteTweet = 0
		self.urls = urls
		#self.lastUpdated = now

class SearchController:
	#def __init__(self, view):
	def __init__(self):
		
		#self.view = view

		self.database = mysql.connector.connect(
  			host="localhost",
  			user="root",
  			passwd="#####",
  			database="SupremeCourtTwitter"
		)

		self.cursor = self.database.cursor()

		consumer_key = "#####"
		consumer_secret = "#####"

		access_token = "#####"
		access_token_secret = "#####"

		auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
		auth.set_access_token(access_token, access_token_secret)

		self.api = tweepy.API(auth)

		self.twitterSearchQueries = []

	def buildTwitterSearchQuery(self):
		self.twitterSearchQueries = []
		#build queries based on dictionary from view class and appends them to self.twitterSearchQueries
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

		self.twitterSearchQueries.append(hashtagQuery)

		accountsQuery = ""
		for i in range(len(searchDict['accounts'])):
			accountsQuery += "from:" + searchDict['accounts'][i] + " OR "
		for i in range(len(searchDict['accounts'])):
			accountsQuery += "to:" + searchDict['accounts'][i] + " OR "
		for i in range(len(searchDict['accounts'])):
			accountsQuery += "@" + searchDict['accounts'][i]
			if i < len(searchDict['accounts']) - 1:
				 accountsQuery += " OR "
		self.twitterSearchQueries.append(accountsQuery)

		if searchDict['fromDate'] != "":
			fromDateQuery = " since:" + searchDict['fromDate']
			for i in range(len(self.twitterSearchQueries)):
				self.twitterSearchQueries[i] += fromDateQuery
		if searchDict['toDate'] != "":
			toDateQuery = " until:" + searchDict['toDate']
			for i in range(len(self.twitterSearchQueries)):
				self.twitterSearchQueries[i] += toDateQuery

	def parseTwitterResponse(self, response):
		# tweets = []
		# for t in response:
		# 	h = t.entities.get('hashtags')
		# 	hashtags = []
		# 	for hDict in h:
		# 		hashtags.append(hDict['text'])
		# 	u = t.entities.get('urls')
		# 	urls = []
		# 	for uDict in u:
		# 		urls.append(uDict['url'])
		# 	if hasattr(t, 'retweeted_status'):
		# 		isRetweet = True
		# 	else:
		# 		isRetweet = False
		# 	tweet = Tweet(t.user.name, t.user.screen_name, t.user.location, t.user.verified, t.created_at, t.full_text, hashtags, t.retweet_count, t.favorite_count, isRetweet, urls)
		# 	tweets.append(tweet)
		# return tweets
		tweets = []
		for r in response:
			ts = []
			if hasattr(r, 'retweeted_status'):
				ts.append(r.retweeted_status)
			elif hasattr(r, 'quoted_status'):
				ts.append(r.quoted_status)
				r.is_quote_status = True
				ts.append(r)
			for t in ts:
				h = t.entities.get('hashtags')
				hashtags = []
				for hDict in h:
					hashtags.append(hDict['text'])
				u = t.entities.get('urls')
				urls = []
				for uDict in u:
					urls.append(uDict['url'])

				tweet = Tweet(t.user.screen_name, t.user.name, t.user.location, t.user.verified, t.created_at, t.full_text, hashtags, t.retweet_count, t.favorite_count, r.is_quote_status, urls)
				tweets.append(tweet)
		return tweets

	def separateNewFromExisting(self, tweets):
		new = []
		existing = []
		for tweet in tweets:
			tweetExistsQuery = "SELECT 1 FROM tweet WHERE username=\'" + tweet.username + "\' and created_at=\'" + tweet.createdAt.strftime('%Y-%m-%d %H:%M:%S') + "\'"
			self.cursor.execute(tweetExistsQuery)
			tweetExistsResult = self.cursor.fetchall()
			if len(tweetExistsResult) == 0:
				new.append(tweet)
			else:
				existing.append(tweet)
		return existing, new
		#separates tweets into list of existing (already in db) and new
		#return existing, new

	def insert(self, tweets):
			
		for tweet in tweets:
			userExistsQuery = "SELECT 1 FROM user WHERE username=\'" + tweet.username + "\'"
			self.cursor.execute(userExistsQuery)
			userExistsResult = self.cursor.fetchall()
			if len(userExistsResult) == 0:
				insertNewUserQuery = "INSERT INTO user (username, screen_name, location, is_verified) VALUES (%s, %s, %s, %s)"
				insertUserVals = (tweet.username, tweet.screenName, tweet.userLocation, tweet.isVerified)
				self.cursor.execute(insertNewUserQuery, insertUserVals)
				self.database.commit()

			for hashtag in tweet.hashtags:
				hashtagExistsQuery = "SELECT 1 FROM hashtag WHERE hashtag_text=\'" + hashtag + "\'"
				self.cursor.execute(hashtagExistsQuery)
				hashtagExistsResult = self.cursor.fetchall()
				if len(hashtagExistsResult) == 0:
					insertNewHashtagQuery = "INSERT INTO hashtag (hashtag_text) VALUES (%s)"
					insertHashtagVals = (hashtag,)
					self.cursor.execute(insertNewHashtagQuery, insertHashtagVals)
					self.database.commit()

			for url in tweet.urls:
				urlExistsQuery = "SELECT 1 FROM url WHERE url_text=\'" + url + "\'"
				self.cursor.execute(urlExistsQuery)
				urlExistsResult = self.cursor.fetchall()
				if len(urlExistsResult) == 0:
					insertNewUrlQuery = "INSERT INTO url (url_text) VALUES (%s)"
					insertUrlVals = (url,)
					self.cursor.execute(insertNewUrlQuery, insertUrlVals)
					self.database.commit()

			insertNewTweetQuery = "INSERT INTO tweet (username, created_at, text, num_retweets, num_favorites, is_quote_tweet) VALUES (%s, %s, %s, %s, %s, %s)"
			insertTweetVals = (tweet.username, tweet.createdAt.strftime('%Y-%m-%d %H:%M:%S'), tweet.text, tweet.numRetweets, tweet.numFavorites, tweet.isQuoteTweet)
			self.cursor.execute(insertNewTweetQuery, insertTweetVals)
			self.database.commit()

			self.cursor.execute("SELECT LAST_INSERT_ID()")

			tweetIdQueryResult = self.cursor.fetchall()

			tweetId = tweetIdQueryResult[0][0]

			for hashtag in tweet.hashtags:
				insertHashtagLogQuery = "INSERT INTO hashtag_log (tweet_id, hashtag_text) VALUES(%s, %s)"
				insertHashtagLogVals = (tweetId, hashtag)
				self.cursor.execute(insertHashtagLogQuery, insertHashtagLogVals)
				self.database.commit()

			for url in tweet.urls:
				insertUrlLogQuery = "INSERT INTO url_log (tweet_id, url_text) VALUES(%s, %s)"
				insertUrlLogVals = (tweetId, url)
				self.cursor.execute(insertUrlLogQuery, insertUrlLogVals)
				self.database.commit()

	def update(self, tweets):
		for tweet in tweets:
			updateQuery = "UPDATE tweet SET num_retweets=" + tweet['numRetweets'] + ", num_favorites=" + tweet['num_favorites'] + " WHERE username=\'" + tweet['username'] + "\' and created_at=" + tweet['createdAt']
			self.cursor.execute(updateQuery)
			self.database.commit()
	
	def searchTwitter(self):
		#should iterate through self.twitterSearchQueries
		#but for now just do it for Tom Brady
		allSearchResults = set()
		for query in self.twitterSearchQueries:
			response = self.api.search(q=query, count=100, tweet_mode='extended')
			tweets = self.parseTwitterResponse(response)
			for tweet in tweets:
				allSearchResults.add(tweet)

		allSearchResults = list(allSearchResults)

		return allSearchResults

	def pull(self):
		self.buildTwitterSearchQuery()
		searchResults = self.searchTwitter()
		existing, new = self.separateNewFromExisting(searchResults)
		self.update(existing)
		self.insert(new)
		#set view class var tweetsToDisplay to everything in db
		#TODO: how do we update the list if they are searching, maybe have a button so they can pull only when they are ready? and disable the button if a new pull isn't available
		#view.display()

controller = SearchController()
controller.pull()
