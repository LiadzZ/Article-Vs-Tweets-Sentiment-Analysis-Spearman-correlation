from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from pymongo import MongoClient
# from wordcloud import WordCloud, STOPWORDS
# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# from sklearn.feature_extraction.text import CountVectorizer
# import re
# import pandas
#
# import seaborn as sns

client = MongoClient("mongodb+srv://Test1:Test1@cluster0-pwaip.mongodb.net/test?retryWrites=true&w=majority")

db = client.USArticles


num_of_articles = 0
total_articles = []
keywords_list = []
keywords_dict = {}
all_text = ""
news_outlet = "Time"
with client:
    #db = client.Categories
    articles = db.articles
    for x in articles.find({"news_outlet": news_outlet}, {'text': 1,'keywords':1}):
        num_of_articles +=1
        #print(x)
        total_articles.append(x['text'])
        keywords = x['keywords']
        for word in keywords:
            all_text += word + " "
            keywords_list.append(word)
            if word in keywords_dict:
                keywords_dict[word] += 1
            else:
                keywords_dict[word] = 1
file_name = news_outlet+"KeyWords.csv"
with open(file_name, 'w') as f:
    for key in keywords_dict.keys():
        f.write("%s,%s\n"%(key,keywords_dict[key]))
#
# corpus = keywords_list
# #Most frequently occuring words
# def get_top_n_words(corpus, n=None):
#     vec = CountVectorizer().fit(corpus)
#     bag_of_words = vec.transform(corpus)
#     sum_words = bag_of_words.sum(axis=0)
#     words_freq = [(word, sum_words[0, idx]) for word, idx in
#                    vec.vocabulary_.items()]
#     words_freq =sorted(words_freq, key = lambda x: x[1],
#                        reverse=True)
#     return words_freq[:n]
#
#
# #Convert most freq words to dataframe for plotting bar plot
# top_words = get_top_n_words(corpus, n=20)
# top_df = pandas.DataFrame(top_words)
# top_df.columns=["Word", "Freq"]
#
# #Barplot of most freq words
# sns.set(rc={'figure.figsize':(13,8)})
# g = sns.barplot(x="Word", y="Freq", data=top_df)
# g.set_xticklabels(g.get_xticklabels(), rotation=30)

#text = keywords_list[1]

#print(all_text)
# t = "Hello how are you Hello yoday you okay or are you not"
# wordcloud = WordCloud(stopwords=STOPWORDS, background_color='white',max_words=50,collocations=False, width=3000, height=3000).generate(t)
# plt.imshow(wordcloud)
# plt.axis('off')
# plt.show()


        #print(x['keywords'])

    #
    #
    # for x in articles.find({"website": link}, {"_id": 0,"website": 1, "name": 1, "link": 1}):
    #     if ".com" in x['link']: # i dont want .co.il
    #         categories_link[x['name']] = x['link']





scores =  {"Positive": 0 , "Negative": 0 , "Neutral": 0}
scores_list = []

analyzer = SentimentIntensityAnalyzer()
pos=neg=neu=compound=compound2=0


#sentences = nltk.sent_tokenize(text.lower())
for article in total_articles:
    idx = 1
    pos = neg = neu = compound = compound2 = 0
    peregraphs = article.split("Advertisement")
    for per in peregraphs:
        sentences = per.split(".")
        for sentence in sentences:
            #print("Sent:", sentence)
            if(len(sentence) < 3):
                continue
            print("Sent:", sentence)
            sent_len = len(sentence.split(" "))
            if sent_len < 1:
                sent_len = 50
            vs = analyzer.polarity_scores(sentence)
            pos += vs["pos"]
            neg += vs["neg"]
            neu += vs["neu"]
            #compound += vs["compound"] / sent_len
            compound2 += vs["compound"]

            print("pos:", pos)
            print("neg:", neg)
            print("neu:", neu)
            print("compound:", compound2)
            idx += 1

            print("--------------")
            print(vs)
            print("--------------")

    print("Final result for the article:")
    print("idx:",idx)
    print("pos:", pos/idx)
    print("neg:", neg/idx)
    print("neu:", neu/idx)
    #print("compound1:", compound)
    print("compound2:", compound2)
    print("Score:",compound2/idx)
    #print("keywords:",keywords_list)
    print("num_of_articles",num_of_articles)
    print("--------------")
    score = compound2/idx
    if score >= 0.05:
        scores["Positive"] += 1
        scores_list.append("Positive")
        print("Positive")

    elif score <= - 0.05:
        scores["Negative"] += 1
        scores_list.append("Negative")
        print("Negative")

    else:
        scores["Neutral"] += 1
        scores_list.append("Neutral")
        print("Neutral")



print(scores)
print(scores_list)
