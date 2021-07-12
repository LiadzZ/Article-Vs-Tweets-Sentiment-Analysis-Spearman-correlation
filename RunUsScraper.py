from usNewsScraper import *
from pymongo import MongoClient



client = MongoClient("mongodb+srv://")

db = client.USArticles




def run_scraper (scraper):
    scraper.get_pages()
    data = scraper.newspaper_parser()
    
    scraper.write_to_mongo(data, db.articles)



#run_scraper(LaTimesScraper("LaTimes","Covid","20-5-2020","25-5-2020"))

run_scraper(TimeScraper("Time","Covid","20-6-2020","25-7-2020"))

#run_scraper(ChicagoTribuneScraper("LaTimes","Covid","1-6-2020","10-6-2020"))
