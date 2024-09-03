"""
ForumToolsCore Module

This module provides a core class for the `speakleash_forum_tools` package, integrating various components such as 
the config manager, crawler manager, scraper, and manifest manager to facilitate forum crawling and scraping.

Classes:
    ForumToolsCore: The main class that integrates various components of the 
    `speakleash_forum_tools` package for effective crawling and scraping of forums.

Dependencies:
    speakleash_forum_tools.src.config_manager: Provides the ConfigManager class for configuration management.
    speakleash_forum_tools.src.crawler_manager: Provides the CrawlerManager class for forum crawling.
    speakleash_forum_tools.src.scraper: Provides the Scraper class for scraping data from forums.
    speakleash_forum_tools.src.manifest_manager: Provides the ManifestManager class for managing dataset manifests.
"""
import logging
from typing import List, Literal

from speakleash_forum_tools.config_manager import ConfigManager
from speakleash_forum_tools.crawler_manager import CrawlerManager
from speakleash_forum_tools.scraper import Scraper
from speakleash_forum_tools.manifest_manager import ManifestManager


class ForumToolsCore:
    """
    A core class that orchestrates the workflow of crawling and scraping forums.

    This class integrates various components such as ConfigManager, CrawlerManager, Scraper,
    and ManifestManager to provide a streamlined process for crawling, scraping, and handling
    data from forums.

    Attributes:
        config_manager (ConfigManager): Manages the configuration settings for the forum tools.
        crawler (CrawlerManager): Handles the crawling of forum pages.
        scraper (Scraper): Responsible for scraping content from crawled pages.
        manifest_manager (ManifestManager): Manages the creation of dataset manifests post-scraping.

    """

    def __init__(
        self,
        dataset_url: str = "https://forum.szajbajk.pl",
        dataset_category: str = "Forum",
        forum_engine: Literal['invision', 'phpbb', 'ipboard', 'xenforo', 'other'] = "invision",
        dataset_name: str = "",
        arg_parser: bool = False,
        check_robots: bool = True,
        force_crawl: bool = False,
        processes: int = 2,
        time_sleep: float = 0.5,
        save_state: int = 100,
        min_len_txt: int = 20,
        sitemaps: str = "",
        log_lvl: int | Literal['INFO', 'DEBUG', 'ERROR'] = logging.INFO,
        print_to_console: bool = True,
        threads_class: List[str] = [],
        threads_whitelist: List[str] = [],
        threads_blacklist: List[str] = [],
        topic_class: List[str] = [],
        topic_whitelist: List[str] = [],
        topic_blacklist: List[str] = [],
        pagination: List[str] = [],
        topic_title_class: List[str] = [],
        content_class: List[str] = [],
        web_encoding: str = '',
    ):
        """
        Initializes the ForumToolsCore class with the given configuration settings 
        and prepares the crawling and scraping process.
        Initializes and integrates the ConfigManager, CrawlerManager, Scraper, and ManifestManager
        for effective forum crawling and scraping operations.

        :param dataset_url (str): The base URL of the dataset or forum to be processed.
        :param dataset_category (str): The category of the dataset, e.g., 'Forum'.
        :param forum_engine (str): The type of forum engine: ['invision', 'phpbb', 'ipboard', 'xenforo', 'other'].
        :param dataset_name (str): Optional custom name for the dataset.
        :param arg_parser (bool): Flag to enable command-line argument parsing.
        :param check_robots (bool): Flag to check and adhere to the forum's robots.txt.
        :param force_crawl (bool): Flag to force crawling even if disallowed by robots.txt.
        :param processes (int): The number of processes to use for multiprocessing.
        :param time_sleep (float): Time delay between requests during crawling.
        :param save_state (int): Checkpoint interval for saving the crawling progress.
        :param min_len_txt (int): Minimum length of text to consider valid for scraping.
        :param sitemaps (str): Custom sitemaps to be used for crawling.
        :param log_lvl: The logging level for logging operations.
        :param print_to_console (bool): Flag to enable or disable console logging. Shows only progress bar.
        :param threads_class (List[str]): HTML selectors used for identifying thread links in the forum.
            "<anchor_tag> >> <attribute_name> :: <attribute_value>", e.g. ["a >> class :: forumtitle"] (for phpBB engine).
        :param topics_class (List[str]): HTML selectors used for identifying topic links within a thread.
            "<anchor_tag> >> <attribute_name> :: <attribute_value>", e.g. ["a >> class :: topictitle"] (for phpBB engine)
        :param threads_whitelist (List[str]): List of substrings; only threads whose URLs contain 
            any of these substrings will be processed. Example for Invision forum: ["forum"].
        :param threads_blacklist (List[str]): List of substrings; threads whose URLs contain 
            any of these substrings will be ignored. Example for Invision forum: ["topic"].
        :param topics_whitelist (List[str]): List of substrings; only topics whose URLs contain 
            any of these substrings will be processed. Example for Invision forum: ["topic"].
        :param topics_blacklist (List[str]): List of substrings; topics whose URLs contain 
            any of these substrings will be ignored. Example for Invision forum: ["page", "#comments"].
        :param pagination (List[str]): HTML selectors used for identifying pagination elements within threads or topics.
            "<attribute_value>" (when attribute_name is 'class'), "<attribute_name> :: <attribute_value>" (if anchor_tag is ['li', 'a', 'div'])
            or "<anchor_tag> >> <attribute_name> :: <attribute_value>", e.g. ["arrow next", "right-box right", "title :: Dalej"] (for phpBB engine)
        :param topic_title_class (List[str]): HTML selector for topic title on topic website. 
            Search for first instance -> "<anchor_tag> >> <attribute_name> :: <attribute_value>"
            e.g. ["h2 >>  :: ", "h2 >> class :: topic-title"] (for phpBB engine)
        :param content_class (List[str]): HTML selectors used for identifying the main content within a topic. 
            "<anchor_tag> >> <attribute_name> :: <attribute_value>", e.g. ["content_class"] (for phpBB engine)
        :param web_encoding (str): Website encoding - because not every website is in UTF-8...
        """
        # Prepare settings and configuration
        config_manager = ConfigManager(
            dataset_url,
            dataset_category,
            forum_engine,
            dataset_name,
            arg_parser,
            check_robots,
            force_crawl,
            processes,
            time_sleep,
            save_state,
            min_len_txt,
            sitemaps,
            log_lvl,
            print_to_console,
            threads_class,
            threads_whitelist,
            threads_blacklist,
            topic_class,
            topic_whitelist,
            topic_blacklist,
            pagination,
            topic_title_class,
            content_class,
            web_encoding,
        )

        # Prepare Crawler for selected forum engine
        crawler = CrawlerManager(config_manager)

        # Start Crawler (sitemaps/manual crawl)
        if crawler.start_crawler():
            # Configure Scraper
            scraper = Scraper(config_manager, crawler)

            # Start Scraper with crawled URLs and visited URLs (if something was scraped)
            total_docs = scraper.start_scraper(
                crawler.get_urls_to_scrap(), crawler.get_visited_urls()
            )

            # If forum is scraped...
            if total_docs:
                # Merge all archive chunks from temp directory (drop duplicated)
                merge_archive_path, docs_num, total_chars = scraper.arch_manager.merge_archives()

                # Create manifest for created dataset file (*.jsonl.zst)
                ManifestManager(
                    config_manager,
                    directory_to_save = scraper.arch_manager.merged_archive_path,
                    total_docs = docs_num,
                    total_characters = total_chars,
                )

                # End Queue listener for multiprocessing logging tool (logging to log file)
                config_manager.q_listener.stop()
