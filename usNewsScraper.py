import re
import csv
import time
import os
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pytz import timezone
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dateutil.parser import parse
from newspaper import Article
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class NewspaperScraper:
    def __init__ (self, newspaper, searchTerm, dateStart, dateEnd):
        self.newspaper = newspaper
        self.searchTerm = searchTerm
        self.dateStart = parse(dateStart)
        self.dateEnd = parse(dateEnd)
        self.links = []

    def get_newspaper_name (self):
        return self.newspaper

    def get_pages (self):
        print('Unimplemented for ' + self.newspaper + ' scraper')
        return

    def check_dates (self, date):
        print("Checking date...")
        page_date = parse(date)
        if page_date >= self.dateStart and page_date <= self.dateEnd:
            print("Date is fine..")
            return True
        return False

    def newspaper_parser (self, sleep_time=1.5):
        print('running newspaper_parser()...')

        results = []
        categories = []
        count = 0

        if self.newspaper == "LaTimes":
            categories = ["california","entertainment","sports","environment","opinion","world-nation",
                          "travel","science","politics","housing","climate","business"]

        for l in self.links:
            print("Try to extract article from : ", l)
            category = "None"
            for cat in categories:
                if cat in l:
                    #print("Yes!" , cat)
                    category = cat
            article = Article(url=l)
            try:
                article.build()
            except Exception as e:
                print("Error loading article")
                print(e)
                time.sleep(10)
                #continue
            



            data = {
                'title': article.title,
                'date_published': article.publish_date,
                'news_outlet': self.newspaper,
                'authors': article.authors,
                'feature_img': article.top_image,
                'article_link': article.canonical_link,
                'keywords': article.keywords,
                'movies': article.movies,
                'summary': article.summary,
                'text': article.text,
                'html': article.html,
                'category': category

            }

            
            if data:
                results.append(data)
                count += 1


            time.sleep(sleep_time)

        return results

    def write_to_csv (self, data, file_name):
        print('writing to CSV...')

        keys = data[0].keys()
        with open(file_name, 'wb') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)

    def write_to_mongo (self, data, collection):
        print('writing to mongoDB...')
        count = 0

        for d in data:
            collection.insert(d)
            count += 1
            print(count)


class NewspaperScraperWithAuthentication(NewspaperScraper):
    def __init__ (self, newspaper, searchTerm, dateStart, dateEnd, userID, password):
        NewspaperScraper.__init__(self, newspaper, searchTerm, dateStart, dateEnd)
        self.userId = userID
        self.password = password

        if newspaper == 'New York Times':
            self.credentials = {
                'userid': userID,
                'password1': password
            }
            self.login_url = 'https://myaccount.nytimes.com/auth/login'
            self.submit_id = 'submit'
        elif newspaper == 'Wall Street Journal':
            self.credentials = {
                'username': userID,
                'password': password
            }
            self.login_url = 'https://id.wsj.com/access/pages/wsj/us/signin.html'
            self.submit_id = 'submitButton'

    def newspaper_parser (self, sleep_time=0):
        print('running newspaper_parser()...')
        results = []
        count = 0

        profile = webdriver.FirefoxProfile()
        browser = webdriver.Firefox(profile)
        credential_names = self.credentials.keys()

        browser.get(self.login_url)
        cred1 = browser.find_element_by_id(credential_names[0])
        cred2 = browser.find_element_by_id(credential_names[1])
        cred1.send_keys(self.credentials[credential_names[0]])
        cred2.send_keys(self.credentials[credential_names[1]])
        browser.find_element_by_id(self.submit_id).click()
        time.sleep(15)

        cookies = browser.get_cookies()
        browser.close()

        s = requests.Session()
        for cookie in cookies:
            s.cookies.set(cookie['name'], cookie['value'])

        for l in self.links:
            page = s.get(l)
            soup = BeautifulSoup(page.content)
            article = Article(url=l)
            article.set_html(str(soup))

            try:
                article.parse()
                article.nlp()
            except:
                time.sleep(60)
                continue

            data = {
                'title': article.title,
                'date_published': article.publish_date,
                'news_outlet': self.newspaper,
                'authors': article.authors,
                'feature_img': article.top_image,
                'article_link': article.canonical_link,
                'keywords': article.keywords,
                'movies': article.movies,
                'summary': article.summary,
                'text': article.text,
                'html': article.html
            }

            results.append(data)
            time.sleep(sleep_time)

            count += 1

        return results


class ChicagoTribuneScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')
        # cap = DesiredCapabilities().FIREFOX
        # cap["marionette"] = False
        # browser = webdriver.Firefox(capabilities=cap)
        #browser.get('http://google.com/')
        #browser.quit()


        profile = webdriver.FirefoxProfile()

        browser = webdriver.Firefox(profile)
        #browser = webdriver.Firefox()
        # System.setProperty("webdriver.gecko.driver", "E:\\GekoDriver\\geckodriver-v0.15.0-win64\\geckodriver.exe");
        #
        # file = str(os.getcwd()) + "/geckodriver.exe"
        # browser = webdriver.Firefox(executable_path=file)

        links = []
        stop = False
        index = 1

        while not stop:
            browser.get('http://www.chicagotribune.com/search/dispatcher.front?page='
                        + str(index)
                        + '&sortby=display_time%20descending&target=stories&spell=on&Query='
                        + self.searchTerm
                        + '#trb_search')
            time.sleep(20)
            soup = BeautifulSoup(browser.page_source,'html.parser')

            if not soup.find('div', class_='trb_search_results'):
                stop = True

            for result in soup.find_all('div', class_="trb_search_result_wrapper"):
                pub_date = result.find('time', class_='trb_search_result_datetime').get('data-dt')
                if ':' in pub_date:
                    pub_date = str(datetime.now(timezone('America/Chicago')).date())

                if self.check_dates(pub_date):
                    link = result.find('a', class_='trb_search_result_title')
                    ltext = 'http://www.chicagotribune.com' + link.get('href')

                    if ltext not in links:
                        print(ltext)
                        links.append(ltext)

                else:
                    stop = True
                    break

            index += 1
            time.sleep(sleep_time)

        browser.close()
        self.links = links
        return links


class LaTimesScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3,num_of_pages = 50):
        print('running get_pages().HELLO..')
        profile = webdriver.FirefoxProfile()
        browser = webdriver.Firefox(profile)
        links = []
        stop = False
        index = 1
        while not stop:
            try:
                browser.get('http://www.latimes.com/search?q='
                    + self.searchTerm
                    + "&p="
                    + str(index)
                 )
            except:
                stop = True

            try:
                soup = BeautifulSoup(browser.page_source,'html.parser')
                print("Working on ",browser.current_url , "index:",index)
            except Exception as e:
                print("[ERROR]:Working on ",browser.current_url , "index:",index)
                stop = True
            #print(soup.prettify())
            if not soup.find('ul', class_='search-results-module-results-menu'):
                print("Error 304")
                stop = True
            for result in soup.find_all('div', class_='promo-wrapper'):
                pub_date = result.find('p', class_='promo-timestamp').get('data-date')
                print("pub_date:",pub_date)
                if self.check_dates(pub_date):
                    head_line = result.find('p', class_='promo-title')
                    head_line = str(head_line)
                    if head_line:
                        t = head_line.split('>')
                        #print("headline:", t)
                        link = t[1].split('href=')[1]
                        link = link.strip('\"')
                        if link not in links:
                            print("Adding link", link)
                            links.append(link)
                else:
                    print("Date is not in range")
            index += 1
            if index > num_of_pages + 1:
                stop = True
            time.sleep(sleep_time)
        browser.close()
        self.links = links
        return links


class WashPostScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')

        browser = webdriver.Chrome()

        links = []
        stop = False
        index = 0

        while not stop:
            browser.get('https://www.washingtonpost.com/newssearch/'
                        + '?utm_term=.94befa345ad6&query='
                        + self.searchTerm
                        + '&sort=Date&datefilter=12%20Months&contenttype=Article'
                        + '&spellcheck&startat=' + str(index) + '#top')

            soup = BeautifulSoup(browser.page_source)
            if not soup.find_all('div', class_="pb-feed-item"):
                stop = True
                continue

            for result in soup.find_all('div', class_="pb-feed-item"):
                if self.check_dates(result.find('span', class_='pb-timestamp').get_text()):
                    link = result.find('a', class_="ng-binding")
                    ltext = link.get('href')

                    if ltext not in links:
                        print(ltext)
                        links.append(ltext)

                else:
                    stop = True
                    break

            index += 20
            time.sleep(sleep_time)

        browser.close()
        self.links = links
        return links


class SlateScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')

        browser = webdriver.Chrome()

        links = []
        stop = False

        browser.get('http://www.slate.com/search.html#search=' + self.searchTerm)

        while not stop:
            soup = BeautifulSoup(browser.page_source)

            for result in soup.find_all('div', class_="full-width left-image"):
                if self.check_dates(result.find('span', class_='timestamp').get_text()):
                    ltext = result.find('a').get('href')
                    section = self.get_section(ltext)

                    if (section == 'articles' or section == 'blogs') and ltext not in links:
                        print(ltext)
                        links.append(ltext)

            header = soup.find('header', class_="tag-header").get_text().split()
            if int(header[2].split('-')[1]) == int(header[4]):
                stop = True

            try:
                element = browser.find_element_by_xpath('//*[@id="search_content"]/p/a')
                ActionChains(browser).move_to_element(element) \
                    .click(element) \
                    .perform()
                element = WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.ID, "search_results")))

            except:
                stop = True

            time.sleep(sleep_time)

        browser.close()
        self.links = links
        return links

    def get_section (self, href):
        href = href[20:]
        try:
            return re.search('/.*?/', href).group(0)[1:-1]
        except:
            return 'error'


class FoxNewsScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')

        profile = webdriver.FirefoxProfile()
        browser = webdriver.Firefox(profile)

        links = []
        stop = False
        index = 0

        while not stop:
            browser.get('http://www.foxnews.com/search-results/search?q='
                        + self.searchTerm
                        + '&ss=fn&sort=latest&type=story'
                        + '&min_date=' + str(self.dateStart.date()) + '&max_date=' + str(self.dateEnd.date())
                        + '&start='
                        + str(index))

            soup = BeautifulSoup(browser.page_source)
            if not soup.find_all('div', class_="search-info"):
                stop = True
                continue

            for result in soup.find_all('div', class_="search-info"):
                if self.check_dates(result.find('span', class_='search-date').get_text()):
                    link = result.find('h3').find('a')
                    ltext = link.get('href')
                    section = self.get_section(ltext)

                    if section != 'v' and ltext not in links:
                        print(ltext)
                        links.append(ltext)

                else:
                    stop = True
                    break

            index += 10
            time.sleep(sleep_time)

        browser.close()
        self.links = links
        return links

    def get_section (self, href):
        href = href[22:]
        try:
            section = re.search('/.*?/', href).group(0)[1:-1]
            if (section == 'politics' or section == 'us' or section == 'opinion' or section == 'v'):
                return section
            else:
                return 'other'
        except:
            return 'error'


class PoliticoScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')

        links = []
        stop = False
        index = 1

        while not stop:
            page = requests.get('http://www.politico.com/search/' + str(index) + '?s=newest&q=' + self.searchTerm)
            soup = BeautifulSoup(page.content)

            for result in soup.find_all('article', class_='story-frag format-ml'):
                pub_date = result.find('p', class_='timestamp')
                if pub_date is None:
                    continue

                if self.check_dates(pub_date.get_text().split()[0]):
                    try:
                        link = result.find('h3').find('a')
                        ltext = link.get('href')
                        section = self.get_section(ltext)
                    except:
                        continue

                    if (section == 'story' or section == 'blogs') and ltext not in links:
                        print(ltext)
                        links.append(ltext)

                else:
                    stop = True
                    break

            index += 1
            time.sleep(sleep_time)

        # browser.close()
        self.links = links
        return links

    def get_section (self, href):
        href = href[23:]
        try:
            return re.search('/.*?/', href).group(0)[1:-1]
        except:
            return 'error'


class WeeklyStandardScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')

        browser = webdriver.Chrome()

        links = []
        stop = False

        browser.get('http://www.weeklystandard.com/search?query=' + self.searchTerm)

        while not stop:
            soup = BeautifulSoup(browser.page_source)

            for result in soup.find_all('div', class_="data-item"):
                if self.check_dates(result.find('div', class_='item-pubdate').get_text()):
                    link = result.find('div', class_="item-headline").find('a')
                    ltext = link.get('href')

                    if ltext not in links:
                        print(ltext)
                        links.append(ltext)

                else:
                    stop = True
                    break

            try:
                element = browser.find_element_by_xpath('//*[@id="resultdata"]/div[22]/a')
                ActionChains(browser).move_to_element(element) \
                    .click(element) \
                    .perform()
                element = WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.ID, "resultdata")))

            except:
                stop = True

            time.sleep(sleep_time)

        browser.close()
        self.links = links
        return links


class BloombergScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')

        profile = webdriver.FirefoxProfile()
        browser = webdriver.Firefox(profile)

        links = []
        stop = False
        index = 1
        days = (self.dateEnd.date() - self.dateStart.date()).days + 1

        while not stop:
            browser.get('https://www.bloomberg.com/search?query='
                        + self.searchTerm
                        + '&startTime=-' + str(days) + 'd'
                        + '&sort=time:desc'
                        + '&endTime=' + str(self.dateEnd.date()) + 'T23:59:59.999Z'
                        + '&page=' + str(index))

            soup = BeautifulSoup(browser.page_source)

            if soup.find('div', class_="search-result-story__container") is None:
                stop = True
                continue

            for result in soup.find_all('div', class_="search-result-story__container"):
                if self.check_dates(result.find('span', class_='metadata-timestamp').get_text()):
                    link = result.find('h1', class_="search-result-story__headline")
                    ltext = link.find('a').get('href')
                    section = self.get_section(ltext)

                    if section == 'articles' and ltext not in links:
                        print(ltext)
                        links.append(ltext)

            index += 1
            time.sleep(sleep_time)

        browser.close()
        self.links = links
        return links

    def get_section (self, href):
        href = href[25:]
        try:
            return re.search('/.*?/', href).group(0)[1:-1]
        except:
            return 'error'


class TimeScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3,num_of_pages = 25):
        print('running get_pages().TimeScraper..')

        profile = webdriver.FirefoxProfile()
        browser = webdriver.Firefox(profile)

        links = []
        sub_links = []
        stop = False
        index = 1



        while not stop:
            browser.get('https://time.com/search/?q='
                + self.searchTerm
                + "&page="
                + str(index)
             )

            try:
                soup = BeautifulSoup(browser.page_source,'html.parser')
                print("Working on ",browser.current_url , "index:",index)
            except Exception as e:
                print("[ERROR]:Working on ",browser.current_url , "index:",index)
                print(e)
                stop = True
            if not soup.find('div', class_='search-results-content'):
                print("Error 304")
                stop = True


            data = soup.findAll('div', attrs={'class': 'media-body'})
            for div in data:
                links = div.findAll('a')
                for a in links:
                    print("link:",a['href'])
                    if("https://time.com" in a['href']):
                        print("Adding ", a['href'])
                        sub_links.append(a['href'])

            index += 1
            if index > num_of_pages + 1:
                stop = True
            time.sleep(sleep_time)

        browser.close()
        self.links = sub_links
        return links
    # def get_pages (self, sleep_time=3):
    #     print('running get_pages()...')
    #
    #     profile = webdriver.FirefoxProfile()
    #     browser = webdriver.Firefox(profile)
    #
    #     links = []
    #     stop = False
    #     index = 1
    #
    #     while not stop:
    #         browser.get('http://search.time.com/?q=' + self.searchTerm + '&startIndex=' + str(index) + '&sort=Date')
    #         soup = BeautifulSoup(browser.page_source)
    #
    #         for result in soup.find_all('div', class_="content-right"):
    #             pub_date = result.find('div', class_='content-snippet').get_text().split('...')[0].strip()
    #             if 'hour' in pub_date:
    #                 pub_date = str((datetime.now(timezone('EST')) - timedelta(hours=int(pub_date[0]))).date())
    #             elif 'day' in pub_date:
    #                 pub_date = str((datetime.today() - timedelta(days=int(pub_date[0]))).date())
    #
    #             if self.check_dates(pub_date):
    #                 link = result.find('div', class_="content-title")
    #                 ltext = link.find('a').get('href')
    #
    #                 if ltext not in links:
    #                     print(ltext)
    #                     links.append(ltext)
    #
    #             else:
    #                 stop = True
    #                 break
    #
    #         error_message = soup.find('div', class_="search-results-message")
    #         if error_message:
    #             if error_message.get_text() == 'Error getting Search Results':
    #                 stop = True
    #
    #         index += 10
    #         time.sleep(sleep_time)
    #
    #     browser.close()
    #     self.links = links
    #     return links


class CNNScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')

        browser = webdriver.Chrome()

        links = []
        index = 0

        browser.get('http://www.cnn.com/search/?text=' + self.searchTerm)
        soup = BeautifulSoup(browser.page_source)
        search_results = int(soup.find('div', class_='cn cn--idx-0 search-results_msg').get_text().split()[4])

        while index < search_results:
            soup = BeautifulSoup(browser.page_source)

            for result in soup.find_all('article',
                                        class_="cd cd--card cd--idx-0 cd--large cd--horizontal cd--has-media"):
                pub_date = result.find('span', class_='cd__timestamp').get_text()
                if not pub_date:
                    continue
                if ':' in pub_date:
                    pub_date = pub_date.split(',')
                    pub_date = (pub_date[1] + ',' + pub_date[2]).strip()

                if self.check_dates(pub_date):
                    link = result.find('h3', class_="cd__headline").find('a')
                    ltext = link.get('href')

                    if 'http://' not in ltext:
                        ltext = 'http://www.cnn.com' + ltext

                    if ltext not in links:
                        print(ltext)
                        links.append(ltext)

            index += 10
            time.sleep(sleep_time)

            try:
                element = browser.find_element_by_xpath('//*[@id="cnnSearchPagination"]/div/div[3]/a/span[1]')
                ActionChains(browser).move_to_element(element) \
                    .click(element) \
                    .perform()
                element = WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.ID, "textResultsContainer")))

            except:
                continue

        browser.close()
        self.links = links
        return links


class CNBCScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')

        links = []
        stop = False
        index = 1
        days = (self.dateEnd.date() - self.dateStart.date()).days + 1

        while not stop:
            page = requests.get('http://search.cnbc.com/rs/search/view.html?partnerId=2000'
                                + '&keywords=' + self.searchTerm
                                + '&sort=date&type=news&source=CNBC.com'
                                + '&pubtime=' + str(days) + '&pubfreq=d'
                                + '&page=' + str(index))
            soup = BeautifulSoup(page.content)

            if soup.find('div', class_="SearchResultCard") is None:
                stop = True
                continue

            for result in soup.find_all('div', class_="SearchResultCard"):
                seconds_since_epoch = float(re.findall(r'\d+', result.find('time').get_text())[0])
                pub_date = str(datetime.fromtimestamp(seconds_since_epoch / 1000).replace(hour=0, minute=0, second=0,
                                                                                          microsecond=0))

                if self.check_dates(pub_date):
                    link = result.find('h3', class_="title")
                    ltext = link.find('a').get('href')
                    if ltext not in links:
                        print(ltext)
                        links.append(ltext)

            index += 1
            time.sleep(sleep_time)

        self.links = links
        return links


class USATodayScraper(NewspaperScraper):
    def get_pages (self, sleep_time=5):
        print('running get_pages()...')

        browser = webdriver.Chrome()
        browser.get('http://www.usatoday.com/search/' + self.searchTerm + '/')

        links = []
        stop = False
        index = 1

        element = browser.find_element_by_xpath('/html/body/div[2]/div[1]/div/div[3]/span[2]')
        ActionChains(browser).move_to_element(element) \
            .click(element) \
            .perform()

        lastHeight = browser.execute_script("return document.body.scrollHeight")
        tries = 0

        while not stop:
            soup = BeautifulSoup(browser.page_source)
            # print soup.find_all('li', class_=' search-result-item')
            last_search_item = soup.find_all('li', class_=' search-result-item')[-1]
            link = last_search_item.find('a', class_='search-result-item-link').get('href')
            date_match = re.search('([0-9]{4}/[0-9]{2}/[0-9]{2})', link)
            if date_match is not None:
                print(date_match.group(1))

            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(sleep_time)

            newHeight = browser.execute_script("return document.body.scrollHeight")
            if (newHeight == lastHeight):
                tries += 1
                time.sleep(5)
                if tries >= 5:
                    stop = True
            else:
                tries = 0

            lastHeight = newHeight

        soup = BeautifulSoup(browser.page_source)

        for result in soup.find_all('li', class_=' search-result-item'):
            link = result.find('a', class_='search-result-item-link').get('href')
            date_match = re.search('([0-9]{4}/[0-9]{2}/[0-9]{2})', link)

            if date_match is not None:
                if self.check_dates(date_match.group(1)):
                    ltext = 'http://www.usatoday.com/' + link

                    if ltext not in links:
                        print(ltext)
                        links.append(ltext)
                else:
                    continue

            index += 1

        browser.close()
        self.links = links
        return links


