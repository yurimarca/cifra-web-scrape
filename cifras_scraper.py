from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

import xml.etree.ElementTree as ET

import langid
from langdetect import detect

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import time
import os
import csv
import logging
import random
import requests


def check_links():
    # Init list that will store all links from songs in sitemaps
    all_links = []

    # Number of songs-ith.xml files
    total_num_songs_sitemap = 25
    # Name of the folder where sitemap xml files are stored
    sitemap_folder = "sitemap/"

    for i in range(total_num_songs_sitemap):
        # Init name of the file iteratively
        sitemap_songfile = sitemap_folder + "songs-" + str(i+1) + ".xml"

        # Init xml parser
        tree = ET.parse(sitemap_songfile)
        root = tree.getroot()

        # Define the namespace
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Find all <loc> tags within the defined namespace
        loc_tags = root.findall('.//ns:loc', namespace)

        # Extract the text content of each <loc> tag (i.e., the links)
        #links = [loc.text for loc in loc_tags]

        links = [loc.text for loc in loc_tags if "/cifra/" in loc.text]

        # store the extracted links
        all_links += links

    return all_links


def scrape_web_title(url):
    try:
        # Send an HTTP GET
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get the title tag content
        title = soup.title.string if soup.title else None

        return title

    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return None


def scrape_cifra(url, logger=None):
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

    # Initialize driver using context manager
    with webdriver.Firefox(options=options, desired_capabilities=capabilities) as driver:
        try:
            # Get website information
            driver.get(url)

            # Explicitly wait for the pre element to be present
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "pre")))

            # Get page source and create BeautifulSoup object
            soup = BeautifulSoup(driver.page_source, "lxml")

            # Get cifra information
            cifrasoup = soup.find("pre")
            cifra_txt = cifrasoup.get_text() if cifrasoup else None

            # Get key of the song
            key_button = soup.find("button", class_="btn btn-icon icon-md")
            key = key_button.text.strip() if key_button else None

        except Exception as e:
            if logger is None:
                print(f"Scraping Error: {e}")
            else:
                logger.warning(f"\tScraping Error: {e}")
            return [None, None]

    return [cifra_txt, key]


def save_cifra_to_file(folder, cifra, cifra_artist, cifra_song):
    # Define artist folder name
    artist_folder = folder + "/" + cifra_artist
    # Create artist folder if not existent
    if not os.path.exists(artist_folder):
        os.makedirs(artist_folder)
        #print(f"Folder '{folder_path}' created successfully!")

    # Define cifra file name
    cifra_file_name = artist_folder + "/" + cifra_song + ".txt"
    with open(cifra_file_name, "w") as file:
        file.write(cifra)

    return cifra_file_name


def check_cifra_file_exists(folder,cifra_artist, cifra_song):
    # Define artist folder name
    artist_folder = folder + "/" + cifra_artist

    # Define cifra file name
    cifra_file_name = artist_folder + "/" + cifra_song + ".txt"

    # Check if file exists
    if os.path.exists(cifra_file_name):
        return True
    else:
        return False


def get_spotify_song_info(track_name, artist_name, idx=0, max_retries=3, retry_after=30, logger=None):
    # Spotify API credentials
    CLIENT_ID = ['092acd03f5ca40e0a3dd8259ecab98e7', 'b1733cfde9a842ad963fdcb10d8bb431',
                 '91b8acb66d8e4ad8a87b66e9f5cbffa9']
    CLIENT_SECRET = ['75c44b710561420aad7c7d5b1afad2ae', '9926ff3b33f74dd7adabecfc4a108db3',
                     '38fa815c7ace4340b0c863bf3da58929']

    for attempt in range(1, max_retries + 1):
        try:
            # Initialize Spotify API client
            client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID[idx], client_secret=CLIENT_SECRET[idx])
            sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

            # Search for the track
            results = sp.search(q=f'track:{track_name} artist:{artist_name}', type='track', limit=1)

            # Check if data was found
            if results['tracks']['items']:
                spotify_song_info = results['tracks']['items'][0]
                audio_features = sp.audio_features([spotify_song_info['id']])[0]

                return [spotify_song_info, audio_features]
            else:
                return [None, None]

        except spotipy.SpotifyException as e:
            if e.http_status == 429:  # Rate limit exceeded

                if logger is None:
                    print(f"\tSpotify rate limit exceeded. Waiting for {retry_after} secs (Attempt {attempt}/{max_retries}).")
                else:
                    logger.warning(f"\tRate limit exceeded. Waiting for {retry_after} secs (Attempt {attempt}/{max_retries}).")

                time.sleep(retry_after)
            else:
                if logger is None:
                    print(f"\tSpotify Request Error: {e}")
                else:
                    logger.warning(f"\tSpotify Request Error: {e}")
                return [None, None]

    if logger is None:
        print(f"\tMaximum retry attempts reached. Unable to get data from Spotify.")
    else:
        logger.warning(f"\tMaximum retry attempts reached. Unable to get data from Spotify.")

    return [None, None]

