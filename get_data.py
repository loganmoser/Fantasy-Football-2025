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
        add_request()
        #TODO Get Position
        #If quarterback - use headers = 0 else headers = 1
        info_box = browser.find_element(By.ID, 'meta')
        media_text = info_box.find_elements(By.CSS_SELECTOR, 'p')
        if 'QB' in media_text:
            headers = 0
        else:
            headers = 1
        #TODO Get years played
        career = pd.read_html(io=link, header=headers)
        add_request()
        career_df = career[0]
        seasons = pd.to_numeric(career_df['Season'], errors='coerce').dropna().astype(int).tolist()
        #TODO Get Game-log links
        a_tags = browser.find_elements(By.TAG_NAME, 'a')
        season_tags = [a for a in a_tags if a.text.isdigit()]
        season_links = [season.get_attribute('href') for season in season_tags if pd.to_numeric(season.text) in seasons] #Get links that contain a year
        season_links = set([season for season in season_links if '/gamelog' in season and '/advanced/' not in season])
        print(season_links)
        #Dropping unneeded rows from df
        filtered_df = career_df[career_df['Season'].astype(str).isin(str(s) for s in seasons)] # convert the df columns and int from list to get str seasons
        #Getting player name for file name
        player_name = info_box.find_element(By.CSS_SELECTOR, 'span').text
        #Make player folder
        # player_folder = f'players/{player_name}'
        # check_dir(player_folder)

    except Exception as e:
        print(f"Error getting career data from {link}...: {str(e)}")


# If the 2025 fantasy rankings don't already exist - get them
players = []
options = webdriver.FirefoxOptions()
options.add_argument("-headless")

#Allow user to decide whether to get new data or just search for player data
user_input = input('Do you want to get new player info? (y/N): ')
if user_input.lower() == 'y':
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
    # Turning top players to a list and saving the file
    link_df = pd.DataFrame(list(top_players), columns=['Player_Link'])
    link_df.to_csv('data/player_links.csv')

link_df = pd.read_csv('data/player_links.csv')

driver = webdriver.Firefox(options=options)
for link in link_df['Player_Link']:
    get_career(link, driver)
    break
driver.close()

