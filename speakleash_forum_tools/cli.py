from typing import Literal
import click
from speakleash_forum_tools.core import ForumToolsCore
from speakleash_forum_tools.utils import (
    display_polars_df_as_full_table,
    load_zst_data,
    turn_zst_data_to_delta,
)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--dataset_url", "-d", required=True, help="URL of the forum dataset to scrape."
)
@click.option(
    "--forum_engine",
    "-f",
    required=True,
    type=click.Choice(["invision", "phpbb", "ipboard", "xenforo", "other"]),
    default="invasion",
    help="Forum engine to use for scraping.",
)
@click.option(
    "--pagination", "-p", multiple=True, help="Pagination settings for the forum."
)
@click.option("--time_sleep", "-t", default=0.5, help="Time to sleep between requests.")
@click.option(
    "--processes", "-n", default=2, help="Number of processes to use for scraping."
)
@click.option(
    "--log_level",
    "-l",
    default="INFO",
    type=click.Choice(["INFO", "DEBUG"]),
    help="Logging level for the scraper.",
)
@click.option(
    "--dataset_name",
    default="",
    help="Name of the dataset to be saved. If not provided, the dataset will be saved with the forum engine name.",
)
def run_scraper(
    dataset_url: str,
    forum_engine: Literal["invision", "phpbb", "ipboard", "xenforo", "other"],
    pagination: list,
    time_sleep: float,
    processes: int,
    log_level: Literal["INFO", "DEBUG"] = "INFO",
    dataset_name: str = "",
):
    print(f"Running scraper for {dataset_url} with engine {forum_engine}")
    print(f"Pagination: {pagination}")
    print(f"Time sleep: {time_sleep}")
    print(f"Processes: {processes}")
    ForumToolsCore(
        dataset_url=dataset_url,
        forum_engine=forum_engine,
        processes=processes,
        log_lvl=log_level,
        dataset_name=dataset_name,
    )


@cli.command()
@click.option("--file_path", "-f", required=True, help="Path to the file to preview.")
@click.option("--limit", "-l", default=100, help="Limit the number of rows to preview.")
def preview_data(file_path: str, limit: int = 100):
    df = load_zst_data(file_path)
    display_polars_df_as_full_table(df, limit)


@cli.command()
@click.option("--file_path", "-f", required=True, help="Path to the file to preview.")
@click.option("--output_path", "-o", required=True, help="Path to save the delta file.")
def turn_to_delta(file_path: str, output_path: str):
    turn_zst_data_to_delta(file_path, output_path)
