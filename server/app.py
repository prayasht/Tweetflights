import json
import tweepy
import configparser
from kafka import SimpleProducer, KafkaClient


class TStreamListener(tweepy.StreamListener):
    """ A class to read the twitter stream via tweepy and push it to a Kafka producer.
    We attach the tweepy.StreamListener instance to this class in order to publish
    live tweets to our Kafka producer.
    Attributes:
        api: An instance of StreamListener from the tweepy API.
        producer: A Kafka Producer to send messages to a consumer
    """

    def __init__(self, api):
        self.api = api
        super(tweepy.StreamListener, self).__init__()

        # Instantiate a KafkaClient on local machine.
        client = KafkaClient("127.0.0.1:9092")
        self.producer = SimpleProducer(client, async = True,
                          batch_send_every_n = 1000,
                          batch_send_every_t = 10)

    def on_status(self, status):
        """ This method is called whenever new data arrives from the live stream.
        We asynchronously push this data to Kafka queue.
        """
        # msg = status.text.encode('utf-8')
        
        try:
            twitter_json = json.dumps(status._json).encode('utf-8')
            twitterFilterJSON = json.loads(twitter_json)

            if twitterFilterJSON["entities"]['user_mentions'] is not None and len(twitterFilterJSON["entities"]['user_mentions']) > 0:
                if twitterFilterJSON['place'] is not None:
                    if not twitterFilterJSON['text'].startswith('RT'):

                        toUser_id = twitterFilterJSON["entities"]['user_mentions'][0]["id_str"]

                        twitter_id_json = json.dumps(api.get_user(toUser_id)._json).encode('utf-8')
                        toUserId_filter_JSON = json.loads(twitter_id_json)
                        # print toUserId_filter_JSON

                        if toUserId_filter_JSON["profile_location"] is not None:
                            # print (twitterFilterJSON['text'])
                            # print "TO:" + toUserId_filter_JSON["profile_location"]['name']
                            # print "From:" + str(twitterFilterJSON['place']['full_name'])

                            tweetJSON = "{\"text\": \"" + twitterFilterJSON['text'].encode('utf-8') + "\", \"fromLocation\": \"" + twitterFilterJSON['place']['full_name'].encode('utf-8') + "\", \"toLocation\": \"" + toUserId_filter_JSON["profile_location"]['name'].encode('utf-8') + "\" }".encode('utf-8')
                            print tweetJSON
                            self.producer.send_messages('twitterstream', tweetJSON)


        except Exception as e:
            # Catch any unicode errors while printing to console
            # and just ignore them to avoid breaking application.
            pass
            print(e)
            return False

        return True

    def on_error(self, status_code):
        """ This method is called when a new error is encountered.
        The status code should give enough indication as to why the
        error has occured.
        """

        print(status_code)
        print("An error occured in the Kafka producer.")

        # Don't kill the stream.
        return True

    def on_timeout(self):
        """ This method is called when a the stream has timed out."""

        print("The stream listener has timed out.")

        # Don't kill the stream.
        return True


if __name__ == '__main__':

    # Read the auth keys from 'keys.txt' file - only store locally!
    config = configparser.ConfigParser()
    config.read('keys.txt')

    # consumer_key = config['DEFAULT']['consumerKey']
    # consumer_secret = config['DEFAULT']['consumerSecret']
    # access_key = config['DEFAULT']['accessToken']
    # access_secret = config['DEFAULT']['accessTokenSecret']
    consumer_key = 'z7mSIufiB7Lom9dJyvQ3blEDR'
    consumer_secret = 'V3Xq4WxpJAo6LWjRLipThKC10wMZHDHfhZQNzDYl6Kg0CIBlgA'
    access_key = '717173546-jgCRHCgVeW9ShqRxRPUko1eEX0dW8v0VM0UrNiLS'
    access_secret = 'kM2ENz91HTDVuC2NajwE1cD7rZVa52hPSgAQP7Y9lEfLZ'

    # Create auth object to consume tweepy's API.
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)

    # Create a tweepy stream and bind the listener to it.
    stream = tweepy.Stream(auth, listener = TStreamListener(api))

    # Custom filters!
    #stream.filter(track = ['love', 'hate'], languages = ['en'])
    stream.filter(languages = ['en','fr'], locations=[-180, -90, 180, 90])
