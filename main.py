import urllib
import pymongo
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import feedparser
import re
import string
from nltk.corpus import stopwords
import nltk

nltk.download("stopwords")

def func(url, source):
    feeds = feedparser.parse(url)
    feeds_cleaned = []
    stops = stopwords.words("english")
    for feed in feeds.entries:
        x = (re.sub("<[^<]+?>", " ", feed.description))
        x_stopped = " ".join(y for y in x.split() if y not in stops)
        if len(list(x_stopped)) > 3:
            feeds_cleaned.append(x_stopped)

    analyzer = SentimentIntensityAnalyzer()
    sentiments = [
        "positive"
        if analyzer.polarity_scores(i).get("compound") >= 0.01 else "negative"
        if analyzer.polarity_scores(i).get("compound") <= -0.01 else "neutral"
        for i in feeds_cleaned
    ]

    positive_percent = (sentiments.count("positive") / len(sentiments)) * 100
    negative_percent = (sentiments.count("negative") / len(sentiments)) * 100
    neutral_percent = (sentiments.count("neutral") / len(sentiments)) * 100
    print(f"Overall sentiment percentage from {source} \npositive: {positive_percent}% \nnegative: {negative_percent}% \nneutral: {neutral_percent}%")

    df = pd.DataFrame(data={"feeds": feeds_cleaned})
    df["sentiments"] = sentiments
    df["source"] = source
    df["words"] = [list(set(feeds.split(" "))) for feeds in feeds_cleaned]
    return df


client = pymongo.MongoClient()
db = client.get_database("RSS")


def send_to_DB(dataframe, name):
    user_collection = pymongo.collection.Collection(db, name)
    data_to_push = dataframe.to_dict("records")
    user_collection.delete_many({})
    user_collection.insert_many(data_to_push)


fox_url = "http://feeds.foxnews.com/foxnews/latest"
send_to_DB(func(fox_url, "Fox News"), "Fox News")

ny_url = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
send_to_DB(func(ny_url, "NewYork Times"), "NewYork Times")

wsPost_url = "http://feeds.washingtonpost.com/rss/rss_powerpost?itid=lk_inline_manual_3"
send_to_DB(func(wsPost_url, "Washington Post"), "Washington Post")