def add_song_to_csv(cifras_csv_file,
                    url_artist_name,
                    url_song_name,
                    cifra_file_location,
                    cifra_key,
                    spotify_song_info,
                    audio_features):

    # Init column names
    col_names = ["url_artist", "url_song", "cifra_file_loc", "cifra_key",
                 "spotify_artist", "spotify_song", "spotify_album", "spotify_popularity",
                 "release_date", "feature_danceability", "feature_energy", "feature_acousticness",
                 "feature_instrumentalness", "feature_key", "feature_liveness", "feature_mode",
                 "feature_speechiness", "feature_tempo", "feature_time_signature", "feature_valence",
                 "song_duration", "cifra_url", "spotify_url"]

    # Get spotify song information
    spotify_artist = ', '.join([artist['name'] for artist in spotify_song_info['artists']])
    spotify_song = spotify_song_info['name']
    spotify_album = spotify_song_info['album']['name']
    release_date = spotify_song_info['album']['release_date']
    spotify_popularity = spotify_song_info['popularity']
    spotify_url = spotify_song_info['external_urls']['spotify']

    # Get audio features from spotify
    feature_danceability = audio_features['danceability']
    feature_energy = audio_features['energy']
    feature_acousticness = audio_features['acousticness']
    song_duration = audio_features['duration_ms']
    feature_instrumentalness = audio_features['instrumentalness']
    feature_key = audio_features['key']
    feature_liveness = audio_features['liveness']
    feature_mode = audio_features['mode']
    feature_speechiness = audio_features['speechiness']
    feature_tempo = audio_features['tempo']
    feature_time_signature = audio_features['time_signature']
    feature_valence = audio_features['valence']

    # Init row to be added to the csv
    row = [url_artist_name, url_song_name, cifra_file_location, cifra_key,
           spotify_artist, spotify_song, spotify_album, spotify_popularity,
           release_date, feature_danceability, feature_energy, feature_acousticness,
           feature_instrumentalness, feature_key, feature_liveness, feature_mode,
           feature_speechiness, feature_tempo, feature_time_signature, feature_valence,
           song_duration, cifra_url, spotify_url]

    with open(cifras_csv_file, "a", newline="") as csvfile:
        # Create a CSV writer object
        writer = csv.writer(csvfile)

        # Write the column names only if the file is empty
        if os.stat(cifras_csv_file).st_size == 0:
            writer.writerow(col_names)

        # Add new row
        writer.writerow(row)

    return


def check_free_space():
    home_folder = os.path.expanduser("~")
    statvfs = os.statvfs(home_folder)
    free_space_bytes = statvfs.f_bavail * statvfs.f_frsize
    free_space_gb = free_space_bytes / (1024 * 1024 * 1024)
    return free_space_gb


def is_portuguese(text):
    lang1, _ = langid.classify(text)
    lang2 = detect(text)
    return (lang1 == 'pt') or (lang2 == 'pt')


def check_pt_title(url, logger=None):
    web_title = scrape_web_title(url)

    if web_title is None:
        logger.debug(f"\t Couldn't retrieve song web title.")
        return False
    else:
        song_title = web_title.split(" | ")[0]
        is_pt = is_portuguese(song_title)

        logger.debug(f"\t Song web title: {song_title}, BR={is_pt}")

        return is_pt


