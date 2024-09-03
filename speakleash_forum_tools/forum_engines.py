"""
Forum Engines Manager Module

This module contains the ForumEnginesManager class, which is designed to facilitate 
the crawling of different types of forum engines. It orchestrates the process 
of identifying and navigating through various forum structures to extract 
threads, topics, and handle pagination effectively. The ForumEnginesManager class 
dynamically selects an appropriate crawler based on the forum engine type 
(e.g., Invision, phpBB, IPBoard, XenForo) and configures it with specific CSS selectors 
and criteria to ensure accurate data extraction. 
This flexibility allows it to adapt to the unique characteristics of each forum engine.

Classes:
- ForumEnginesManager: Manages crawling processes across various forum engine types. 
    Utilizes specialized crawler classes for each forum type and manages thread and topic extraction, as well as pagination handling.

Key Functionalities:
- Dynamically selects and configures a specific crawler class based on the forum engine type.
- Extracts thread and topic URLs and titles from forum pages.
- Handles pagination to ensure complete data extraction from forum threads.
- Integrates with a ConfigManager class to obtain necessary configurations and settings.
- Utilizes urllib's robotparser to respect the forum's robots.txt rules, ensuring ethical crawling practices.

Usage:
The ForumEnginesManager class requires an instance of ConfigManager for initialization. 
It uses the settings from ConfigManager to determine the forum engine type and other essential parameters. 
After initialization, the crawl_forum method can be called to start the crawling process.

Dependencies:
- requests: For making HTTP requests to forums.
- BeautifulSoup: For parsing HTML and extracting data.
- urllib: For handling URLs and complying with robots.txt rules.
- pandas: For data manipulation and handling data structures.
- logging: For logging the crawling process.
- tqdm: For displaying progress in terminal during long-running operations.
- ConfigManager: Custom class providing necessary configuration settings.
"""
import re
import time
import logging
import requests
import urllib3
# import dataclasses
from urllib.parse import urljoin
from typing import Optional, Union, List

from bs4 import BeautifulSoup

from speakleash_forum_tools.config_manager import ConfigManager
from speakleash_forum_tools.utils import create_session

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)     # Supress warning about 'InsecureRequest' (session.get(..., verify = False))

#TODO: Re-write classes for specific forum engines to -> dataclasses -> ????

