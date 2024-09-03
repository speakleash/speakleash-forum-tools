"""
Archive Manager Module

This module offers the ArchiveManager class, which is essential for managing data archiving in 
the context of a forum crawling and scraping tool. The class is specifically designed to handle 
various file management tasks related to the archival process of scraped data, including the 
creation of folders, merging of data chunks, and maintaining records of visited URLs.

The ArchiveManager class aims to streamline the archiving aspect of the web scraping process, 
providing a robust and scalable solution for handling large volumes of data in an organized manner.

Key Features:
- Efficient management of archive directories, ensuring organized storage of scraped data.
- Creation and maintenance of visited URLs file, aiding in tracking the progress of the scraping process.
- Merging functionality for combining multiple archive chunks into a single, consolidated file.
- Support for creating empty template files for storing scraped data, enhancing data management efficiency.
- Utilization of the 'lm-dataformat' library for handling JSONL.ZST file format, ensuring high compression and fast access.

Classes:
- ArchiveManager: The primary class in this module, responsible for various archiving operations. 
  It initializes with dataset names and paths, manages temporary and merged archive folders, and provides 
  functionalities for adding URLs to visited files, merging archives, and creating empty files for future data storage.

Dependencies:
- pandas: Used for data manipulation and CSV file operations.
- os, glob, tqdm: Utilized for file system interactions and progress tracking.
- logging: For logging and monitoring the archiving process.
- lm-dataformat: For handling and managing archive formats such as JSONL.ZST .

"""
import os
import glob
import shutil
import logging
from typing import Tuple

import pandas
from lm_dataformat import Archive, Reader
from tqdm import tqdm

class ArchiveManager:
    """
    ArchiveManager class is to manage:
    1) creating folders:
        1.a) temp folder - for scraper archives chunks 
    2) functions:
        2.a) __init__ - init folders / Archive class
        2.b) add_to_visited_file
        2.c) merge archives after scraping
    3) prepare Archive (with path to specific folder)
    """
    def __init__(self, dataset_name: str, dataset_folder: str, logger_tool: logging.Logger, logger_print: logging.Logger, print_to_console: bool):
        """
        ArchiveManager class provides simple functions for managing Archive and everything around this topic.
        Import important names and paths, process some more paths and prepare Archive class.
        Provides function "merge_archives" to merge all archive chunks.

        :param dataset_name (str): Dataset name.
        :param dataset_folder (str): Path to dataset directory.
        :param visited_filename (str): File name with visited URLs.
        """
        self.logger_tool = logger_tool
        self.logger_print = logger_print
        self.print_to_console = print_to_console

        self.dataset_zst_filename = dataset_name + '.jsonl.zst'
        self.dataset_name = dataset_name
        self.dataset_folder = dataset_folder
        self.temp_data_path = os.path.join(self.dataset_folder, 'temp_scraper_data')
        self.merged_archive_path = os.path.join(self.dataset_folder, 'archive_merged-JSONL_ZST')
        
        self._create_archive_folder()                       # Create folder for Archive (temp_scraper_data)
        self.archive = Archive(self.temp_data_path)         # Archive - manager for temporary chunks of archives
        

    def _create_archive_folder(self) -> None:
        """
        Create the temp archive folder -> 'temp_scraper_data' (if it doesn't exist).
        """
        try:
            if not os.path.exists(self.temp_data_path):
                os.makedirs(self.temp_data_path)
                self.logger_tool.info(f"Archive // Created archive folder at {self.temp_data_path}")
                self.logger_print.info(f"* Created archive folder at {self.temp_data_path}")
        except Exception as e:
            self.logger_tool.error(f"Archive // Error while checking or creating folder for 'temp_scraper_data' -> {e}")

    def merge_archives(self) -> Tuple[str, int, int]:
        """
        Merge all .zst archive files in the dataset folder into one.

        :return: Tuple containing the path to the merged archive, number of documents,
          and total number of characters across all documents.
        """
        self.logger_tool.info("* Preparing Archive for chunks merging...")
        self.logger_print.info("* Preparing Archive for chunks merging...")

        merged_file_path = os.path.join(self.merged_archive_path, f"{self.dataset_name}.jsonl.zst")
        merged_file_dir_temp = os.path.join(self.merged_archive_path, "temp")
        ar_merge = Archive(merged_file_dir_temp)

        # Find all .zst files in the temp_scraper_data directory
        data_files = glob.glob(os.path.join(self.temp_data_path, '*.zst'))
        urls_visited = []
        urls_duplicated = 0
        total_docs = 0
        total_chars = 0

        self.logger_tool.debug(f"Archive // Ready for merging loop...")

        # Re-packing chunks of archive to 1 output file
        for file_path in tqdm(data_files, disable = not self.print_to_console):
            self.logger_tool.debug(f"Archive // Merging file: {file_path}")
            arch_part = Reader(file_path)
            for id, record in enumerate(arch_part.stream_data(get_meta = True)):
                urel = record[1].get('url')
                if urel not in urls_visited:
                    urls_visited.append(urel)
                    ar_merge.add_data(data = record[0], meta = record[1])
                    total_docs += 1
                    total_chars += record[1].get('characters')
                else:
                    self.logger_tool.debug(f"Archive // Merging - URL duplicate: {urel}")
                    urls_duplicated += 1
        ar_merge.commit()
        del (ar_merge)          # Delete Archive class to avoid errors with directories
        self.logger_tool.info(f"* Merged {total_docs} documents with a total of {total_chars} characters | Duplicated: {urls_duplicated}")
        self.logger_print.info(f"* Merged {total_docs} documents with a total of {total_chars} characters | Duplicated: {urls_duplicated}")

        # Read merged archive - check if everything is okey
        try:
            data_merge = glob.glob(f'{merged_file_dir_temp}/*.zst')
            data_merge.sort()
            if not data_merge[-1]:
                self.logger_tool.error("Archive // Error! Can't find merged file -> *.jsonl.zst")
                return "", 0, 0
            len_archive_merged = 0
            ar_merge_reader = Reader(merged_file_dir_temp)

            # Check number of documents
            for id, doc in enumerate(ar_merge_reader.read_jsonl_zst(data_merge[-1], get_meta=True)):
                len_archive_merged = id
            len_archive_merged = len_archive_merged + 1
        except Exception as e:
            self.logger_tool.error(f"Archive // Error while checking merged Archive: {e}")

        # Last check everything was okey
        if len_archive_merged == total_docs:
            self.logger_tool.info(f"Archive // Checked Archive --> joined - DONE! | Docs: {len_archive_merged} | File: {merged_file_path}")
        else:
            self.logger_tool.error(f"Archive // Error! Length of merged Archive is different! -> {total_docs=} != {len_archive_merged=}")

        try:
            if os.path.exists(merged_file_path):
                os.remove(merged_file_path)
            shutil.move(data_merge[-1], merged_file_path)
        except Exception as e:
            self.logger_tool.error(f"Archive // Error while renaming: {e}")

        self.logger_print.info(f"Dataset File: {merged_file_path}")

        try:
            shutil.rmtree(merged_file_dir_temp)
        except Exception as e:
            self.logger_tool.error(f"Archive // Error while removedirs: {e}")

        return merged_file_path, total_docs, total_chars
