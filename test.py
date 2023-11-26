import pandas as pd

from speakleash_forum_tools import ConfigManager, CrawlerManager, Scraper, ManifestManager


# Example usage:
if __name__ == "__main__":
    print("*****************")

    ### Engine: invision
    #+ config_manager = ConfigManager()      # Default: forum.szajbajk.pl -> invision                           # Topics to find = 18k (from dashboard) == almost all
    #+ config_manager = ConfigManager(dataset_url='https://max3d.pl/forums/', forum_engine='invision')          # Topics to find = 85.5k (from dashboard) == to big for testing manual crawler

    ### Engine: phpBB 
    config_manager = ConfigManager(dataset_url="https://forum.prawojazdy.com.pl", forum_engine='phpbb', time_sleep=0.2, processes=6)      # Topics to find = 21 669 (calc from website) == almost all
    #+ config_manager = ConfigManager(dataset_url="https://www.gry-planszowe.pl", forum_engine='phpbb')         # Topics to find = 24 596 (calc from website) == almost all
    #+ config_manager = ConfigManager(dataset_url="https://www.excelforum.pl", forum_engine='phpbb')            # Topics to find = 58 414 (calc from website) == 48k found

    ### Engine: ipboard
    #+ config_manager = ConfigManager(dataset_url="https://forum.omegaklub.eu", forum_engine='ipboard')         # Disconnect for no reason
    #+ config_manager = ConfigManager(dataset_url="http://forum-kulturystyka.pl", forum_engine='ipboard')       # Topics to find = 110k ~ 119k (calc ~ dashboard)

    ### Engine: xenforo
    # https://forum.modelarstwo.info --> Crawl-delay = 15sec (in robots.txt)
    #+ config_manager = ConfigManager(dataset_url="https://forum.modelarstwo.info", forum_engine='xenforo')     # Topics to find = 16 500 (calc from website) == almost all


    # Use the settings from config_manager.settings as needed
    crawler = CrawlerManager(config_manager)
    if crawler.start_crawler():
        scraper = Scraper(config_manager, crawler)
        total_docs = scraper.start_scraper()
        if total_docs:
            merge_archive_path, docs_num, total_chars = scraper.arch_manager.merge_archives()
            manifest_created = ManifestManager(config_manager, scraper.arch_manager.merged_archive_path, total_docs=docs_num, total_characters=total_chars)
            if manifest_created:
                print("+++ HEY! WE CREATE EVERYTHING!!! +++")