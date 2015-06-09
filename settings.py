periodicity = 86400 # amount of seconds between every digest email
target = "me@email.com" # digest recipient email
smtpserver = "smtp.gmail.com:587" # smtp connections tring host:port
email = "gmailaccount@gmail.com" # sender email used as login for the smtp server
password = "thepassword" # smtp password


# All tweets from gold handles will be included in the digest
golds = ['twitter', 'facebook', 'google']

# All tweets from the timeline with matching regex patterns will be included in the digest
patterns = ['win', 'prize']

# additional stream keywords to add to the user timeline (mind the amount of tweets)
track_terms = ['contest', 'soccer','film']

# blacklist of regexes
blacklist = []

# Tweets with RT or Fav values within these ranges will be included in the digest
rt_range = range(3, 20)
fav_range = range(2, 8)

# Minimum length for an interesting tweet (tip: http://t.co/xxxxxxxxxx is 22)
tweet_length = 22

# Go to http://dev.twitter.com and create an app. 
# The consumer key and secret will be generated for you after
consumer_key="xxxxxx"
consumer_secret="yyyyyy"

# After the step above, you will be redirected to your app's page.
# Create an access token under the the "Your access token" section
access_token="zzzzzzz"
access_token_secret="aaaaaaa"

