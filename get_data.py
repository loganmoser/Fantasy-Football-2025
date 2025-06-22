from bs4 import BeautifulSoup
import requests
import pandas as pd
import os
from pathlib import Path
import time

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


def get_top_performers(season):
    try:
        global counter
        # Check for the directory and if it does not exist create it
        check_dir('seasons')
        # By passing in unique seasons we can quickly get the url
        url = f"https://www.pro-football-reference.com/years/{season}/fantasy.htm" 
        # Pandas implementation using read_html we can get the 2025 season and skip the first row for headers
        print(f"Fetching data for {season} season...")

        # Getting the best players from the particular season
        response = requests.get(url)
        response.raise_for_status()
        # After making a request we need to make sure we are within site rules
        add_request()
        soup = BeautifulSoup(response.text, 'lxml')
        links = soup.find_all('a') # all links

        players_links = [link.get('href') for link in links if '/players' in link.get('href')]
        top_players = players_links[:200] #top 200 players per season - 10 teams x 16 players on the roster plus some extra rankings
        return top_players
        
    except Exception as e:
        print(f"Error getting top players from the {season} season: {str(e)}")
        return False


#If the 2025 fantasy rankings don't already exist - get them
players = []
for i in range(2024, 2019, -1):
    players += get_top_performers(i)

top_players = set(players)

print(top_players)

#Getting player info from the most recent season, going through the top 100 and getting career stats 
#ff24_df = pd.read_csv('data/seasons/2024_fantasy.csv')

# We only want top 200 performs and skip unnamed 0 column
#top_performers = ff24_df.iloc[:200, 1:]

#players = top_performers['Player']
#positions = top_performers['FantPos']