class WSJScraper(NewspaperScraperWithAuthentication):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')

        links = []
        stop = False
        index = 1

        while not stop:
            page = requests.get('http://www.wsj.com/search/term.html?KEYWORDS='
                                + self.searchTerm
                                + '&min-date=' + str(self.dateStart.date()).replace('-', '/')
                                + '&max-date=' + str(self.dateEnd.date()).replace('-', '/')
                                + '&page=' + str(index)
                                + '&isAdvanced=true&daysback=4y&andor=AND&sort=date-desc&source=wsjarticle,wsjblogs,sitesearch')
            soup = BeautifulSoup(page.content)

            if soup.find('div', class_="headline-item") is None:
                stop = True
                continue

            for result in soup.find_all('div', class_="headline-item"):
                pub_date = result.find('time', class_='date-stamp-container').get_text()
                if 'min' in pub_date:
                    pub_date = str((datetime.now(timezone('EST')) - timedelta(minutes=int(pub_date[0]))).date())
                elif 'hour' in pub_date:
                    pub_date = str((datetime.now(timezone('EST')) - timedelta(hours=int(pub_date[0]))).date())
                else:
                    pub_date = pub_date.split()
                    pub_date = pub_date[0] + ' ' + pub_date[1] + ' ' + pub_date[2]

                if self.check_dates(pub_date):
                    link = result.find('h3', class_="headline")
                    ltext = link.find('a').get('href')
                    if 'http://' not in ltext:
                        ltext = 'http://www.wsj.com' + ltext

                    if ltext not in links and 'video' not in ltext:
                        print(ltext)
                        links.append(ltext)

            index += 1
            time.sleep(sleep_time)

        self.links = links
        return links


class NYTScraper(NewspaperScraperWithAuthentication):
    def get_pages (self, sleep_time=5):
        print('running get_pages()...')

        profile = webdriver.FirefoxProfile()
        browser = webdriver.Firefox(profile)

        links = []
        stop = False
        index = 1
        current_start = (self.dateEnd - timedelta(days=6)).date()
        current_end = self.dateEnd.date()

        while not stop:
            while True:
                browser.get('http://query.nytimes.com/search/sitesearch/?action=click&contentCollection'
                            + '&region=TopBar&WT.nav=searchWidget&module=SearchSubmit&pgtype=Homepage#/'
                            + self.searchTerm
                            + '/from' + str(current_start).replace('-', '') + 'to' + str(current_end).replace('-', '')
                            + '/allresults/'
                            + str(index)
                            + '/allauthors/newest/')

                time.sleep(sleep_time)
                soup = BeautifulSoup(browser.page_source)

                for result in soup.find_all('li', class_="story"):
                    pub_div = result.find('span', class_='dateline')
                    if pub_div is None:
                        continue

                    if self.check_dates(pub_div.get_text()):
                        link = result.find('div', class_='element2')
                        ltext = link.find('a').get('href')
                        section = self.get_section(ltext)

                        if section != 'video' and ltext not in links:
                            # print ltext
                            print(pub_div.get_text())
                            links.append(ltext)

                    else:
                        stop = True
                        break

                next_page = soup.find('a', class_="stepToPage next")
                if not next_page and index == 1:
                    continue
                elif not next_page or stop is True:
                    break

                index += 1

            current_start = current_start - timedelta(days=7)
            current_end = current_end - timedelta(days=7)
            index = 1

        browser.close()
        self.links = links
        return links

    def get_section (self, href):
        href = href[22:]
        try:
            return re.search('/.*?/', href).group(0)[1:-1]
        except:
            return 'error'''
