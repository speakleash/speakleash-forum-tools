<h1 align="center">
<img src="https://raw.githubusercontent.com/speakleash/speakleash/main/branding/logo/speakleash_logo.png" width="300">
</h1><br>

<p align="center">
    <a href=""><img src="https://img.shields.io/badge/version-0.0.2-brightgreen"></a>
    <a href="https://pypi.org/project/speakleash"><img src="https://img.shields.io/badge/python-_>=_3.6-blue"></a>
    <a href="https://speakleash.org/"><img src="https://img.shields.io/badge/organisation-Speakleash-orange"></a>
</p>

# SpeakLeash Forum Tools

## Overview

SpeakLeash Forum Tools is a comprehensive toolkit designed for crawling, scraping, and managing data from various online forums. The package integrates multiple components such as configuration management, crawling, scraping, and archiving functionalities to streamline the process of extracting and organizing forum data.

## Features

- **Forum Crawling**: Efficiently crawl forums using sitemaps or manual crawling techniques.
- **Data Scraping**: Extract text data from forum pages with support for pagination and different forum engines.
- **Forum Engines Supports**: ['invision', 'phpbb', 'ipboard', 'xenforo', 'other'] - ‘other’ option is designed for more difficult forums, where appropriate parameters such as pagination or HTML paths with posts must be defined. 
- **Data Archiving**: Manage and merge scraped data into well-organized archives.
- **Manifest Management**: Create and handle SpeakLeash manifest files for datasets, including metadata and statistics.
- **Documentation**: Each module and class is carefully documented to make it easy to understand and use.
- **Detailed Logs**: Extensive logging capabilities to track the progress and status of crawling and scraping operations, including debugging and error information.

## Installation

Currently, this toolkit is available as a repository on GitHub. To use it, you need to clone the repository:

```bash
git clone https://github.com/speakleash/speakleash-forum-tools.git
cd speakleash-forum-tools
```

For testing create new virtual environment using:
```bash
python -m venv .venv
```

After that activate virtual environment:
```bash
# Linux
. .venv/bin/activate

# Windows
. .\.venv\Scripts\Activate.ps1
```

And install requirements:
```bash
pip install -r requirements.txt 
```

## Usage

> [!WARNING]
> Always check robots.txt and website/forum policies!

An example script (run_examples.py) is included in the repository to demonstrate how to use the library with various forum engines. You can run this script directly after cloning the repository:

```bash
python run_examples.py
```

If you want to use the tool in your code you can do so with a few lines:

```python
from speakleash_forum_tools import ForumToolsCore

if __name__ == "__main__":
    ForumToolsCore(dataset_url="http://www.excelforum.pl", forum_engine='phpbb')
```

> [!NOTE]  
> Keep in mind that some forums, even if they use predefined engines, may be defined differently - in which case the tool has some functionality built in to solve the problem. 

Here are some additional examples that may help you find a solution when testing in different forums:

```python
# Logging level - to find potential problems
ForumToolsCore(dataset_url="https://forum.modelarstwo.info", forum_engine='xenforo', log_lvl='DEBUG')

# Corresponding class for the pagination button
ForumToolsCore(dataset_url="https://forum.prawojazdy.com.pl/", forum_engine='phpbb', pagination = ["next"])

# Content of posts in another class && Different website encoding
ForumToolsCore(dataset_url = "https://www.excelforum.pl", forum_engine = 'phpbb',
                content_class = ["span >> class :: postbody"],
                web_encoding = 'iso-8859-2')

# Sleep for each thread - 0.5s and 4 threads
ForumToolsCore(dataset_url='https://max3d.pl/forums/', forum_engine='invision', time_sleep = 0.5, processes = 4)

```

> [!TIP]
> Please check the ForumToolsCore class documentation - all parameters should be described there.<br>
> Worth noting are, for example:

```python
ForumToolsCore(... , 
    processes: int = 4      # Creates 4 processes which scrape data
    sitemaps: str = "..."   # Path to the sitemaps website
    print_to_console: bool = True,  # If False, only the progress bar is displayed
)
```


## Archiving

The ArchiveManager class manages the creation and merging of data archives. It ensures that the scraped data is stored in an organized manner and supports the JSONL.ZST file format for efficient data handling.

## Manifest Management

The ManifestManager class generates a manifest file containing metadata about the dataset. This includes information such as project name, dataset name, description, license, and statistical details about the dataset content.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss your ideas.