class ForumEnginesManager:
    """
    Manages the crawling process for various forum engine types. 
    It provides methods to extract threads and topics from forum pages and handle pagination.
    The class orchestrates the use of specific crawler classes tailored to each identified forum engine type, 
    ensuring that the crawling process is optimized for the nuances of each forum software.
    """
    def __init__(self, config_manager: ConfigManager):
        """
        Manages the crawling process for various forum engine types.

        :param config_manager (ConfigManager): Configuration class, containing settings with keys like 'FORUM_ENGINE', 'DATASET_URL', etc.
        .. note:: The `urllib.robotparser` is used to ensure compliance with the forum's scraping policies as declared in its 'robots.txt'.

        Important:
        - threads_class (List[str]): "<anchor_tag> >> <attribute_name> :: <attribute_value>", 
            e.g. ["a >> class :: forumtitle"] (for phpBB engine)
        - topics_class (List[str]): "<anchor_tag> >> <attribute_name> :: <attribute_value>", 
            e.g. ["a >> class :: topictitle"] (for phpBB engine)
        - threads_whitelist (List[str]): to validate URL with specific words, 
            e.g. ["forum"] (for Invision engine)
        - threads_blacklist (List[str]): but sometimes whitelist is not enough, 
            e.g. ["topic"] (no, it is not a typo) (for Invision engine)
        - topics_whitelist (List[str]): to validate URL with specific words, 
            e.g. ["topic"] (for Invision engine)
        - topics_blacklist (List[str]): but sometimes whitelist is not enough, 
            e.g. ["page", "#comments"] (for Invision engine)
        - pagination (List[str]): "<attribute_value>" (when attribute_name is 'class'), "<attribute_name> :: <attribute_value>" (if anchor_tag is ['li', 'a', 'div']) 
            or "<anchor_tag> >> <attribute_name> :: <attribute_value>", e.g. ["arrow next", "right-box right", "title :: Dalej"] (for phpBB engine)
        - topic_title_class (List[str]): Searched for first instance -> "<anchor_tag> >> <attribute_name> :: <attribute_value>"
            e.g. ["h2 >>  :: ", "h2 >> class :: topic-title"] (for phpBB engine)
        - content_class (List[str]): "<anchor_tag> >> <attribute_name> :: <attribute_value>", 
            e.g. ["content_class"] (for phpBB engine)
        """
        self.logger_tool = config_manager.logger_tool
        self.logger_print = config_manager.logger_print
        
        self.headers = config_manager.headers
        self.engine_type = config_manager.settings['FORUM_ENGINE']
        self.forum_url = config_manager.settings['DATASET_URL']
        self.dataset_name = config_manager.settings['DATASET_NAME']
        self.time_sleep = config_manager.settings['TIME_SLEEP']
        self.web_encoding = config_manager.settings['ENCODING']
        self.logger_tool.info(f"Forum Engines Manager -> Forum URL = {self.forum_url} | Engine Type = {self.engine_type} | Sleep Time = {self.time_sleep}")

        self.robot_parser = config_manager.robot_parser
        self.force_crawl = config_manager.force_crawl

        self.check_engine_content(config_manager)
        
        self.forum_threads = []
        self.threads_topics = {}


    ### Functions ###

    def check_engine_content(self, config_manager: ConfigManager):
        """
        Check Engine type and assign default values for threads/topic/content classes and whitelist/blacklist.

        :param config_manager(ConfigManager): ConfigManager class with settings.
        """
        self.logger_tool.info(f"Checking engine type: {self.engine_type}")
        self.logger_print.info(f"Checking engine type: {self.engine_type}")

        try:                                    # Forums: ['invision', 'phpbb', 'ipboard', 'xenforo', 'other']
            if self.engine_type == 'invision':
                engine_type = InvisionCrawler()
            elif self.engine_type == 'phpbb':
                engine_type = PhpBBCrawler()
            elif self.engine_type == 'ipboard':
                engine_type = IPBoardCrawler()
            elif self.engine_type == 'xenforo':
                engine_type = XenForoCrawler()
            elif self.engine_type == 'other':
                engine_type = UnsupportedCrawler()
            else:
                raise ValueError("Unsupported forum engine type - you can chose: ['invision', 'phpbb', 'ipboard', 'xenforo', 'other']")
        except Exception as e:
            self.logger_tool.error(f"Error while checking engine type: {e}")
            self.logger_print.info(f"Error while checking engine type: {e}")

        self.threads_class = engine_type.threads_class
        self.threads_whitelist = engine_type.threads_whitelist
        self.threads_blacklist = engine_type.threads_blacklist
        self.topics_class = engine_type.topics_class
        self.topics_whitelist = engine_type.topics_whitelist
        self.topics_blacklist = engine_type.topics_blacklist
        self.pagination = engine_type.pagination
        self.topic_title_class = engine_type.topic_title_class
        self.content_class = engine_type.content_class

        try:
            if config_manager.settings['THREADS_CLASS'] and isinstance(config_manager.settings['THREADS_CLASS'], list):
                self.threads_class.extend(config_manager.settings['THREADS_CLASS'])
                self.threads_class = list(dict.fromkeys(self.threads_class))
            if config_manager.settings['THREADS_WHITELIST'] and isinstance(config_manager.settings['THREADS_WHITELIST'], list):
                self.threads_whitelist.extend(config_manager.settings['THREADS_WHITELIST'])
                self.threads_whitelist = list(dict.fromkeys(self.threads_whitelist))
            if config_manager.settings['THREADS_BLACKLIST'] and isinstance(config_manager.settings['THREADS_BLACKLIST'], list):
                self.threads_blacklist.extend(config_manager.settings['THREADS_BLACKLIST'])
                self.threads_blacklist = list(dict.fromkeys(self.threads_blacklist))
            if config_manager.settings['TOPICS_CLASS'] and isinstance(config_manager.settings['TOPICS_CLASS'], list):
                self.topics_class.extend(config_manager.settings['TOPICS_CLASS'])
                self.topics_class = list(dict.fromkeys(self.topics_class))
            if config_manager.settings['TOPICS_WHITELIST'] and isinstance(config_manager.settings['TOPICS_WHITELIST'], list):
                self.topics_whitelist.extend(config_manager.settings['TOPICS_WHITELIST'])
                self.topics_whitelist = list(dict.fromkeys(self.topics_whitelist))
            if config_manager.settings['TOPICS_BLACKLIST'] and isinstance(config_manager.settings['TOPICS_BLACKLIST'], list):
                self.topics_blacklist.extend(config_manager.settings['TOPICS_BLACKLIST'])
                self.topics_blacklist = list(dict.fromkeys(self.topics_blacklist))
            if config_manager.settings['PAGINATION'] and isinstance(config_manager.settings['PAGINATION'], list):
                self.pagination.extend(config_manager.settings['PAGINATION'])
                self.pagination = list(dict.fromkeys(self.pagination))
            if config_manager.settings['CONTENT_CLASS'] and isinstance(config_manager.settings['CONTENT_CLASS'], list):
                self.content_class.extend(config_manager.settings['CONTENT_CLASS'])
                self.content_class = list(dict.fromkeys(self.content_class))
            self.logger_tool.debug("Checked all additional lists of threads/topics/whitelist/blacklist to search...")
        except Exception as e:
            self.logger_tool.error(f"ForumEnginesManager: Error while extending lists of threads/topics/whitelist/blacklist to search! Error: {e}")


    def crawl_forum(self) -> bool:
        """
        Initiates the crawling process over the configured forum URL. It leverages the specified forum engine crawler
        to navigate through threads and topics, adhering to the rules specified in `robots.txt`.

        :return: A boolean indicating the success or failure of the crawling process.
        """
        self.logger_tool.info(f"Starting crawler on: {self.forum_url}")
        self.logger_print.info((f"Starting crawler on: {self.forum_url}"))

        try:
            # Fetch the main page of the forum and extract thread links
            session = create_session()
            self.forum_threads.append(self._get_forum_threads(self.forum_url, session = session))
            
            # Iterate over each thread and extract topics
            for x in self.forum_threads:
                for thread_url, thread_name in x.items():
                    self.logger_tool.info(f"Crawling thread: || {thread_name} || at {thread_url}")
                    self.logger_print.info(f"Crawling thread: || {thread_name} || at {thread_url}")
                    topics = self._get_thread_topics(thread_url, session = session)
                    self.threads_topics.update(topics)
                    self.logger_tool.info(f"-> All Topics found: {len(self.threads_topics)}")
                    self.logger_print.info(f"-> All Topics found: {len(self.threads_topics)}")
                    time.sleep(self.time_sleep)

            self.forum_threads = {key: value for d in self.forum_threads for key, value in d.items()}

            self.logger_tool.info(f"Crawler (manually) found: Threads = {len(self.forum_threads)}")
            self.logger_tool.info(f"Crawler (manually) found: Topics = {len(self.threads_topics)}")
            self.logger_print.info(f"Crawler (manually) found: Threads = {len(self.forum_threads)}")
            self.logger_print.info(f"Crawler (manually) found: Topics = {len(self.threads_topics)}")

            if len(self.threads_topics) == 0:
                return False

            return True
        except Exception as e:
            self.logger_tool.error("ERROR --- ERROR --- ERROR --- ERROR --- ERROR")
            self.logger_tool.error(f"Can't crawl topics -> {e}")
            self.logger_tool.error("ERROR --- ERROR --- ERROR --- ERROR --- ERROR")
            return False

    def _get_forum_threads(self, url_now: str, session: requests.Session) -> dict:
        """
        Retrieves all the threads listed on a given forum page by utilizing the CSS selectors specified for the forum engine.

        :param url_now (str): The URL of the forum page from which to extract the threads.
        :param session (requests.Session): Session with http/https adapters.

        :return: A dictionary mapping thread URLs to their respective thread titles.
        """
        forum_threads = {}
        try:
            if self.forum_url in url_now:
                response = session.get(url_now, timeout=60, headers=self.headers)
            else:
                return forum_threads
        except Exception as e:
            # self.logger_tool(f"Error while getting WEBSITE: {e}")
            return forum_threads
        web_encoding = self.web_encoding if self.web_encoding else response.encoding
        soup = BeautifulSoup(response.content, "html.parser", from_encoding=web_encoding)

        forum_threads = self._get_forum_threads_extract(soup)
        page_num = 1
        self.logger_tool.info(f"* Forum searched for Threads/Forums ({page_num}): {url_now}")
        self.logger_print.info(f"* Forum searched for Threads/Forums ({page_num}): {url_now}")

        # Find the link to the next page
        while self._get_next_page_link(url_now, soup, self.pagination, engine_type=self.engine_type, logger_tool=self.logger_tool):
            next_page_link = self._get_next_page_link(url_now, soup, self.pagination, engine_type=self.engine_type, logger_tool=self.logger_tool, push_log=False)
            url_now = urljoin(self.forum_url, next_page_link) if next_page_link else False
            
            if url_now and self.forum_url in url_now:
                page_num += 1
                self.logger_tool.info(f"*** Found new page with threads... URL: {url_now}")
                try:
                    if self.forum_url in url_now:
                        response = session.get(url_now, timeout=60, headers=self.headers)
                    else:
                        return forum_threads
                except Exception as e:
                    # self.logger_tool(f"Error while getting WEBSITE: {e}")
                    return forum_threads
                web_encoding = self.web_encoding if self.web_encoding else response.encoding
                soup = BeautifulSoup(response.content, "html.parser", from_encoding=web_encoding)

                forum_threads.update(self._get_thread_topics_extract(soup = soup))
                self.logger_tool.info(f"--> Threads found in forum ({page_num}): {len(forum_threads)}")
                self.logger_print.info(f"--> Threads found in forum ({page_num}): {len(forum_threads)}")
            else:
                break

        return forum_threads

    def _get_forum_threads_extract(self, soup: BeautifulSoup) -> dict:
        """
        Extracts valid threads from the forum page.

        :param soup (BeautifulSoup): BeautifulSoup object with currently searched URL.

        :return: Dict with threads (forums) found on website.
        """
        forum_threads = {}

        for thread_class in self.threads_class:
            html_tag, th_type_class = thread_class.split(" >> ")
            th_type, th_class = th_type_class.split(" :: ")
            threads = soup.find_all(html_tag, {th_type: th_class})

            threads_found = self._crawler_search_filter(to_find = "THREAD", to_search = threads, whitelist = self.threads_whitelist,
                                                  blacklist = self.threads_blacklist, robotparser = self.robot_parser, 
                                                  forum_url = self.forum_url, force_crawl = self.force_crawl, logger_tool=self.logger_tool)
            forum_threads.update(threads_found)
            time.sleep(self.time_sleep)
        self.logger_tool.info(f"-> Found threads: {len(forum_threads)}")
        self.logger_print.info(f"-> Found threads: {len(forum_threads)}")
        return forum_threads


    def _get_thread_topics(self, url_now: str, session: requests.Session) -> dict:
        """
        Retrieves all the topics listed on a given thread (forum) page by utilizing the CSS selectors specified for the forum engine.

        :param url_now (str): The URL of the thread (forum) page from which to extract the topics.
        :param session (requests.Session): Session with http/https adapters.

        :return: A dictionary mapping topic URLs to their respective topic titles.
        """
        thread_topics = {}
        page_num = 1
        
        try:
            if self.forum_url in url_now:
                response = session.get(url_now, timeout=60, headers=self.headers)
            else:
                return thread_topics
        except Exception as e:
            # self.logger_tool(f"Error while getting WEBSITE: {e}")
            return thread_topics
        web_encoding = self.web_encoding if self.web_encoding else response.encoding
        soup = BeautifulSoup(response.content, "html.parser", from_encoding=web_encoding)
        
        thread_topics = self._get_thread_topics_extract(soup = soup)
        self.logger_tool.info(f"--> Topics found in thread ({page_num}): {len(thread_topics)}")
        self.logger_print.info(f"--> Topics found in thread ({page_num}): {len(thread_topics)}")

        # Find the link to the next page
        while self._get_next_page_link(url_now, soup, self.pagination, engine_type=self.engine_type, logger_tool=self.logger_tool):
            next_page_link = self._get_next_page_link(url_now, soup, self.pagination, engine_type=self.engine_type, logger_tool=self.logger_tool, push_log=False)
            url_now = urljoin(self.forum_url, next_page_link) if next_page_link else False
            
            if url_now and self.forum_url in url_now:
                page_num += 1
                self.logger_tool.info(f"* Found new page with topics ({page_num})... URL: {url_now}")
                try:
                    if self.forum_url in url_now:
                        response = session.get(url_now, timeout=60, headers=self.headers)
                    else:
                        return thread_topics
                except Exception as e:
                    # self.logger_tool(f"Error while getting WEBSITE: {e}")
                    return thread_topics
                web_encoding = self.web_encoding if self.web_encoding else response.encoding
                soup = BeautifulSoup(response.content, "html.parser", from_encoding=web_encoding)

                thread_topics.update(self._get_thread_topics_extract(soup = soup))
                self.logger_tool.info(f"--> Topics found in thread ({page_num}): {len(thread_topics)}")
                self.logger_print.info(f"--> Topics found in thread ({page_num}): {len(thread_topics)}")
            else:
                break
        
        return thread_topics


    def _get_thread_topics_extract(self, soup: BeautifulSoup) -> dict:
        """
        Extracts valid topics from the forum page.

        :param soup (BeautifulSoup): BeautifulSoup object with currently searched URL.

        :return: Dict with topics found in thread (forum)
        """
        thread_topics = {}

        for topic_class in self.topics_class:
            # topics = soup.select(topic_class)
            html_tag, tp_type_class = topic_class.split(" >> ")
            tp_type, tp_class = tp_type_class.split(" :: ")
            topics = soup.find_all(html_tag, {tp_type: tp_class})
            self.logger_tool.debug(f"Found URLs = {len(topics)}")

            if len(topics) == 0:
                forum_threads = self._get_forum_threads_extract(soup=soup)
                self.forum_threads.append(forum_threads)
                self.logger_tool.info(f"Added new threads (while searching for topics) = {len(forum_threads)}")
                self.logger_print.info(f"Added new threads (while searching for topics) = {len(forum_threads)}")
                continue
            
            topics_found = self._crawler_search_filter(to_find = "TOPIC", to_search = topics, whitelist = self.topics_whitelist,
                                                 blacklist = self.topics_blacklist, robotparser = self.robot_parser, 
                                                 forum_url = self.forum_url, force_crawl = self.force_crawl, logger_tool=self.logger_tool)
            thread_topics.update(topics_found)
        
        time.sleep(self.time_sleep)
        self.logger_tool.debug(f"Found topics: {len(thread_topics)}")
        return thread_topics

    @staticmethod
    def _get_next_page_link(url_now: str, soup: BeautifulSoup, pagination: list[str], engine_type: str, logger_tool: logging.Logger, push_log: bool = True) -> Union[str, bool]:
        """
        Finds the link to the next page using pagination.
        Default HTML tags to search = ['li', 'a', 'div']

        :param url_now (str): URL of website which crawler is now checking.
        :param soup (BeautifulSoup): BeautifulSoup object with currently searched URL.

        :return: Returns string with link to next page or False if did not find any.
        """
        for pagination_class in pagination:
            next_button = []
            html_tag = ['li', 'a', 'div']
            next_page = ""
            
            try:
                if (pagination_class.find(" >> ") < 0) and (pagination_class.find(" :: ") < 0):
                    next_button = soup.find_all(html_tag, {'class': {pagination_class}})
                    if next_button:
                        if engine_type == 'phpbb' and "pagination-arrow" in pagination:
                            flag_found = False
                            for x in next_button:
                                if x.find('i', {'class':'fa fa-arrow-right'}):
                                    next_button = x
                                    flag_found = True
                                    logger_tool.debug("Found PHPBB weird pagination")
                                    break
                            if not flag_found:
                                next_button = ''
                        else:
                            next_button = next_button[0]

                if not next_button and (pagination_class.find(" >> ") < 0) and (pagination_class.find(" :: ") > 0):
                    pag_type, pag_class = pagination_class.split(" :: ")
                    next_button = soup.find_all(html_tag, {pag_type:pag_class})
                    if next_button:
                        next_button = next_button[0]

                if not next_button and (pagination_class.find(" >> ") > 0) and (pagination_class.find(" :: ") > 0):
                    html_tag, pag_type_class = pagination_class.split(" >> ")
                    pag_type, pag_class = pag_type_class.split(" :: ")
                    next_button = soup.find_all(html_tag, {pag_type:pag_class})
                    if next_button:
                        next_button = next_button[0]

            except Exception as e:
                logger_tool.error(f"NEXT PAGE // ERROR: Error while searching for pagination -> {e}")
                logger_tool.debug("NEXT PAGE // NOT FOUND - Button to next page - NOT FOUND")
                continue
            
            if next_button:
                # logger_tool.debug(f"NEXT PAGE // Found button! ({len(next_button)}) | Button: {True if next_button else False}") 
                try:
                    next_page = next_button['href']
                except:
                    next_page = next_button.find('a')['href']
                
                if next_page == url_now:
                    continue
                
                if push_log:
                    logger_tool.debug(f"NEXT PAGE // Found next page with topics -> {next_page}")
                
                if next_page:
                    return next_page
        
        # Search for URLs - no buttons or HTML tags for them
        if engine_type == 'phpbb':
            try:
                # Preapre URL without 'sid=' and 'start='
                forum_num = 0
                topic_num = 0
                startnum_num = 0

                # Save url_now => forum number / topic number / start shift
                url_wo_ = url_now.replace("&amp;","&").split("?")[1].split('&')
                for x in url_wo_:
                    if x.startswith("f="):
                        forum_num = int(x.replace("f=",""))
                    elif x.startswith("t="):
                        topic_num = int(x.replace("t=",""))
                    elif x.startswith("start="):
                        startnum_num = int(x.replace("start=",""))

                # Find valid topics
                page_no = dict()
                pages = soup.find_all('a')

                for page in pages:
                    link_page: str = page.get('href', '')
                    if link_page:
                        if '?' in link_page and 'start=' in link_page:
                            temp_startnum_num = 0 
                            temp_forum_num = 0
                            temp_topic_num = 0

                            link_page = link_page.replace("&amp;","&")
                            link_page_query = link_page.split("?")

                            if len(link_page_query) > 1:
                                if link_page_query[1]:
                                    temp_page = link_page_query[1].split('&')
                                    try:
                                        for x in temp_page:
                                            if x.startswith("f="):
                                                temp_forum_num = int(x.replace("f=",""))
                                            elif x.startswith("t="):
                                                temp_topic_num = int(x.replace("t=",""))
                                            elif x.startswith("start="):
                                                temp_startnum_num = int(x.replace("start=",""))
                                        if temp_startnum_num != 0 and temp_forum_num == forum_num and temp_topic_num == topic_num:
                                            page_no.update({link_page : temp_startnum_num})
                                    except Exception as e:
                                        logger_tool.error(f"Error while searching for valid next page: {e}")
        
                # Search for next page url
                for url_next, key_num in dict(sorted(page_no.items(), key=lambda item: item[1])).items():
                    if key_num > startnum_num:
                        if push_log:
                            # print(f"| NEXT PAGE // Found next page with topics -> {url_next}")
                            logger_tool.debug(f"NEXT PAGE // Found next page with topics -> {url_next}")
                        return url_next
            except Exception as e:
                logger_tool.error(f"Problem when searching manually for next page: {e}")

        logger_tool.debug("NEXT PAGE // Can't find more pages in this topic ---")
        return False
    
    @staticmethod
    def _crawler_search_filter(to_find: str, to_search, whitelist: List[str], blacklist: List[str],
                               robotparser, forum_url: str, force_crawl: bool, logger_tool: logging.Logger) -> dict:
        """
        Filtering found URLs and check them with robots.txt parser.

        :param to_find (str): Simple string for debug only (e.g. "THREADS" or "TOPICS").
        :param to_search (BeautifulSoup.find_all()): ResultSet from BeautifulSoup.find_all() function.
        :param whitelist (list[str]): Strings which have to be inside URL if we wanna make sure it is valid URL.
        :param blacklist (list[str]): Strings for blocking some URLs.
        :param robotparser (urllib.robotparser): Parser for 'robots.txt' - check if robots.txt doesn't block topics / threads URLs.
        :param forum_url (str): Forum main website URL - for checking if crawler will take only forum URLs.

        :return: Returns dict with valid URLs for Threads / Topics (checked with whitelist/blacklist/robots.txt)
        """
        to_return_dict = {}

        for tag_solo in to_search:
            try:
                try:
                    if tag_solo['href']:
                        a_tags = [tag_solo]
                except:
                    a_tags = tag_solo.find_all('a')

                for a_tag in a_tags:
                    # self.logger_tool.debug(f"{to_find} -> {a_tag['href']}")
                    if whitelist:
                        if any(y in a_tag['href'] for y in whitelist):
                            if blacklist:
                                if any(y in a_tag['href'] for y in blacklist):
                                    logger_tool.debug(f"{to_find} OUT <- {a_tag['href']}")
                                    continue
                            if robotparser.can_fetch("*", a_tag['href']) or force_crawl == True:
                                logger_tool.debug(f"{to_find} GOOD -> {a_tag['href']}")
                                url_return = urljoin(forum_url, a_tag['href'])
                                if forum_url not in url_return:
                                    url_return = forum_url + a_tag['href'][1:]
                                to_return_dict.update({url_return : a_tag.get_text(strip=True)})
                            else:
                                logger_tool.debug(f"{to_find} OUT <- {a_tag['href']}")
                            continue
                        else:
                            logger_tool.debug(f"{to_find} OUT <- {a_tag['href']}")
                            continue
                    if blacklist:
                        if any(y in a_tag['href'] for y in blacklist):
                            logger_tool.debug(f"{to_find} OUT <- {a_tag['href']}")
                            continue
                    
                    if not whitelist or not blacklist:
                        if robotparser.can_fetch("*", a_tag['href']) or force_crawl == True:
                            logger_tool.debug(f"{to_find} GOOD (+) -> {a_tag['href']}")
                            url_return = urljoin(forum_url, a_tag['href'])
                            if forum_url not in url_return:
                                url_return = forum_url + a_tag['href'][1:]
                            to_return_dict.update({url_return : a_tag.get_text(strip=True)})
                        else:
                            logger_tool.debug(f"{to_find} OUT (+) <- {a_tag['href']}")
            except Exception as e:
                logger_tool.error(f"Error while crawl for {to_find}s -> {e}")

        return to_return_dict


    def get_topics_list(self) -> List[List[str]]:
        return [[key, value] for key, value in self.threads_topics.items()]
    
    def get_topics_urls_only(self) -> List[str]:
        return [key for key, value in self.threads_topics.items()]
    
    def get_topics_titles_only(self) -> List[str]:
        return [value for key, value in self.threads_topics.items()]