if __name__ == "__main__":
    """
    Loop over all cifras available according to the cifras.com.br sitemap
        Check if the cifra is of interest:
        ###- Brazilian or English song
        - There is information about it in Spotify
        If so:
            Retrieve cifra and its main key from cifras.com.br
            ###Transform the chords notation to a standard format using roman number taking the main key as root note
            Store cifra in a file
            Store the audio features and song information from spotify in a csv along the location of the saved file

    PS. It would be reasonable to limit the amount of data stored.
    PS2. Perhaps it will be necessary to do a IP pooling, but let's test first with an interval between requests.
    """

    restart_from = 22218

    # Init logging
    logger = logging.getLogger(__name__)

    # Set the logging level
    logger.setLevel(logging.DEBUG)

    # Define a custom formatter to include milliseconds
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s: \t %(message)s',
                                  '%H:%M:%S')

    # Create a file handler for logging to a file
    file_handler = logging.FileHandler('cifras_scraper.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create a stream handler for logging to the console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Dataset variables definitions
    cifras_folder = "cifras"
    cifras_csv_file = "cifras.csv"

    # Create folder if it does not exist
    if not os.path.exists(cifras_folder):
        os.makedirs(cifras_folder)
        logger.debug(f"Folder to store cifras created named: {cifras_folder}")
    else:
        logger.debug(f"Folder to store cifras already exists! Folder name: {cifras_folder}")

    # Get all cifras available in cifras.com.br
    all_links = check_links()
    logger.info(f"Number of song URLs available: {len(all_links)}")

    # Init auxiliary counters for loop
    count = 1
    found_cifras_count = 0
    spotify_request_count = 0

    # Init time auxiliary variable to guarantee an interval between requests
    cifra_scrape_time = time.time()
    spotify_request_time = time.time()

    # Define request interval
    spotify_request_interval = 5
    cifra_scrape_interval = 10

    # Loop over all cifras
    for cifra_url in all_links:
        if count > restart_from:
            logger.info(f"Cifra URL #{count}: {cifra_url}")

            # Get cifra's artists name and song title from link text
            cifra_title = cifra_url[32:]

            # Get artist name and song title
            cifra_artist, cifra_song = cifra_title.split("/")
            artist = " ".join(cifra_artist.split("-"))
            logger.info(f"\tArtist: {artist}")
            song = " ".join(cifra_song.split("-"))
            logger.info(f"\tSong: {song}")

            # Check if information was already obtained
            if check_cifra_file_exists(cifras_folder, cifra_artist, cifra_song):
                logger.info(f"\tSong was already scraped and saved!")
                found_cifras_count += 1
            else:
                # Check if it is Portuguse/BR song by its title
                if check_pt_title(cifra_url, logger=logger):

                    # Check if there is information available in Spotify
                    [spotify_song_info, audio_features] = get_spotify_song_info(song, artist, idx=spotify_request_count%3, logger=logger)

                    # Put to sleep to respect spotify request interval
                    interval = time.time() - spotify_request_time
                    if interval < spotify_request_interval:
                        wait_interval = spotify_request_interval - interval
                        logger.debug(f"\tWait interval of {wait_interval} secs for spotify request.")
                        time.sleep(wait_interval)
                    spotify_request_time = time.time()

                    spotify_request_count += 1

                    if spotify_song_info:
                        logger.info(f"\tSpotify data fount! URL: {spotify_song_info['external_urls']['spotify']}")

                        # Scrape cifra
                        [cifra_txt, cifra_key] = scrape_cifra(cifra_url, logger=logger)
                        if cifra_txt is None:
                            logger.warning(f"\tSCRAPE ERROR! Cifra was not retrieved!!!")

                            # Save empty cifra to avoid trying to scrape it again next time
                            save_cifra_to_file(cifras_folder, "", cifra_artist, cifra_song)

                        else:
                            found_cifras_count += 1
                            logger.info(f"\tCifra #{found_cifras_count} retrieved! Key: {cifra_key}")

                            # Save cifra to file
                            cifra_file_location = save_cifra_to_file(cifras_folder, cifra_txt, cifra_artist, cifra_song)
                            logger.info(f"\tCifra stored at: {cifra_file_location}")

                            # Add song info to csv
                            add_song_to_csv(cifras_csv_file, artist, song, cifra_file_location, cifra_key,
                                            spotify_song_info, audio_features)

                            # Put to sleep to respect cifras.com.br scrape interval of 10secs
                            interval = time.time() - cifra_scrape_time
                            if interval < cifra_scrape_interval:
                                wait_interval = cifra_scrape_interval - interval
                                logger.debug(f"\tWait interval of {wait_interval} secs for cifra scrape.")
                                time.sleep(wait_interval)
                            cifra_scrape_time = time.time()
                    else:
                        logger.info("\tSpotify data not found!")
                else:
                    logger.info("\tSong is not Portuguese/BR!!!!")

            # Check if there is free enough space
            free_space_gb = check_free_space()
            if free_space_gb < 2:
                logger.warning("\tStop scraper due to high disk space usage!")
                logger.debug("\tFree disk space: {free_space_gb:.2f} GB")
                break

            if count % 100 == 0:
                logger.debug("-------------------------------------------------------------")
                logger.debug(
                    f"Number of songs found: {found_cifras_count}, representing {(100 * found_cifras_count / count):.2f}%")
                logger.debug(f"\tFree disk space: {free_space_gb:.2f} GB")
                logger.debug("-------------------------------------------------------------")

        count += 1

    logger.info(f"Number of songs found: {found_cifras_count}, representing {(100*found_cifras_count/count):.2f}%")
