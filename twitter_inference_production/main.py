import os
import tweepy
from tweepy import Stream
import nest_asyncio
import psycopg2
from tweepy import StreamListener
import numpy as np
from scipy.stats import beta as beta_distribution



CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCES_TOKEN')
ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_TOKEN_SECRET')


COLOMBIA_GEO_LOCATION_BOUNDING_BOX = [-78.31, 0.44, -70.71, 11.39]
NUMBER_OF_TWEETS = 100


# 
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)
 
from unidecode import unidecode

def make_lowercase(tweet):
    return tweet.lower()

def remove_diacritics(tweet):
    return unidecode(tweet)
def remove_non_alpha_characters(tweet):
    return ''.join(character for character in tweet if character.isalpha() or character == ' ')


DATABASE_NAME = 'twitter_inference'
TABLE_NAME = 'tweets'
USER = 'admindb'
HOST = 'localhost'
PASSWORD = 'toor'


class PersistedStreamListener(StreamListener):
    def __init__(self):
        self._database_connection = psycopg2.connect(dbname=DATABASE_NAME, user=USER, host=HOST, password=PASSWORD)
        super().__init__()

    def on_status(self, status):
        cleaned_status_text = self._clean_status_text(status.text)
        self._insert_status(id_str=status.id_str, text = cleaned_status_text)

    def _clean_status_text(self, status_text):
        cleaned_status_text = status_text
        for cleaning_function in self._cleaning_functions:
            cleaned_status_text = cleaning_function(cleaned_status_text)
        return cleaned_status_text

    def _insert_status(self, id_str, text):
        cursor = self._database_connection.cursor()
        insert_statement = f""" INSERT INTO {TABLE_NAME} VALUES ( '{id_str}', '{text}' ); """
        #import pdb; pdb.set_trace()
        cursor.execute(insert_statement)
        self._database_connection.commit()
        cursor.close()
    
    @property
    def _cleaning_functions(self):
        return [make_lowercase, remove_diacritics, remove_non_alpha_characters]


# 
streaming_api = Stream(auth=auth, listener=PersistedStreamListener())
streaming_api.filter(locations=COLOMBIA_GEO_LOCATION_BOUNDING_BOX, is_async=True)


# 

X_VALUES = np.linspace(0,1,1002)[1:-1]
DATABASE_CONNECTION = psycopg2.connect(dbname=DATABASE_NAME, user=USER, host=HOST, password=PASSWORD)
KEYWORD = 'yo'

def fetch_tweets(db_conn = DATABASE_CONNECTION):
    cursor = db_conn.cursor()
    select_statement = f"""SELECT tweet FROM {TABLE_NAME}"""
    cursor.execute(select_statement)
    result = cursor.fetchall()

    return [tweet[0] for tweet in result]


def compute_alpha_and_beta(tweets, keyword=KEYWORD):
    number_of_occurrences = sum(keyword in tweet for tweet in tweets)
    alpha = 1 + number_of_occurrences
    beta = 1 + (len(tweets)- number_of_occurrences)
    
    return alpha, beta
    

def compute_pdf_y_values(alpha, beta, x_values=X_VALUES):
    return beta_distribution(alpha, beta).pdf(x_values)


# 
nest_asyncio.apply()


# 
from bokeh.client import push_session
from bokeh.models import FixedTicker
from bokeh.plotting import figure, curdoc, reset_output

# reset_output
reset_output()

# initialize alpha, beta
tweets = fetch_tweets()
alpha, beta = compute_alpha_and_beta(tweets=tweets)
pdf_y_values = compute_pdf_y_values(alpha, beta)

# create bokeh figure
bokeh_figure = figure(
    title='PDF of True Probability of a Tweet containing keyword',
    x_axis_label='True probability',
    y_axis_label='probability_density',
    width=1000,
    height=600
)
bokeh_figure.xaxis[0].ticker=FixedTicker(ticks=list(np.linspace(0, 1, 21)))
bokeh_line = bokeh_figure.line(X_VALUES, pdf_y_values, color="navy", line_width=4)

# open a session to keep out local document in sync with server
session = push_session(curdoc())

def update():
    tweets = fetch_tweets()
    alpha, beta = compute_alpha_and_beta(tweets=tweets)
    pdf_y_values = compute_pdf_y_values(alpha, beta)
    bokeh_line.data_source.data.update(y=pdf_y_values)

curdoc().add_periodic_callback(update, 50)

session.show(bokeh_figure)
session._loop_until_closed()
#session.loop_until_closed()


# 
len(fetch_tweets())


# 
from bokeh.client import push_session
from bokeh.models import FixedTicker
from bokeh.plotting import figure, curdoc, reset_output

# reset output
reset_output()

# initialize alpha, beta
tweets = fetch_tweets()
alpha, beta = compute_alpha_and_beta(tweets=tweets)
pdf_y_values = compute_pdf_y_values(alpha, beta)

# create bokeh figure
bokeh_figure = figure(
    title='PDF of True Probability of a Tweet Containing Keyword',
    x_axis_label='true_probability',
    y_axis_label='probability_density',
    width=1000,
    height=600
)
bokeh_figure.xaxis[0].ticker=FixedTicker(ticks=list(np.linspace(0, 1, 21)))
bokeh_line = bokeh_figure.line(X_VALUES, pdf_y_values, color="navy", line_width=4)

# open a session to keep our local document in sync with server
session = push_session(curdoc())

def update():
    tweets = fetch_tweets()
    alpha, beta = compute_alpha_and_beta(tweets=tweets)
    pdf_y_values = compute_pdf_y_values(alpha, beta)
    
    bokeh_line.data_source.data.update(y=pdf_y_values)

curdoc().add_periodic_callback(update, 50)

session.show(bokeh_figure)

session._loop_until_closed()


