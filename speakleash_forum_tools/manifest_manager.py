"""
Manifest Manager Module

This module provides functionalities for creating and managing the manifest file associated with a dataset of forum discussions. 
It utilizes settings from the ConfigManager to generate a manifest file that contains metadata about the dataset.

The ManifestManager class in this module is responsible for creating a manifest file in JSON format. 
This file includes various details about the dataset, such as project name, dataset name, description, license, 
category, language, file size, sources, and statistical information about the dataset's content. 
The class handles both the generation of the manifest content and the writing of this content to a file, 
ensuring error handling and logging throughout the process.

Classes:
- ManifestManager: Manages the creation and handling of the dataset manifest file. 
It uses configuration settings provided by the ConfigManager and dataset specifics to construct a manifest with essential metadata.

Dependencies:
- os: Used for file and path operations related to the manifest file.
- json: Utilized for creating and writing the JSON formatted manifest file.
- logging: Provides logging capabilities for tracking the process of manifest creation.
- speakleash_forum_tools.src.config_manager.ConfigManager: Provides configuration settings necessary for manifest creation.
"""
import os
import json

from speakleash_forum_tools.config_manager import ConfigManager

class ManifestManager:
    def __init__(self, config_manager: ConfigManager, directory_to_save: str, total_docs: int = 0, total_characters: int = 0):
        """
        Using ConfigManager settings prepare manifest with placeholders.

        :param config_manager (ConfigManager): ConfigManager class with settings.
        :param directory_to_save (str): Path to directory where to save *.manifest .
        :param total_docs (int): Number of documents in merged (*.jsonl.zst) dataset file.
        :param total_characters (int): Number of characters in merged (*.jsonl.zst) dataset file.

        Attributes:
        - manifest_created (bool): True if manifest was created without issues.
        """
        self.logger_tool = config_manager.logger_tool
        self.logger_print = config_manager.logger_print
        
        self.manifest_created: bool = self.create_manifest(config_manager, directory_to_save, total_docs, total_characters)
        if self.manifest_created:
            self.logger_tool.info("* Manifest created (in directory with merged archive)")
            self.logger_print.info("* Manifest created (in directory with merged archive)")


    ### Functions ###

    def create_manifest(self, config_manager: ConfigManager, directory_to_save: str, total_docs: int = 0, total_characters: int = 0) -> bool:
        """
        Prepare manifest for dataset.

        :param config_manager (ConfigManager): ConfigManager class with settings.
        :param directory_to_save (str): Path to directory where to save *.manifest .
        :param total_docs (int): Number of documents in merged (*.jsonl.zst) dataset file.
        :param total_characters (int): Number of characters in merged (*.jsonl.zst) dataset file.

        :return: True if everything was OK and manifest is created, or False if something was wrong.
        """
        self.logger_tool.info("MANIFEST // Preparing to create manifest...")

        manifest_filename: str = config_manager.settings["DATASET_NAME"] + '.manifest'

        # Placeholder values, will be updated in postprocessing
        file_size = 0
        total_sentences = 0
        total_words = 0
        total_verbs = 0
        total_nouns = 0
        total_punctuations = 0
        total_symbols = 0
        total_stopwords = 0
        total_oovs = 0

        try:
            manifest = {"project" : "SpeakLeash", 
                            "name": config_manager.settings["DATASET_NAME"], 
                            "description": config_manager.settings["DATASET_DESCRIPTION"], 
                            "license": config_manager.settings["DATASET_LICENSE"], 
                            "category": config_manager.settings["DATASET_CATEGORY"], 
                            "language": "pl", 
                            "file_size": file_size,
                            "sources": [{"name": config_manager.settings["DATASET_NAME"], 
                                        "url": config_manager.settings["DATASET_URL"], 
                                        "license": config_manager.settings["DATASET_LICENSE"]}], 
                                        "stats": {"documents": total_docs, 
                                            "characters": total_characters, 
                                            "sentences": total_sentences, 
                                            "words" : total_words, 
                                            "nouns" : total_nouns, 
                                            "verbs" : total_verbs, 
                                            "punctuations" : total_punctuations, 
                                            "symbols" : total_symbols, 
                                            "stopwords": total_stopwords, 
                                            "oovs": total_oovs}}

            try:
                json_manifest = json.dumps(manifest, indent = 4)
            except Exception as e:
                self.logger_tool.error(f"Manifest // Error while json.dumps: {str(e)}")
                return e

            try:
                with open(os.path.join(directory_to_save, manifest_filename), 'w') as mf:
                    mf.write(json_manifest)
            except Exception as e:
                self.logger_tool.error(f"Manifest // Error while writing json file: {str(e)}")
                return e
            
        except Exception as e:
            self.logger_tool.error(f"Manifest // Error while creating manifest!!! | Error: {str(e)}")
            return False

        self.logger_tool.info(f"MANIFEST // Manifest created: {os.path.join(directory_to_save, manifest_filename)}")
        return True 
