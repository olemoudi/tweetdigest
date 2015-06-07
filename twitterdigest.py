#!/usr/bin/python -u
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import traceback
import sched
import sys
import time
from collections import defaultdict
from threading import RLock
import re
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
import smtplib
import cgi


class TwitterDigester(StreamListener):

    def __init__(self, config=None):
        self.lock = RLock()
        self.config = config
        self.clean_report()
        self.tweet_count = 0
        self.selected_tweets = 0
        self.error = False
        super(TwitterDigester, self).__init__()

    def clean_report(self):
        with self.lock:
            self.report = {} 
            self.report['golds'] = defaultdict(list)
            self.report['patterns'] = defaultdict(list)
            self.report['retweeted'] = []
            self.report['favorited'] = []
            self.tweet_count = 0
            self.selected_tweets = 0

    def on_status(self, status):
        selected = False
        with self.lock:
            self.tweet_count += 1
            try:
                if len(status.text) > self.config['tweet_length']:
                    # check goldlist
                    if status.user.screen_name.lower() in map(str.lower, self.config['golds']):
                        self.report['golds'][status.user.screen_name].append(status)
                        selected = True
                    # check patterns
                    for pattern in self.config['patterns']:
                        regex = re.compile(pattern, re.IGNORECASE|re.DOTALL)
                        if regex.search(status.text):
                            self.report['patterns'][pattern].append(status)
                            selected = True
                    # check RT and FAV number
                    if hasattr(status, 'retweeted_status'):
                        if int(status.retweeted_status.retweet_count) in self.config['rt_range']:
                            self.report['retweeted'].append(status)
                            selected = True
                        elif int(status.retweeted_status.favorite_count) in self.config['fav_range']:
                            self.report['favorited'].append(status)
                            selected = True

                if selected:
                    self.selected_tweets += 1
                    print
                    print "\033[92m@%s\033[0m : %s" %(status.user.screen_name,  status.text)
                    print

                print "\r\033[91m%i\033[0m Tweets Monitored"  % (self.tweet_count), 
            except Exception as e:
                print e
                traceback.print_stack()
                # something is bad
                raise e

    def on_disconnect(self, notice):
        self.error = True

    def on_error(self, error):
        self.error = True

    def on_timeout(self):
        self.error = True

    def on_exception(self, exception):
        self.error = True

    def send_email(self):


        with self.lock:
            copy = self.report.copy()

            try:

                strFrom = self.config['email']
                strTo = self.config['target']

                # Create message container - the correct MIME type is multipart/alternative.
                msg = MIMEMultipart('alternative')
                msg['Subject'] = "Twitter Digest [%s]" % time.strftime('%d %b %H:%M')
                msg['From'] = strFrom
                msg['To'] = strTo

                # Create the body of the message (a plain-text and an HTML version).
                # TODO: make plain text version
                text = ""
                html = """\
                <html>
                <head></head>
                <body>
                <h2>Twitter Digest</h2>
                Total selected tweets: <b>%i</b><br>
                Total tweets monitored: <b>%i</b><br>
                Selection Ratio: <b>%.1f%%</b><br>
                <h3>Gold Tweeters</h3>
                """ % (self.selected_tweets, self.tweet_count, self.selected_tweets * 100 / float(self.tweet_count))
                for gold in copy['golds'].keys():
                    html += '<ul>' 
                    for status in copy['golds'][gold]:
                        html += '<li><a href="https://twitter.com/%s" target="_blank">@%s</a> : %s - [<a href="https://twitter.com/%s/status/%s" target="_blank">Link</a>]</li>' %(gold, gold,  cgi.escape(status.text).encode('ascii', 'xmlcharrefreplace'), gold, status.id)
                    html += '</ul><br>'

                html += '<h3>Patterns</h3>'
                for pattern in copy['patterns'].keys():
                    html += '%s<br><ul>' % pattern
                    for status in copy['patterns'][pattern]:
                        html += '<li><a href="https://twitter.com/%s" target="_blank">@%s</a> : %s< - [<a href="https://twitter.com/%s/status/%s" target="_blank">Link</a>]</li>' %(status.user.screen_name, status.user.screen_name,  cgi.escape(status.text).encode('ascii', 'xmlcharrefreplace'), status.user.screen_name, status.id)
                    html += '</ul><br>'

                html += '<h3>Most Retweeted</h3><ul>' 
                for status in copy['retweeted']:
                    html += '<li>[%i] <a href="https://twitter.com/%s" target="_blank">@%s</a> : %s - [<a href="https://twitter.com/%s/status/%s" target="_blank">Link</a>]</li>' %(status.retweeted_status.retweet_count, status.user.screen_name, status.user.screen_name,  cgi.escape(status.text).encode('ascii', 'xmlcharrefreplace'), status.user.screen_name, status.id)
                html += '</ul><br>'

                html += '<h3>Most Faved</h3><ul>' 
                for status in copy['favorited']:
                    html += '<li>[%i] <a href="https://twitter.com/%s" target="_blank">@%s</a> : %s - [<a href="https://twitter.com/%s/status/%s" target="_blank">Link</a>]</li>' %(status.retweeted_status.favorite_count, status.user.screen_name, status.user.screen_name,  cgi.escape(status.text).encode('ascii', 'xmlcharrefreplace'), status.user.screen_name, status.id)
                html += '</ul><br>'
                html +="""\
                </body>
                </html>
                """

                # Record the MIME types of both parts - text/plain and text/html.
                part1 = MIMEText(text, 'plain')
                part2 = MIMEText(html, 'html')

                # Attach parts into message container.
                # According to RFC 2046, the last part of a multipart message, in this case
                # the HTML message, is best and preferred.
                msg.attach(part1)
                msg.attach(part2)

                # Send the email (this example assumes SMTP authentication is required)
                server = smtplib.SMTP(self.config['smtpserver'])
                #server.ehlo()
                server.starttls()
                server.login(self.config['email'], self.config['password'])
                server.sendmail(strFrom, strTo, msg.as_string())
                server.quit()

                self.clean_report()
                print
                print "\033[91m[%s] Digest Email Sent!\033[0m"  % time.strftime('%H:%M')
                print
            except Exception as e:
                print e
                traceback.print_stack()

        if self.error:
            raise

if __name__ == '__main__':

    while True:
        try:
            config = {}
            execfile(sys.argv[1], config)
            td = TwitterDigester(config)
            auth = OAuthHandler(td.config['consumer_key'], td.config['consumer_secret'])
            auth.set_access_token(td.config['access_token'], td.config['access_token_secret'])

            stream = Stream(auth, td)    
            stream.userstream(async=True)
            stream_filter = Stream(auth, td)    
            stream_filter.filter(track=td.config['track_terms'], async=True)

            scheduler = sched.scheduler(time.time, time.sleep)
            while True:
                scheduler.enter(td.config['periodicity'], 1, td.send_email, ([]))
                scheduler.run()
        except KeyboardInterrupt:
            print
            print "Ctrl+C detected, sending email..."
            td.send_email()

        except Exception as e:
            print e
            traceback.print_stack()
            time.sleep(180)
        finally:
            try:
                stream.disconnect()
                stream_filter.disconnect()
            except:
                pass
