
import requests
from bs4 import BeautifulSoup
import re
from nltk.stem import PorterStemmer
from urllib.parse import urljoin,urlparse
from requests.exceptions import ConnectionError, HTTPError, Timeout
from urllib3.exceptions import NewConnectionError, MaxRetryError

'''
sometimes websites display their images after page uploaded (then we should fix the link of this images)
'''
def update_image_sources(soup,base_url):
    img_attributes = ['data-src','data-srcset', 'data-original', 'data-lazy-src', 'src'] #here we trying to get all posible of attributes for img tag
    for img in soup.find_all("img"):
        for attribute in img_attributes:
            if attribute in img.attrs:
                # check if any of the attributes is from img_attributes if yes then we save his path in src attribute 
                img['src'] = img[attribute]
                del img['loading']
                break  # if we find attribute then no need to search other attributes in img_attributes
        #some times the img is also relative and not absolute then we convert to absolute 
        relative_url = img.get('src')
        absolute_url = urljoin(base_url, relative_url)
        img['src'] = absolute_url
    return soup

'''
this method used for change the relative path to absolute path.
some news website make the links realtive and when requests fetch it, it come relative 
then we convert it to absolute to display it in the page in our website 
'''
def change_css_js_href_to_absoulute(soup,base_url):
    for link_tag in soup.find_all('link'):
        relative_url = link_tag.get('href')
        absolute_url = urljoin(base_url, relative_url)
        link_tag['href'] = absolute_url

    #convert realtive paths of scripts to absolute 
    for script_tag in soup.find_all('script',src=True):
        relative_url = link_tag.get('src')
        absolute_url = urljoin(base_url, relative_url)
        script_tag['src'] = absolute_url
    return soup

'''
this method delete articles in this way (it start check the parent tag of a_tag of the article and check if it have more a_tags if yes check there href if they for another articles means we go out from article bounds )
'''
def herarchial_delete_of_article_bounds(soup,links_to_delete):
    if not links_to_delete: #in case the set is empty then no need for delete articles 
        return soup
    for link_to_delete in links_to_delete:
        a_tags_article = soup.find_all('a',href=link_to_delete)
        try:
            for a_tag_article in a_tags_article:
                current_article_a_tag = a_tag_article
                while current_article_a_tag.parent:  #while the parent didn't have href of another articles and exist 
                    parent = current_article_a_tag.parent
                    parent_a_tags = parent.find_all('a',href=True)
                    isDelete = any(l.get('href') and l.get('href') not in links_to_delete for l in parent_a_tags) #here we checked if the parent have a href of pages(articles or other things) that not need to delete then we delete the current tag
                    if isDelete:
                        current_article_a_tag.decompose() #if we get here this meaning that the parent have another articles or pages
                        break
                    else:
                        current_article_a_tag = parent #meaning that the parent of current tag isn't include another a_tags with href then not need to delete meaning we still in the bounds of the article
        except AttributeError:
            continue
    return soup

'''
this method manipulate/edit the page we want to display for the user
it do two things :
1: delete the unwanted articles
2: change the HREF of the survival articles to "/displayFilteredArticle/XX", instead of xxx there will be the link of the article 
'''
def manipulate_toDisplay_htmlPage(soup,links_to_delete,absolute_Links,url):
    if soup is None or links_to_delete is None:
        return None
    soup_without_undesiredArticles = herarchial_delete_of_article_bounds(soup,links_to_delete)
    url_for_displayFilteredArticle = "/displayFilteredArticle/XXX"
    a_tags = soup_without_undesiredArticles.find_all('a')
    for a_tag in a_tags:
        try:
            if a_tag.has_attr('href'):
                editLink = a_tag['href']
                if editLink in absolute_Links: 
                    editLink = absolute_Links[editLink] #get the absolute link
                    editLink=editLink.replace("/","*") #flask think the / of article links is route in our sever then we change it 
                    a_tag['href'] = url_for_displayFilteredArticle.replace("XXX",editLink) #replace XX with link of article
        except AttributeError as e:
                print("Error with tag:")
    edited_soup = update_image_sources(soup_without_undesiredArticles,url) #fix images if they not display 
    edited_soup = change_css_js_href_to_absoulute(edited_soup,url) #if css (link tag) or js(script tag) there links is realtive then we convert to absolute 
    if edited_soup:
        return edited_soup
    return soup_without_undesiredArticles

