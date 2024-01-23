from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup

import xml.etree.ElementTree as ET

import logging
import random
import csv

def get_genres_urls(sitemap_folder="sitemap"):
    sitemap_genres = sitemap_folder + "/genres-1.xml"

    tree = ET.parse(sitemap_genres)
    root = tree.getroot()

    # Define the namespace
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    # Find all <loc> tags within the defined namespace
    loc_tags = root.findall('.//ns:loc', namespace)

    # Extract the text content of each <loc> tag (i.e., the links)
    links = [loc.text for loc in loc_tags]

    return links


def get_genre_num_pages(url):
    max_pages = 1
    try:
        options = Options()
        options.add_argument("--headless")

        driver = webdriver.Firefox(options=options)

        driver.get(url)
        driver.implicitly_wait(10)

        soup = BeautifulSoup(driver.page_source, "lxml")

        cifrasoup = soup.find(class_="pagination")

        if cifrasoup:
            for pages in cifrasoup.find_all('li'):
                i_page = pages.find('a', class_='page-link')
                if i_page:
                    i_page = i_page.text.strip()
                    max_pages = int(i_page) if i_page.isnumeric() else max_pages

        driver.quit()

    except Exception as e:
        print(f"Scraping Error!!!!")
        print(e)
        return None

    return max_pages


def scrape_cifra_genre(url):

    # List of user-agents
    user_agent_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.0.0",
        "Mozilla/5.0 (Linux; Android 11; Pixel 4a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (iPad; CPU OS 15_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
    ]

    # Initialize options and capabilities
    options = Options()
    options.add_argument("--headless")

    capabilities = DesiredCapabilities.FIREFOX
    capabilities["pageLoadStrategy"] = "eager"
    options.add_argument(f"user-agent={random.choice(user_agent_list)}")

    try:
        options = Options()
        options.add_argument("--headless")

        driver = webdriver.Firefox(options=options, desired_capabilities=capabilities)

        driver.get(url)
        driver.implicitly_wait(10)

        soup = BeautifulSoup(driver.page_source, "lxml")

        cifrasoup = soup.find(class_="all-artists-list__content")

        artists = []
        for artist_element in cifrasoup.find_all('a'):
            artist_name = artist_element.find('div', class_='artist-name').text.strip()
            artist_href = artist_element['href']  # Corrected this line
            artists.append([artist_name, artist_href[1:]])

        driver.quit()

    except Exception as e:
        print(f"Scraping Error!!!!")
        print(e)
        return "ERROR!!"
    finally:
        return artists


def save_artist_genres_to_file(file, artists, genre):
    with open(file, 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        for a in artists:
            csv_writer.writerow([genre] + a)


if __name__ == "__main__":
    """
    Loop over all genres URLs
    """

    # Init logging
    logger = logging.getLogger(__name__)

    # Set the logging level
    logger.setLevel(logging.DEBUG)

    # Define a custom formatter to include milliseconds
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s: \t %(message)s',
                                  '%H:%M:%S')

    # Create a file handler for logging to a file
    file_handler = logging.FileHandler('genres_scraper.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create a stream handler for logging to the console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    genres_urls = get_genres_urls()

    file = "artist_genres.csv"

    for url in genres_urls:
        genre=url[33:]
        logger.info(f"Genre = {genre}")
        logger.info(f"\t Genre URL = {url}")
        num_pages = get_genre_num_pages(url)
        num_pages = num_pages if not None else 1
        logger.info(f"\t Number of pages for = {num_pages}")

        count_artists = 0
        for i in range(num_pages):
            i += 1
            page_url = url + "?page=" + str(i) if i > 1 else url
            artists = scrape_cifra_genre(page_url)
            #logger.debug(f"{artists}")
            logger.debug(f"\t{len(artists)} newly added artists!")
            count_artists += len(artists)
            save_artist_genres_to_file(file, artists, genre)
        logger.info(f"\t Number of artists = {count_artists}")