class InvisionCrawler:
    """
    Specific functionalities for Invision forums
    """
    def __init__(self):
        self.threads_class: List[str] = ["div >> class :: ipsDataItem_main"]     # Used for threads and subforums
        self.topics_class: List[str] = ["div >> class :: ipsDataItem_main"]      # Used for topics
        self.threads_whitelist: List[str] = ["forum"]
        self.threads_blacklist: List[str] = ["topic"]
        self.topics_whitelist: List[str] = ["topic"]
        self.topics_blacklist: List[str] = ["page", "#comments"]
        self.pagination: List[str] = ["ipsPagination_next"]             # Used for subforums and topics pagination
        self.topic_title_class: List[str] = ["h1 >> class :: ipsType_pageTitle ipsContained_container"]  # Used for topic title on topic 1-st page
        self.content_class: List[str] = ["div >> data-role :: commentContent"]  # Used for content_class

class PhpBBCrawler:
    """
    Specific functionalities for phpBB forums
    """
    def __init__(self):
        self.threads_class: List[str] = ["a >> class :: forumtitle", "a >> class :: forumlink"]  # Used for threads
        self.topics_class: List[str] = ["a >> class :: topictitle"]  # Used for topics
        self.threads_whitelist: List[str] = []
        self.threads_blacklist: List[str] = []
        self.topics_whitelist: List[str] = []
        self.topics_blacklist: List[str] = []
        self.pagination: List[str] = ["pagination-arrow", "next", "arrow next", "right-box right", "title :: Dalej", "pag-img", "right-box-topic right btn btn-primary", "span >> class :: pagination"]  # Different phpBB forums
        self.topic_title_class: List[str] = ["h2 >>  :: ", "h2 >> class :: topic-title", "h2 >> class :: viewtopic", "a >> class :: nav"]  # Used for topic title on topic 1-st page
        self.content_class: List[str] = ["div >> class :: content", "div >> class :: postbody"]  # Used for content_class / messages

