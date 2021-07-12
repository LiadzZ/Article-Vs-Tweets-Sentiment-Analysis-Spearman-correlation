import warnings
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt
import scipy.stats
import pandas as pd
import random
import seaborn as sns






def Snippet_121():

    print(format('Spearman\'s correlation'))

    # Create empty dataframe

    df = pd.DataFrame()

    # Add columns
    #df['x'] = random.sample(range(1, 100), 75)


    df['x'] = [39, 16, 20,
               31, 15, 25,
               16, 17, 22,
               24, 10, 21,
               20, 16, 25,
               ]
    df['y'] = [448,155,452,
               425, 151, 392,
               427, 122, 390,
               402, 162, 382,
               420, 145, 393,
               ]


    def spearmans_rank_correlation(xs, ys):
        # Calculate the rank of x's
        xranks = pd.Series(xs).rank()
        # Caclulate the ranking of the y's
        yranks = pd.Series(ys).rank()
        # Calculate Pearson's correlation coefficient on the ranked versions of the data
        return scipy.stats.pearsonr(xranks, yranks)
    # Show Pearson's Correlation Coefficient
    result = spearmans_rank_correlation(df.x, df.y)[0]

    print("spearmans_rank_correlation is: ", result)
    # Calculate Spearman’s Correlation Using SciPy
    print("Scipy spearmans_rank_correlation is: ", scipy.stats.spearmanr(df.x, df.y)[0])
    # reg plot
    # sns.lmplot('x', 'y', data=df, fit_reg=True)
    # plt.show()
Snippet_121()

#
# import matplotlib.pyplot as plt
# x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# y = [2, 4, 5, 7, 6, 8, 9, 11, 12, 12]
#
# plt.scatter(x, y, label="stars", color="green",
#             marker="1", s=30)
#
#
# plt.xlabel('x - axis')
# plt.ylabel('y - axis')
#
# plt.title('Scatter plot')
# plt.legend()
#
# plt.show()
