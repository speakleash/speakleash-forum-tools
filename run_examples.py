from speakleash_forum_tools import ForumToolsCore


# Example usage:
if __name__ == "__main__":

    ### Check robots.txt before - library should download 'robots.txt' in forum directory

    ### Engine: invision (should have sitemaps)
    #+ ForumToolsCore()      # Default: forum.szajbajk.pl -> invision                           # Topics to find = 18k (from dashboard) == almost all
    #+ ForumToolsCore(dataset_url='https://max3d.pl/forums/', forum_engine='invision')          # Topics to find = 85.5k (from dashboard) == to big for testing manual crawler

    ### Engine: phpBB (old forum engine, small % sitemaps)
    #+ ForumToolsCore(dataset_url="https://forum.prawojazdy.com.pl/", forum_engine='phpbb', pagination = ["next"], time_sleep = 0.5, processes = 4)  # Topics to find = 21 669 (calc from website) == almost all
    #+ ForumToolsCore(dataset_url="https://www.gry-planszowe.pl", forum_engine='phpbb', log_lvl='DEBUG')         # Topics to find = 24 596 (calc from website) == almost all
    #+ ForumToolsCore(dataset_url="http://www.excelforum.pl", forum_engine='phpbb', log_lvl='DEBUG')            # Topics to find = 58 414 (calc from website) == 48k found

    ### Engine: ipboard (sometimes sitemaps)
    #+ ForumToolsCore(dataset_url="https://forum.omegaklub.eu", forum_engine='ipboard')         # Disconnect for no reason
    #+ ForumToolsCore(dataset_url="http://forum-kulturystyka.pl", forum_engine='ipboard')       # Topics to find = 110k ~ 119k (calc ~ dashboard)

    ### Engine: xenforo (sometimes sitemaps)
    # https://forum.modelarstwo.info --> Crawl-delay = 15sec (in robots.txt)
    #+ ForumToolsCore(dataset_url="https://forum.modelarstwo.info", forum_engine='xenforo', log_lvl='DEBUG')     # Topics to find = 16 500 (calc from website) == almost all

    # ForumToolsCore(dataset_url = "https://forum.mitsumaniaki.pl", 
    #                 forum_engine = 'phpbb',
    #                 content_class = ["span >> class :: postbody"],
    #                 processes = 6,
    #                 log_lvl="DEBUG" ) 

    #ForumToolsCore(dataset_url = "https://www.excelforum.pl", 
    #                forum_engine = 'phpbb',
    #                content_class = ["span >> class :: postbody"],
    #                processes = 4,
    #                web_encoding = 'iso-8859-2',
    #                log_lvl="DEBUG") 

    # ForumToolsCore(dataset_url = "https://naobcasach.pl", 
    #                 forum_engine = 'phpbb',
    #                 processes = 4,
    #                 log_lvl="DEBUG" ) 

    ForumToolsCore(dataset_url = "https://jerkbait.pl/", 
                    forum_engine = 'ipboard',
                    processes = 4,
                    log_lvl="DEBUG" ) 