"""
check if stemming word exist in the scraped text 
"""
def check_stemming_exist(stemmed_index,stemmed_word):
    for word in stemmed_word:
        if word in stemmed_index:
            return True
    return False

"""
remove stop words (because they not important for the meaning of the text)
"""
def remove_stop_words(index):
    stop_words = {'a', 'an', 'the', 'and', 'or', 'in', 'on', 'at'}
    for stop_word in stop_words:
        if stop_word in index:
            del index[stop_word]
    return index

"""
method to steaming the words entered by the user 
"""
def Stemming_entered_words(words):
    stem_list = []
    stemmer = PorterStemmer() #using porter stem 
    for word in words:
        stemmed_word = stemmer.stem(word) #do the stem 
        stem_list.append(stemmed_word)
    return stem_list

'''
this method delete the links in page before we scrape/crawl it.
in more details:
before we scarpe all the words in the article we delete the proposed and non relevant words (like proposed articles)
'''
def first_manipulate_htmlPage(soup):
    if soup:
        for a_tag in soup.find_all('a'):
            a_tag.extract()  # delete a tag 
    return soup


'''
this method convert the scraped text of article to stemming mode 
'''
def apply_stemming(index):
    stemmer = PorterStemmer()
    stemmed_index = {} #save the words in dictionary (search in dict done in O(1),this will optimize our search )
    for word, count in index.items():
        stemmed_word = stemmer.stem(word)
        if stemmed_word in stemmed_index:
            stemmed_index[stemmed_word] += count
        else:
            stemmed_index[stemmed_word] = count
    return stemmed_index


'''
this method extract all the words in the page by using regular expressions 
soup:include the html code of page
'''
def index_words(soup):
    index = {}
    try:
        words = re.findall(r'\w+', soup.get_text())
        for word in words:
            word = word.lower()
            if word in index:
                index[word] += 1
            else:
                index[word] = 1
        return index
    except AttributeError as e:
        print('error as e')
        return {}

'''
this method check the url if it relevant or not (relevant mean we should scrape/crawl it)
the method also convert relative link of page to absolute (requests need absolute link to request the data)
'''
def checkURL(url, mainURL):
    used_protocols = ['https', 'http'] #we just allowed this two protocols and denied protocols like MAILTO: , WHATSUP: , TEL: etc...
    ##### some links we crawled are pictures or videos or pdf... and this things take so much time to crawled and also its not pages then we 
    ##### remove this type of links and not crawling it. we want to crawling and extracting HTML PAGES
    unwanted_ends = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.xls', '.csv', '.zip', '.mp3', '.mp4', '.avi']
    parsed_url = urlparse(url) #extract details about the url (like domain name, protocol used etc...)
    if parsed_url.scheme == '':# if url is relative (urlparse above help us to know that because relative their scheme is '')
        full_url = urljoin(mainURL, url) #convert for absolute path 
        parsed_url = urlparse(full_url)  # Reparse the newly formed URL
    else: #if its absolute then no need for convert 
        full_url = url
    # Check if the protocol is from the allowed types and the domain matches the main domain (same domain mean link related to the newswebsite we want to crawling)
    if parsed_url.scheme in used_protocols and parsed_url.netloc == urlparse(mainURL).netloc:
        path_part = parsed_url.path.split('?')[0]  # Get the part of the path before any query string
        if not path_part.endswith(tuple(unwanted_ends)):
            return full_url
    return None #if get there then links isn't have all the conditions then we return None(mean we will not crawling it)

