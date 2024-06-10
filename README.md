# Cifra (Music Notation) Data Science Project

Cifras are popular music sheets for guitar players to learn songs. In Brazil, there are online forums where users share cifras of popular songs. We looked at [cifras.com.br](https://www.cifras.com.br/) and scraped some cifras from their forum following the web crawler time request delay [robots.txt](https://www.cifras.com.br/robots.txt). 
**DISCLAIMER: scraped cifras have been collected solely for the purpose of personal research and self-study; the data will not be used for any commercial activities or purposes.**

This repository aims to showcase a complete data science project from data collection, cleaning, and filtering to data analysis and insights. The goal is to scrape from the web and analyze cifras to uncover patterns and insights that can assist musicians, especially DIY guitar players, in understanding the mechanics of popular songs, such as common chord progressions, popular keys, and song structures.

## Repository Structure

All steps in the sequence where developed using Python and running Jupyter Notebooks to conceptualize the solution. 

### Data Collection

- Notebook `cifra-web-scrape-study.ipynb` presents the steps we produced to retrieve cifras from  [cifras.com.br](https://www.cifras.com.br/) using Python libraries **selenium** for accessing JavaScript generated website, and **BeautifulSoup** for parsing HTML and extracting data. Following that, we run script `cifras_scraper.py` to scrape cifras automatically while logging and filtering only Brazilian songs. 

- Notebook `cifras-data-availability.ipynb` show our study to retrieve information about artists' music genres, and script `genre_scraper.py` runs the code to scrape music genres.

After collecting the data

### Data Cleaning and Preprocessing

- Notebook `data-consolidation.ipynb` parses the scraped data into a consolidated format, saving the result in CSV file. Handling missing values, duplicates, and inconsistencies in the data 

### Exploratory Data Analysis (EDA)


### Feature Engineering


### Data Analysis


