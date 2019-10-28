import tweepy
import csv
consumer_key = "065p3Ddh3T1rxoAbhsNQKTT0r"
consumer_secret = "qHTYc1aLUfVFCezVLz1U0yPphthRM0DevNL2AKSxG4LTrzWiWA"

access_token = "1176877630382985217-qFO9wveUf0LycpO8cP23ISSVMr1U3g"
access_token_secret = "1zr5Guity4uffdYKQ9XCfP6M1r1e8VmeLd6y3Cm9wzoBk"

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
	m = tweet.entities.get('media')
	tweetDict['media'] = []
	if m:
		for mDict in m:
			tweetDict['media'].append(mDict['display_url'])
	for uDict in u:
		tweetDict['urls'].append(uDict['url'])
	tweets.append(tweetDict)

print(tweets)

with open('employee_file.csv', mode='w') as csv_file:
	employee_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	employee_writer.writerow([tweets[0]['text'], tweets[1]['text'], tweets[2]['text']])

