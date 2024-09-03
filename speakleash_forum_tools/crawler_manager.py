"""
Crawler Manager Module

This module provides a CrawlerManager class designed to efficiently manage the 
crawling process on various forum websites. It leverages sitemaps when available 
or falls back to manual crawling using the ForumEnginesManager class, depending on 
the forum's structure and available data.

The CrawlerManager class orchestrates the crawling operation by integrating the 
configuration settings from the ConfigManager class, processing the forum website, 
and returning a comprehensive list of topic URLs. 

The module is designed to offer flexibility, scalability, and robustness in crawling operations across 
diverse forum platforms, ensuring a streamlined and effective data extraction process.

Key Features:
- Configurable crawling strategy utilizing both sitemaps and manual crawling techniques.
- Integration with ForumEnginesManager for enhanced crawling capabilities across different forum engines.
- Adherence to forum's scraping policies through the use of urllib.robotparser.
- Efficient data handling and processing, optimized for performance and memory usage.
- Advanced filtering mechanisms, including whitelist and blacklist options, for precise crawling control.
- Capability to handle pagination and extract content based on specified HTML tags and selectors.

Classes:
- CrawlerManager: The primary class responsible for managing the crawling process. It initializes with 
  settings from ConfigManager, employs advanced crawling techniques, and outputs a list of topic URLs. 
  The class effectively manages the crawling workflow, ensuring compliance with scraping policies and 
  efficient data extraction.

Dependencies:
- usp (ultimate-sitemap-parser) - Provides good parser for sitemap.xml files (XML, GZIP etc.). 
    Used fork with adopted XML files packed into PHP files - 
    https://github.com/Samox1/ultimate-sitemap-parser@develop#egg=ultimate-sitemap-parser
- pandas - Provides an easy-to-use DataFrame structure for simple management of collected data. 
    (In future: polars - less memory allocated by DataFrame)
- logging - For tracking and logging the crawling process.
- requests, urllib, BeautifulSoup -  For web requests and HTML parsing.
"""
import os
import re
import time
import logging
from typing import List

import pandas
from usp.tree import sitemap_tree_for_homepage      # install ultimate-sitemap-parser (use this fork: pip install git+https://github.com/Samox1/ultimate-sitemap-parser@develop#egg=ultimate-sitemap-parser )

from speakleash_forum_tools.config_manager import ConfigManager
from speakleash_forum_tools.forum_engines import ForumEnginesManager
from speakleash_forum_tools.archive_manager import ArchiveManager

# logging.getLogger("usp.helpers").setLevel(logging.ERROR)        # Set logging level for 'ultimate-sitemap-parser' to only ERROR
# logging.getLogger("usp.fetch_parse").setLevel(logging.ERROR)    # Set logging level for 'ultimate-sitemap-parser' to only ERROR

