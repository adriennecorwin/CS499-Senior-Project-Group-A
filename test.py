import tweepy
import mysql.connector

class TweetModel:
	def __init__(self, username, screenName, userLocation, isVerified, createdAt, text, hashtags, numRetweets, numFavorites, isRetweet):
		self.username = username
		self.screenName = screenName	
		self.userLocation = userLocation
		self.isVerified = isVerified
		self.createdAt = createdAt
		self.text = text
		self.hashtags = hashtags
		self.numRetweets = numRetweets
		self.numFavorites = numFavorites
		self.isRetweet = isRetweet
		#self.lastUpdated = now

class SearchController:
	def __init__(self, view):
		
		self.view = view

		self.database = mysql.connector.connect(
  			host="localhost",
  			user="root",
  			passwd="########",
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
		#self.twitterSearchQueries = []
		#build queries based on dictionary from view class and appends them to self.twitterSearchQueries

	def parseTwitterResponse(self, response):
		tweets = []
		for t in response:
			h = tweet.entities.get('hashtags')
			hashtags = []
			for hDict in h:
				hashtags.append(hDict['text'])
			tweet = Tweet(tweet.user.name, tweet.user.screen_name, tweet.user.location, tweet.created_at, tweet.full_text, hashtags, tweet.retweet_count, tweet.favorite_count, tweet.retweeted)
			tweets.append(tweet)
		return tweets

	def separateNewFromExisting(self, tweets):
		#separates tweets into list of existing (already in db) and new
		#return existing, new

	def insert(self, tweets):
			
		for tweet in tweets:
			userExistsQuery = "SELECT 1 FROM user WHERE username=\'" + tweet.username + "\')"
			self.cursor.execute(userExistsQuery)
			userExistsResult = self.cursor.fetchall()
			if len(userExistsResult) == 0:
				insertNewUserQuery = "INSERT INTO user (username, screen_name, location, is_verified) VALUES (\'%s\', \'%s\', \'%s\', )"
				insertUserVals = (tweet.username, tweet.screenName, tweet.userLocation, tweet.isVerified)
				self.cursor.execute(insertNewUserQuery, insertUserVals)
				self.database.commit()
			for hashtag in tweet.hashtags:
				hashtagExistsQuery = "SELECT 1 FROM hashtag WHERE hashtag_name=\'" + hashtag + "\')"
				hashtagExistsResult = self.cursor.execute(userExistsQuery)
				if len(hashtagExistsResult) == 0:
					insertNewHashtagQuery = "INSERT INTO hashtag (hashtag_name) VALUES (\'%s\')"
					insertHashtagVals = (hashtag)
					self.cursor.execute(insertNewHashtagQuery, insertHashtagVals)
					self.database.commit()
			#insertNewTweetQuery = "INSERT INTO tweets (username, created_at, text, num_retweets, num_favorites) VALUES (\'%s\', 

	def searchTwitter(self):
		#should iterate through self.twitterSearchQueries
		#but for now just do it for Tom Brady
		allSearchResults = ()
		response = api.search(q="Tom Brady", count=100, tweet_mode='extended')
		tweets = parseTwitterResponse(response)
		for tweet in tweets:
			allSearchResults.add(tweet)

		allSearchResults = list(allSearchResults)

		return allSearchResults

	def pull(self):
		searchResults = searchTwitter()
		#existing, new = separateOldAndNew(searchResults)
		#update(existing)
		#insert(new)
		#set view class var tweetsToDisplay to everything in db
		#TODO: how do we update the list if they are searching, maybe have a button so they can pull only when they are ready? and disable the button if a new pull isn't available
		#view.display()
		
