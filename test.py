import tweepy
import mysql.connector
from datetime import datetime, timedelta
import re

class Tweet:
	def __init__(self, username, screenName, userLocation, isVerified, createdAt, isRetweet, originalText, commentText, hashtags, urls, numRetweetsOriginal, numRetweetsNew, numFavoritesOriginal, numFavoritesNew):
		self.username = username.replace("\'", "\\\'")
		self.screenName = screenName.replace("\'", "\\\'")
		self.userLocation = userLocation.replace("\'", "\\\'")
		if isVerified:
			self.isVerified = 1
		else:
			self.isVerified = 0
		self.createdAt = createdAt
		if isRetweet:
			self.isRetweet = 1
		else:
			self.isRetweet = 0
		self.originalText = originalText.replace("\'", "\\\'")

		self.commentText = commentText
		if commentText != None:
			self.commentText = commentText.replace("\'", "\\\'")

		self.hashtags = hashtags
		self.urls = urls
		self.numRetweetsOriginal = numRetweetsOriginal
		self.numRetweetsNew = numRetweetsNew
		self.numFavoritesOriginal = numFavoritesOriginal
		self.numFavoritesNew = numFavoritesNew
		#self.lastUpdated = now

class SearchController:
	#def __init__(self, view):
	def __init__(self):
		
		#self.view = view

		self.database = mysql.connector.connect(
  			host="localhost",
  			user="root",
  			passwd="u2109861",
  			database="SupremeCourtTwitter"
		)

		self.cursor = self.database.cursor()

		consumer_key = "065p3Ddh3T1rxoAbhsNQKTT0r"
		consumer_secret = "qHTYc1aLUfVFCezVLz1U0yPphthRM0DevNL2AKSxG4LTrzWiWA"

		access_token = "1176877630382985217-qFO9wveUf0LycpO8cP23ISSVMr1U3g"
		access_token_secret = "1zr5Guity4uffdYKQ9XCfP6M1r1e8VmeLd6y3Cm9wzoBk"

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
		for t in response:
			isRetweet = False
			commentText = None
			originalText = t.full_text
			numRetweetsOriginal = None
			numFavoritesOriginal = None
			if hasattr(t, 'retweeted_status'):
				isRetweet = True
				numRetweetsOriginal = t.retweeted_status.retweet_count
				numFavoritesOriginal = t.retweeted_status.favorite_count

			elif hasattr(t, 'quoted_status'):
				isRetweet = True
				originalText = t.quoted_status.full_text
				commentText = t.full_text
				numRetweetsOriginal = t.quoted_status.retweet_count
				numFavoritesOriginal = t.quoted_status.favorite_count

			h = t.entities.get('hashtags')
			hashtags = []
			for hDict in h:
				hashtags.append(hDict['text'])
			u = t.entities.get('urls')
			urls = []
			for uDict in u:
				urls.append(uDict['url'])

			tweet = Tweet(t.user.screen_name, t.user.name, t.user.location, t.user.verified, t.created_at, isRetweet, originalText, commentText, hashtags, urls, numRetweetsOriginal, t.retweet_count, numFavoritesOriginal, t.favorite_count)
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

			insertNewTweetQuery = "INSERT INTO tweet (username, created_at, is_retweet, original_text, comment_text, num_retweets_original, num_retweets_new, num_favorites_original, num_favorites_new) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

			insertTweetVals = (tweet.username, tweet.createdAt.strftime('%Y-%m-%d %H:%M:%S'), tweet.isRetweet, tweet.originalText, tweet.commentText, tweet.numRetweetsOriginal, tweet.numRetweetsNew, tweet.numFavoritesOriginal, tweet.numFavoritesNew)
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
		#TODO: fix for new db structure and using tweet obj instead of dict?
		for tweet in tweets:
			updateQuery = "UPDATE tweet SET num_retweets=" + tweet['numRetweets'] + ", num_favorites=" + tweet['num_favorites'] + " WHERE username=\'" + tweet['username'] + "\' and created_at=" + tweet['createdAt']
			self.cursor.execute(updateQuery)
			self.database.commit()
	
	def searchTwitter(self):
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