class CrawlerManager:
    """
    Crawler Manager class handle crawling on given forum website - using sitemaps (if found) 
    or manual crawling using ForumEnginesManager class.
    Import all settings from ConfigManager class, process website and return Topic URLs list.

    How it works:
    1) Import all settings, robotparser and other from ConfigManager
    2) Checks if sitemaps are in robots.txt
    3) Checks if sitemaps are in other places or if they exist at all
    4) If sitemaps exist it parses them using the appropriate engine / library
    5) If sitemaps do not exist then it uses the forum crawl engine from the ForumEnginesManager class.
    6) If there are pages / topics to crawl then it displays the number of them and returns a list of URLs 
        (optionally with topic names if collected manually)
    7) Updates all settings for further process -> scraping

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
    - pagination (List[str]): "<attribute_value>" (when attribute_name is 'class'), 
        "<attribute_name> :: <attribute_value>" (if anchor_tag is ['li', 'a', 'div']) 
        or "<anchor_tag> >> <attribute_name> :: <attribute_value>", e.g. ["arrow next", "right-box right", "title :: Dalej"] (for phpBB engine)
    - topic_title_class (List[str]): Searched for first instance -> "<anchor_tag> >> <attribute_name> :: <attribute_value>"
        e.g. ["h2 >>  :: ", "h2 >> class :: topic-title"] (for phpBB engine)
    - content_class (List[str]): "<anchor_tag> >> <attribute_name> :: <attribute_value>", 
        e.g. ["content_class"] (for phpBB engine)
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger_tool = self.config_manager.logger_tool
        self.logger_print = self.config_manager.logger_print

        if self.config_manager.logger_tool.level > 10:
            logging.getLogger("usp.helpers").setLevel(logging.ERROR)        # Set logging level for 'ultimate-sitemap-parser' to only ERROR
            logging.getLogger("usp.fetch_parse").setLevel(logging.ERROR)    # Set logging level for 'ultimate-sitemap-parser' to only ERROR

        self.files_folder = self.config_manager.files_folder
        self.dataset_folder = self.config_manager.dataset_folder
        self.dataset_name = self.config_manager.settings['DATASET_NAME']
        self.topics_dataset_file = self.config_manager.topics_dataset_file
        self.topics_visited_file = self.config_manager.topics_visited_file

        self.forum_topics, self.visited_topics = self._check_dataset_files(self.dataset_name, self.topics_dataset_file, self.topics_visited_file)

        self.forum_engine = ForumEnginesManager(config_manager = self.config_manager)

        # self.start_crawler()
        # topics_to_scrap = self.get_urls_to_scrap()


    ### Functions ###

    def start_crawler(self) -> bool:
        """
        Crawler starting function. Takes ConfigManager and create ForumEnginesManager class.
        Start searching and parsing sitemaps (if found) or crawl forum website manually with default HTML tags/selectors.
        Save Topics (and Topics titles optionally) as CSV files.

        :return: True if found Topics (>0) or False (==0)
        """
        if not self.forum_topics.empty:
            self.logger_tool.info("* CralwerManager found file with Topics...")
            self.logger_print.info("* CralwerManager found file with Topics...")
        else:

            if self.config_manager.settings['SITEMAPS']:
                self.sitemaps_url = self.config_manager.settings['SITEMAPS'][0]
                self.logger_tool.info(f"* Crawler will use Sitemaps URL -> {self.sitemaps_url}")
            else:
                self.sitemaps_url = self.config_manager.main_site

            try:
                self.logger_tool.info("---------------------------------------------------------------------------------------------------")
                self.logger_tool.info("* Crawler will try to find and parse Sitemaps (using 'ultimate-sitemap-parser' library)...")
                self.logger_print.info("---------------------------------------------------------------------------------------------------")
                self.logger_print.info("* Crawler will try to find and parse Sitemaps (using 'ultimate-sitemap-parser' library)...")
                forum_tree = self._tree_sitemap(self.sitemaps_url)
                self.forum_topics['Topic_URLs'] = self._urls_generator(forum_tree = forum_tree, 
                                                             whitelist = self.forum_engine.topics_whitelist, blacklist = self.forum_engine.topics_blacklist, 
                                                             robotparser = self.config_manager.robot_parser, force_crawl = self.config_manager.force_crawl)
                self.forum_topics['Topic_Titles'] = ""
                self.forum_topics = self.forum_topics.drop_duplicates(subset='Topic_URLs', ignore_index=True)

                if self.config_manager.settings['FORUM_ENGINE'] == 'phpbb':
                    self.forum_topics['Topic_URLs'] = self.phpbb_cut_query(self.forum_topics['Topic_URLs'])
                    self.forum_topics = self.forum_topics.drop_duplicates(subset='Topic_URLs', ignore_index=True)
                    
                self.logger_tool.info("---------------------------------------------------------------------------------------------------")
                self.logger_print.info("---------------------------------------------------------------------------------------------------")
            except Exception as e:
                self.logger_tool.error(f"CRAWLER: Error while searching and parsing Sitemaps: {e}")
                self.logger_print.error(f"CRAWLER: Error while searching and parsing Sitemaps: {e}")

            if self.forum_topics.empty:
                self.logger_tool.warning(f"* Crawler did not find any Topics URLs in stemaps... -> checking manually using engine for: {self.forum_engine.engine_type}")
                self.logger_print.info(f"* Crawler did not find any Topics URLs in stemaps... -> checking manually using engine for: {self.forum_engine.engine_type}")

                try:
                    if self.forum_engine.crawl_forum():
                        self.forum_topics['Topic_URLs'] = self.forum_engine.get_topics_urls_only()
                        self.forum_topics['Topic_Titles'] = self.forum_engine.get_topics_titles_only()
                        self.forum_topics = self.forum_topics.drop_duplicates(subset='Topic_URLs', ignore_index=True)
                except Exception as e:
                    self.logger_tool.error(f"CRAWLER: Error while crawling: {e}")
                    self.logger_print.error(f"CRAWLER: Error while crawling: {e}")

        self.logger_tool.info(f"* Crawler (Manager) found: Topics = {self.forum_topics.shape[0]}")
        self.logger_print.info(f"* Crawler (Manager) found: Topics = {self.forum_topics.shape[0]}")

        if self.forum_topics.shape[0] > 0:
            # Saving Topics to CSV
            self.forum_topics.to_csv(os.path.join(self._get_dataset_folder(), self.topics_dataset_file), sep='\t', header=True, index=False, encoding='utf-8')
            return True
        else:
            return False

    def get_urls_to_scrap(self) -> pandas.DataFrame:
        """
        Get URLs to crap (topics titles if found).

        :return: Pandas DataFrame with columns: ['Topic_URLs','Topic_Titles'] .
        """
        if self.visited_topics.empty:
            self.logger_tool.info(f"* Return Topics DataFrame: {self.forum_topics.shape[0]} URLs")
            return self.forum_topics
        else:
            #TODO: Zastanowic sie nad:: where(self.visited_topics['Visited_flag'] == 1 & self.visited_topics['Skip_flag'] == 0)     # Skip "1" jest z roznych powodow, np. error albo brak tekstu / Skip "0" to strona na ktorej byl tekst
            topics_minus_visited = self.forum_topics[~self.forum_topics['Topic_URLs'].isin(self.visited_topics['Topic_URLs'].where(self.visited_topics['Visited_flag'] == 1))]
            self.logger_tool.info(f"* Return [Topics - Visited] DataFrame: {topics_minus_visited.shape[0]} URLs")
            self.logger_print.info(f"* Return [Topics - Visited] DataFrame: {topics_minus_visited.shape[0]} URLs")
            return topics_minus_visited
        
    def get_visited_urls(self) -> pandas.DataFrame:
        """
        Get visited URLs (visited topics URL).

        :return: Pandas DataFrame with columns: ['Topic_URLs', 'Topic_Titles', 'Visited_flag', 'Skip_flag']
        """
        return self.visited_topics

    def _tree_sitemap(self, url: str):
        """
        Uses the Ulitmate Sitemap Parser's (Samox1 fork with extended search for XML and PHP files) 
        sitemap_tree_for_homepage method to get the sitemap and extract all the URLs.

        :param url (str): Website URL to get sitemap.

        :return: Tree of AbstractSitemap subclass objects that represent the sitemap hierarchy found on the website.
        """
        start_time = time.perf_counter()
        forum_tree = sitemap_tree_for_homepage(url)
        end_time = time.perf_counter()
        self.logger_tool.info(f"* Crawler - Sitemaps parsing = DONE || Time = {(end_time - start_time):.2f} sec = {((end_time - start_time) / 60):.2f} min")
        self.logger_print.info(f"* Crawler - Sitemaps parsing = DONE || Time = {(end_time - start_time):.2f} sec = {((end_time - start_time) / 60):.2f} min")
        return forum_tree

    def _urls_generator(self, forum_tree, whitelist: List[str], blacklist: List[str], robotparser, force_crawl: bool = False) -> list[str]:
        """
        Uses the Ulitmate Sitemap Parser's sitemap_tree_for_homepage method to get the sitemap and extract all the URLs.

        :param forum_tree (AbstractSitemap): Tree of AbstractSitemap subclass objects 
            that represent the sitemap hierarchy found on the website.

        :return: Extract all urls to scrap (list[str]).
        """
        # Extract all the URLs with EXPECTED_URL_PARTS (whitelist) in it 
        urls_expected: list[str] = []

        for page in forum_tree.all_pages():
            if self.config_manager.settings["DATASET_URL"] in page.url:
                if whitelist:
                    if any(url_part in page.url for url_part in whitelist):
                        if blacklist:
                            if any(url_part in page.url for url_part in blacklist):
                                self.logger_tool.debug(f"URL OUT <- {page.url}")
                                continue
                        if robotparser.can_fetch("*", page.url) or force_crawl == True:
                            self.logger_tool.debug(f"URL GOOD -> {page.url}")
                            urls_expected.append(page.url)
                        else:
                            self.logger_tool.debug(f"URL OUT <- {page.url}")
                        continue
                    else:
                        self.logger_tool.debug(f"URL OUT <- {page.url}")
                        continue
                if blacklist:
                    if any(url_part in page.url for url_part in blacklist):
                        self.logger_tool.debug(f"URL OUT <- {page.url}")
                        continue

                if not whitelist or not blacklist:
                    if robotparser.can_fetch("*", page.url) or force_crawl == True:
                        self.logger_tool.debug(f"URL GOOD (+) -> {page.url}")
                        urls_expected.append(page.url)
                    else:
                        self.logger_tool.debug(f"URL OUT (+) <- {page.url}")
            else:
                self.logger_tool.debug(f"CRAWLER // URL not from desire forum: {page.url}")

        urls_expected = list(set(urls_expected))
        self.logger_tool.debug(f"CRAWLER // URL Generator -> URLs_expected: {len(urls_expected)}")
        return urls_expected

    def phpbb_cut_query(self, urls_list):
        cleaned_urls_list = [re.sub(r"&start=\d+", '', url) for idx, url in enumerate(urls_list)]
        return cleaned_urls_list


    def _check_dataset_files(self, dataset_name: str, topics_urls_filename: str = "Topics_URLs.csv", topics_visited_filename: str = "Visited_Topics_URLs.csv") -> tuple[pandas.DataFrame, pandas.DataFrame]:
        """
        Checking if exists files with:
        1) forum urls - if not create sitemaps tree -> generate urls -> save to file.
        2) visited urls - if not create empty file.

        :param crawl_urls_filename (str): Filename for CSV file with topics urls 
            --> 3 columns = ['Topic_URLs', 'Topic_Titles'] (sep = '\t').
        :param visited_filename (str): Filename for CSV file with visited urls 
            --> 3 columns = ['Topic_URLs', 'Topic_Titles', 'Visited_flag', 'Skip_flag'] (sep = '\t').

        Returns
        -------
        :return topics_links (pandas.DataFrame): DataFrame (pandas) with urls generated from sitemaps tree or crawler engine, ['Topic_URLs', 'Topic_Titles'].
        :return visited_links (pandas.DataFrame): DataFrame (pandas) with ['Topic_URLs', 'Topic_Titles', 'Visited_flag', 'Skip_flag'].
        """
        dataset_folder = self._get_dataset_folder()
        
        topics_links = pandas.DataFrame(columns=['Topic_URLs', 'Topic_Titles'])
        visited_links = pandas.DataFrame(columns=['Topic_URLs', 'Topic_Titles', 'Visited_flag', 'Skip_flag'])

        if os.path.exists(dataset_folder):
            self.logger_tool.info(f"* Folder for [{dataset_name}] exist -> Checking files...")
            # Check if file with Topics URLs exists
            if os.path.exists(os.path.join(dataset_folder, topics_urls_filename)):
                # Read parsed Topics URLs
                topics_links = pandas.read_csv(os.path.join(dataset_folder, topics_urls_filename), sep = '\t', header = 0, names = ['Topic_URLs', 'Topic_Titles'], index_col = None)
                self.logger_tool.info(f"Imported Topics URLs for: [{dataset_name}] | Shape: {topics_links.shape} | Size in memory (MB): {(topics_links.memory_usage(deep=True).sum() / pow(10,6)):.3f}")
                self.logger_print.info(f"* Imported Topics URLs for: [{dataset_name}] | Shape: {topics_links.shape}")
            else:
                self.logger_tool.info(f"File with Topics URLs not found... [{topics_urls_filename}]")

            if os.path.exists(os.path.join(dataset_folder, topics_visited_filename)):
                # Read scraped Visited Topics URLs
                visited_links = pandas.read_csv(os.path.join(dataset_folder, topics_visited_filename), sep = '\t', header = 0, names = ['Topic_URLs', 'Topic_Titles', 'Visited_flag', 'Skip_flag'])
                self.logger_tool.info(f"Imported Visited Topics URLs for: {dataset_name} | Shape: {visited_links.shape} | Size in memory (MB): {(visited_links.memory_usage(deep=True).sum() / pow(10,6)):.3f}")
                self.logger_print.info(f"* Imported Visited Topics URLs for: {dataset_name} | Shape: {visited_links.shape}")
            else:
                self.logger_tool.info(f"File with Visited Topics URLs not found... [{topics_visited_filename}]")
        else:
            self.logger_tool.warning(f"* Can't find folder for [{dataset_name}]... -> Create new folder...")
            os.makedirs(dataset_folder)

        if not topics_links.empty:
            topics_links = topics_links.drop_duplicates(subset='Topic_URLs', ignore_index=True)

        if not visited_links.empty:
            visited_links = visited_links.drop_duplicates(subset='Topic_URLs', ignore_index=True)

        return topics_links, visited_links


    def _get_dataset_folder(self) -> str:
        """
        Return path to directory for the dataset.

        :return: Path folder for desire dataset.
        """
        return self.dataset_folder
