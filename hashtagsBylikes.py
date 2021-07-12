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


all_data = pd.read_csv("TopPopularAfter25.csv", converters={"hashtags": literal_eval})
likes_count = all_data["likes_count"].tolist()
hashTags_data = pd.read_csv("TopPopularAfter25resultHashtags.csv")

hashTags = hashTags_data['word'].tolist()

temp_dict = {}

for x,value in all_data['hashtags'].items():
    for word in value:
        new_word = word.strip(" #")
        if new_word in hashTags:
            if new_word in temp_dict:
                temp_dict[new_word] += likes_count[x]
            else:
                temp_dict[new_word] = likes_count[x]


likes_count_hashtag = []
for hashtag in hashTags:
    if hashtag in temp_dict:
        likes_count_hashtag.append(temp_dict[hashtag])
    else:
        likes_count_hashtag.append(1)


hashTags_data['likes_count'] = likes_count_hashtag

hashTags_data.to_csv("TopPopularAfter25resultHashtags2.csv")