class IPBoardCrawler:
    """
    Specific functionalities for IPBoard forums
    """
    def __init__(self):
        self.threads_class: List[str] = ["td >> class :: col_c_forum"]  # Used for threads
        self.topics_class: List[str] = ["a >> class :: topic_title"]  # Used for topics
        self.threads_whitelist: List[str] = []
        self.threads_blacklist: List[str] = []
        self.topics_whitelist: List[str] = []
        self.topics_blacklist: List[str] = []
        self.pagination: List[str] = ["next"]  # Used for subforums and topics pagination
        self.topic_title_class: List[str] = ["h1 >> class :: ipsType_pagetitle"]  # Used for topic title on topic 1-st page
        self.content_class: List[str] = ["div >> class :: post entry-content"]  # Used for content_class / messages

class XenForoCrawler:
    """
    Specific functionalities for XenForo forums
    """
    def __init__(self):
        self.threads_class: List[str] = ["h3 >> class :: node-title"]  # Used for threads
        self.topics_class: List[str] = ["div >> class :: structItem-title"]  # Used for topics
        self.threads_whitelist: List[str] = []
        self.threads_blacklist: List[str] = ["prefix_id"]
        self.topics_whitelist: List[str] = ["threads"]
        self.topics_blacklist: List[str] = ["preview"]
        self.pagination: List[str] = ["pageNav-jump pageNav-jump--next"]  # Used for subforums and topics pagination
        self.topic_title_class: List[str] = ["h1 >> class :: p-title-value"]  # Used for topic title on topic 1-st page
        self.content_class: List[str] = ["article >> class :: message-body js-selectToQuote"]  # Used for content_class / messages

class UnsupportedCrawler:
    """
    Specific functionalities for Unsupported forum engines
    """
    def __init__(self):
        self.threads_class: List[str] = []
        self.topics_class: List[str] = []
        self.threads_whitelist: List[str] = []
        self.threads_blacklist: List[str] = []
        self.topics_whitelist: List[str] = []
        self.topics_blacklist: List[str] = []
        self.pagination: List[str] = []
        self.topic_title_class: List[str] = []
        self.content_class: List[str] = []