'''
this method crawling/scraping all the links from a page
it also remove all non relevant links by the method checkURL and return just relevant links for us and unique witch mean link not exist more than one time 
'''
def get_links_inPage(soup,url,Set_checkLinks):
    links_abosluteLinks = {} #search in dict done in O(1) becasue of that we use it 
    absolute_Links = {}
    SetLinks = set() #set to save relevant links just one time and not more 
    try:
        a_tags = soup.find_all('a')
        for a_tag in a_tags:
            if a_tag.get('href') and a_tag.get_text(strip=True):   #check if a_tag include href ATTRIBUTE and TEXT
                link = a_tag['href']
                res = checkURL(link,url) #here we check if the link is relevant and in case its relative then we convert to absolute 
                if res and res not in Set_checkLinks and res not in SetLinks:
                    SetLinks.add(res)
                    links_abosluteLinks[res] = link
                    absolute_Links[link] = res
    except AttributeError as e: #in case any exception happen
        print('error as e')
    return SetLinks,links_abosluteLinks,absolute_Links

'''
this method fetch page by requests 
we use session to fetch page because session stay the connetion open with the server after fetch page(for new fetch)
and this help us to fetch pages fasting but sometimes news website does not accept to fetch with session 
then we use the requests.get (requests.get after each fetch it stop the connection)
'''
def fetch_page(url,session):
    print('trying to fetch:', url)
    try:
        response = session.get(url, timeout=30)  # add timeout (if the scrape not getten within 30 sec then stop and return)
        if response.status_code == 200: #200 is a status code mean the respone success 
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        else: #sometimes news website refuse session then we use requests.get instead 
            response = requests.get(url,timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup
            else:
                print('Failed to retrieve:', url, 'Status code:', response.status_code)
    except (ConnectionError, HTTPError, Timeout, NewConnectionError, MaxRetryError) as e:
        print('Failed to connect:', url, 'Error:', str(e))
    
    return None


def identify_and_classify_unwantedLinks(links_set,classify_links,newsWebsite_session,stem_entered_words,links_abosluteLinks):
    deleted_links = set()
    for link in links_set: #fetch all the links in the page and classify them for yes to delete/no not for delete 
        if link in classify_links: #before we fetch the page we check if it fetched before, if yes no need to fetch again because its already classified 
            if classify_links[link] =='yes':
                deleted_links.add(links_abosluteLinks[link])
            continue #stop this iteration if it fetched before 
        soup = fetch_page(link,newsWebsite_session) 
        edited_soup = first_manipulate_htmlPage(soup)
        index = index_words(edited_soup) #scrape/crawl the text and split it for words and save in dict 
        index_wo_stopWords = remove_stop_words(index)
        stemming_index = apply_stemming(index_wo_stopWords)
        isEnteredWordsExist = check_stemming_exist(stemming_index,stem_entered_words)
        if(isEnteredWordsExist): #check if entered words occur in the page 
            classify_links[link] = 'yes' #yes this article/page should deleted 
            deleted_links.add(links_abosluteLinks[link])
        else:
            classify_links[link] = 'no'
    return deleted_links,classify_links

'''
this method used to parse the data entered by the user (category he choose/words he entered)
'''
def get_data_entered(data_entered):
    entered_words = []
    if data_entered['type'] == "category": #if he choose category and not entered words
        for category,is_true in data_entered['data'].items():
            if is_true: #check witch categories user choose 
                if category=="politics":
                    entered_words.extend(politics)
                if category=="criminal":
                    entered_words.extend(criminal)
                if category=="sexual":
                    entered_words.extend(sexual)
        stem_entered_words = entered_words #no need for stemming convert because the words in categories is already stemmed
    else: #in case data_type is entered words 
        entered_words = data_entered['data']
        stem_entered_words = Stemming_entered_words(entered_words) #stem the entered words
    return stem_entered_words


'''
this method called by the flask server every time user click in a new article in the page 
its called all the methods below to make the filtering process 
'''
def articleCrawling(articleURL,data_entered,classify_links,newsWebsite_session):
    Set_checkLinks = {}
    stem_entered_words = get_data_entered(data_entered)
    parsed_url = urlparse(articleURL)
    url = f"{parsed_url.scheme}://{parsed_url.netloc}" #get the domain name and and build with concatenate with protocol (https or http)
    mysoup = fetch_page(articleURL,newsWebsite_session)
    if mysoup is None:  #check if fetch not success to get the html code of the page in url then return None 
        return None,classify_links
    links_set,links_abosluteLinks,absolute_Links = get_links_inPage(mysoup,url,Set_checkLinks)
    links_for_delete,classify_links = identify_and_classify_unwantedLinks(links_set,classify_links,newsWebsite_session,stem_entered_words,links_abosluteLinks)
    edited_html_page=manipulate_toDisplay_htmlPage(mysoup,links_for_delete,absolute_Links,url) #edit the page (delete unwanted content and change HREF of survival pages )
    print('deletedLinks:')
    print(links_for_delete)
    return edited_html_page,classify_links   

'''
this method called by the flask server when user request to filter the main page of the news website
its called all the methods below to make the filtering process 
'''
def newsWebsiteCrawling(newsWebsiteURL,data_entered,session):
    stem_entered_words = get_data_entered(data_entered)  #here we check type of data and get the words or categories we should filter based to them
    parsed_url = urlparse(newsWebsiteURL)
    url = f"{parsed_url.scheme}://{parsed_url.netloc}" #in case user not entered the url of the mainpage of the news website (then extract the domain name and concatenate with protocol)
    Set_checkLinks = {}
    classify_links = {}
    mysoup = fetch_page(url,session)
    if mysoup is None:  #check if fetch not success to get the html code of the page in url then return None 
        return None,classify_links
    links_set,links_abosluteLinks,absolute_Links = get_links_inPage(mysoup,url,Set_checkLinks) #get all the relevant links in the main page
    links_for_delete,classify_links = identify_and_classify_unwantedLinks(links_set,classify_links,session,stem_entered_words,links_abosluteLinks)
    edited_html_page=manipulate_toDisplay_htmlPage(mysoup,links_for_delete,absolute_Links,url)
    print('deletedLinks:')
    print(links_for_delete)
    return edited_html_page,classify_links #return the html code of the main page and also the links and their classify (used for fasting the filtering process of the articles)

#this words is the most popular words in each category and they are in there stemming mode 
# politics = ["government","politics","democracy","choice","parliament","parliament","President","congress","policy","legislation","political party","campaign","diplomacy","International Relations","Political System","constitution","Knesset","Legislation","Governance","Lobbying","Judiciary","Civil rights","Activism","Public policy","Political campaign","Foreign policy","Bureaucracy","Constitution","Sovereignty","Oligarchy","Tyranny","Anarchy"]
politics = ['govern', 'polit', 'democraci', 'choic', 'parliament', 'parliament', 'presid', 'congress', 'polici', 'legisl', 'political parti', 'campaign', 'diplomaci', 'international rel', 'political system', 'constitut', 'knesset', 'legisl', 'govern', 'lobbi', 'judiciari', 'civil right', 'activ', 'public polici', 'political campaign', 'foreign polici', 'bureaucraci', 'constitut', 'sovereignti', 'oligarchi', 'tyranni', 'anarchi']
# sexual = ["porn","pornography","sex","sexual","homosexual","sexuality","Erotica","Intimacy","LGBTQ","Consent","Fetish","Arousal","Contraception","Orientation","Transgender","Queer","Bisexuality","rape","libido","masturbate"]
sexual = ['porn', 'pornographi', 'sex', 'sexual', 'homosexu', 'erotica', 'intimaci', 'lgbtq', 'fetish', 'arous', 'contracept', 'orient', 'transgend', 'queer', 'bisexu', 'rape', 'libido', 'masturb']
# criminal = ["kill","crime","Theft","Robbery","Assault","Fraud","Arson","Burglary","Vandalism","Homicide","Manslaughter","Cybercrime","Terrorism","Extortion","Forgery","Kidnapping","Smuggling","Corruption","Embezzlement","Conspiracy",]
criminal = ['kill', 'crime', 'theft', 'robberi', 'assault', 'fraud', 'arson', 'burglari', 'vandal', 'homicid', 'manslaught', 'cybercrim', 'terror', 'extort', 'forgeri', 'kidnap', 'smuggl', 'corrupt', 'embezzl', 'conspiraci']
