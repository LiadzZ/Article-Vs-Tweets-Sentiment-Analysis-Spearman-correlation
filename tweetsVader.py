import twint
# from optimus import Optimus
import nest_asyncio
from ast import literal_eval
from textblob import TextBlob
from IPython.display import Markdown, display
from pyspark.sql.functions import udf
import os
import pandas as pd
import sys
import re
import seaborn as sns
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer



class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
nest_asyncio.apply()
#op = Optimus()


c = twint.Config()
analyzer = SentimentIntensityAnalyzer()


def available_columns():
    return twint.output.panda.Tweets_df.columns

def twint_to_pandas(columns):
    return twint.output.panda.Tweets_df[columns]





def printmd(string, color=None):
    colorstr = "<span style='color:{}'>{}</span>".format(color, string)
    display(Markdown(colorstr))



def apply_vader(sentence):
    vs = analyzer.polarity_scores(sentence)
    #temp = TextBlob(sentence).sentiment[0]
    vs["compound"]
    if vs["compound"] <=  -0.05:
        return "Negative" # Negative
    elif vs["compound"] >= 0.05:
        return "Positive" # Positive
    else:
        return "Neutral"# Neutral


#sentiment = udf(apply_blob)



def read_tweets(search, limit=1,until = "2020-05-26 00:00:00"):
    c.Search = search
    # Custom output format
    c.Format = "Username: {username} |  Tweet: {tweet}"
    c.Limit = limit
    c.Popular_tweets = True
    c.Lang = "en"
    # c.Translate = True

    #c.Geo(lat=36.778,lng=-119.417)
    #c.Geo("36.778259, -119.417931,10km")
    # location = 'California'
    # c.Near(location)
    c.Store_csv = True
    # c.Since = '2019-05-25'
    c.Until = until
    c.Pandas = True
    c.Output = "TopPopularAfter25.csv"
    twint.run.Search(c)

    with HiddenPrints():
        twint.run.Search(c)


def sentiment_analysis():
    all_data = pd.read_csv("TopPopularAfter25.csv", converters={"hashtags": literal_eval})
    all_data = all_data.drop_duplicates(subset='id', keep="first")

    data = pd.DataFrame(all_data[["date", "username", "tweet", "hashtags", "likes_count"]])
    # Regex pattern for only alphanumeric, hyphenated text with 2 or more chars
    data.dropna(inplace=True)
    pattern = re.compile(r"[A-Za-z0-9\-]{1,50}")
    data['clean_tweet'] = data['tweet'].str.findall(pattern).str.join(' ')
    

    return data



df_result = sentiment_analysis()

tweets = df_result['clean_tweet'].tolist()
sent_list = []
for tweet in tweets:
    answer = apply_vader(tweet)
    sent_list.append(answer)

df_result["sentiment"] = sent_list

df_result.to_csv("TopPopularAfter25VaderResult.csv")
