"""
Utility Module

Provides funcions for other modules.
"""
import pathlib
import time
import requests
import logging
from requests.adapters import HTTPAdapter           # install requests
from urllib3.util.retry import Retry                # install urllib3
from typing import Optional, Union

from speakleash_forum_tools.__version__ import __version__
import pandas as pd
import polars as pl

def create_session(retry_total: Optional[Union[bool, int]] = 3, retry_backoff_factor: float = 3.0, verify: bool = False) -> requests.Session:
    """
    Creates and configures a new session with retry logic for HTTP requests.

    This function initializes a `requests.Session` object and sets up a retry mechanism
    for failed requests. It configures the session to retry up to three times with a
    backoff factor to control the delay between retries. The session is equipped to handle
    both HTTP and HTTPS requests.

    The function also ensures that SSL certificate verification is disable for the session.

    :return (requests.Session): A configured session object with retry logic.
    :rtype: requests.Session
    """
    session = requests.Session()
    retry = Retry(total = retry_total, backoff_factor = retry_backoff_factor)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.verify = verify
    return session


def check_for_library_updates() -> bool:
    """
    Checks for the availability of new updates for the package.

    This function queries a specified online source to determine the latest available version 
    of the package. It then compares this version with the package's current version. If a newer 
    version is available, it notifies the user about the update.

    The function queries the package information from PyPI (or another specified source) and extracts 
    the version number from the response. It assumes that the package follows semantic versioning.

    :return (bool): Return True and outputs a message to the console if an update is available.
    """
    current_version = __version__
    try:
        response = requests.get('https://pypi.org/pypi/speakleash-forum-tools/json')
        latest_version = response.json()['info']['version']
    except Exception as e:
        logging.warning(f"Can't find library on pypi.org || Error: {e}")
        latest_version = "unknown"

    if current_version != latest_version:
        print_info = f"Update available: {latest_version} || You are currently using version: {current_version}."
        logging.info(len(print_info) * "^")
        logging.info(print_info)
        logging.info(len(print_info) * "_")
        return True
    
    return False


# timming decorator
def timewrap(func):
    def innerfunc(*args, **kwargs):
        start = time.perf_counter()
        output = func(*args, **kwargs)
        end = time.perf_counter()
        logging.info(f"* Timing * -> Func: {func.__name__} | Time: {(end-start) * 1000} ms = {end-start} sec = {(end-start)/60} min")
        return output
    return innerfunc

def load_zst_data(path: pathlib.Path | str) -> pl.DataFrame:
    if isinstance(path, pathlib.Path):
        path = path.as_posix()  
    df = pl.DataFrame(pd.read_json(path, lines=True))
    return df.unnest('meta')

def turn_zst_data_to_delta(path: pathlib.Path | str, output_path: pathlib.Path | str) -> None:
    df = load_zst_data(path)
    if isinstance(output_path, pathlib.Path):
        output_path = output_path.as_posix()
    df.write_delta(output_path, mode='overwrite')

def display_polars_df_as_full_table(df: pl.DataFrame, limit: int = 100, column_width: int = 1000) -> None:
    with pl.Config(fmt_str_lengths=column_width, tbl_formatting="ASCII_FULL"):
        print(df.head(limit))