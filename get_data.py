from bs4 import BeautifulSoup
import requests
import pandas as pd
import os
from pathlib import Path
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

counter = 0

def add_request():
    global counter
    counter += 1
    if counter % 10 == 0:
        print("10 requests reached. Stopping for 60 seconds...")
        time.sleep(60)

# If seasons or player subdirectory does not exist create it
def check_dir(subdir):
    dir_path = Path(f"data/{subdir}/")
    if not dir_path.is_dir():
        print(f"Directory 'data/{subdir}' does not exist")
        print(f"Creating 'data/{subdir}'...")
        Path.mkdir(dir_path)

def get_fantasy_season(season):
    global counter
    # Check for the directory and if it does not exist create it
    check_dir('seasons')
    url = f"https://www.pro-football-reference.com/years/{season}/fantasy.htm"
    print(f"Fetching {season} fantasy data...")
    try:
        curr_season = pd.read_html(io=url, header=1)
        # After making a request we need to make sure we are within site rules
        add_request()

        season_df = curr_season[0]
        season_df.set_index('Rk', drop=False)
        #Data cleaning to clean up player names and drop headers
        # Every 31 lines the headers of the file reappear so we need to drop these rows where Rk = Rk
        season_df = season_df.drop(season_df[season_df['Rk'] == 'Rk'].index)
        season_df['Player'] = season_df['Player'].str.strip('*+')

        # Saving 2025 season for future use
        file_path = os.path.abspath(os.path.join(os.getcwd(), f"data/seasons/{season}_fantasy.csv"))
        print(f"Attempting to save to: {file_path}")
        season_df.to_csv(file_path)
    except Exception as e:
        print(f"Error processing {season} season: {str(e)}")
        return False

def get_top_performers(season, browser):
    try:
        global counter
        # By passing in unique seasons we can quickly get the url
        url = f"https://www.pro-football-reference.com/years/{season}/fantasy.htm" 
        # Pandas implementation using read_html we can get the 2025 season and skip the first row for headers
        print(f"Fetching top players from {season}...")

        browser.get(url)
        add_request()
        time.sleep(2)
        # Filter out non-player hrefs
        links = browser.find_elements(By.TAG_NAME, 'a')
        player_links = [link.get_attribute('href') for link in links if '/players' in str(link.get_attribute('href'))]
        best_players = player_links[:200] #top 200 players per season - 10 teams x 16 players on the roster plus some extra rankings
        return best_players
        
    except Exception as e:
        print(f"Error getting top players from the {season} season: {str(e)}")
        return False

def get_career(link, browser):
    try:
        browser.get(link)
        player_info = browser.find_element(By.ID, 'info')
        #Getting player name for file name
        player_name = player_info.find_element(By.CSS_SELECTOR, 'span').text
        #TODO Get years played

    except Exception as e:
        print(f"Error getting career data from {link}...: {str(e)}")


#If the 2025 fantasy rankings don't already exist - get them
players = []
options = webdriver.FirefoxOptions()
options.add_argument("-headless")
driver = webdriver.Firefox(options=options)
for i in range(2024, 2019, -1):
    players += get_top_performers(i, driver)
    file_path = Path(f'data/seasons/{i}_fantasy.csv')
    if Path.is_file(file_path):
        print(f'There is already data for the {i} season...')
        continue
    else:
        get_fantasy_season(i)
driver.close()
top_players = set(players)

print(top_players)

# Turning top players to a list and saving the file
link_df = pd.DataFrame(list(top_players), columns=['Player_Link'])
link_df.to_csv('data/player_links.csv')

driver = webdriver.Firefox(options=options)
for link in link_df['Player_Link']:
    get_career(link, driver)
    break
driver.close()

