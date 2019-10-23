import tweepy

consumer_key = "#####"
consumer_secret = "#####"

access_token = "#####"
access_token_secret = "#####"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

tweets = []
response = api.search(q="Tom Brady", count=100, tweet_mode='extended')
for tweet in response:
	tweetDict = {}
	tweetDict['username'] = tweet.user.name
	tweetDict['screenName'] = tweet.user.screen_name
	tweetDict['userLocation'] = tweet.user.location
	tweetDict['isVerified'] = tweet.user.verified
	tweetDict['createdAt'] = tweet.created_at
	tweetDict['text'] = tweet.full_text
	tweetDict['numRetweets'] = tweet.retweet_count
	tweetDict['numFavorites'] = tweet.favorite_count
	tweetDict['isRetweet'] = tweet.retweeted
	h = tweet.entities.get('hashtags')
	tweetDict['hashtags'] = []
	for hDict in h:
		tweetDict['hashtags'].append(hDict['text'])
	u = tweet.entities.get('urls')
	tweetDict['urls'] = []
	for uDict in u:
		tweetDict['urls'].append(uDict['url'])
	tweets.append(tweetDict)

print(tweets)
