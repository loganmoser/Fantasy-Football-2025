import requests
import pandas as pd
import os
from pathlib import Path
import time

counter = 0

# If seasons or player subdirectory does not exist create it
def check_dir(subdir):
    dir_path = Path(f"data/{subdir}/")
    if not dir_path.is_dir():
        print(f"Directory 'data/{subdir}' does not exist")
        print(f"Creating 'data/{subdir}'...")
        Path.mkdir(dir_path)


def get_season(season):
    try:
        global counter
        # Check for the directory and if it does not exist create it
        check_dir('seasons')
        # By passing in unique seasons we can quickly get the url
        url = f"https://www.pro-football-reference.com/years/{season}/fantasy.htm" 
        # Pandas implementation using read_html we can get the 2025 season and skip the first row for headers
        print(f"Fetching data for {season} season...")
        curr_season = pd.read_html(io=url, header=1)
        # After making a request we need to make sure we are within site rules
        counter += 1
        if counter % 10 == 0:
            print("10 requests reached. Stopping for 60 seconds...")
            time.sleep(60)

        season_df = curr_season[0]
        season_df.set_index('Rk', drop=False)
        #Data cleaning to clean up player names and drop headers
        # Every 31 lines the headers of the file reappear so we need to drop these rows where Rk = Rk
        season_df = season_df.drop(season_df[season_df['Rk'] == 'Rk'].index)

        players = season_df['Player']
        pro_bowl = [1 if "*" in player else 0  for player in players]
        all_pro = [1 if "+" in player else 0 for player in players]
        season_df['Pro_bowl'] = pro_bowl
        season_df['All_pro'] = all_pro
        season_df['Player'] = season_df['Player'].str.strip('*+')
        
        # Saving 2025 season for future use
        file_path = os.path.abspath(os.path.join(os.getcwd(), f"data/seasons/{season}_fantasy.csv"))
        print(f"Attempting to save to: {file_path}")
        season_df.to_csv(file_path)
    except Exception as e:
        print(f"Error processing {season} season: {str(e)}")
        return False

def get_player(player):
    try:
        global counter
        # To track requests and comply with rate limits
        # Check for players directory if not present -- create it
        check_dir(f'players/{player}')
        # Each player has a unique url for their stats page made up of /first letter of last name /first four of last name first two of first name00
        first_name = player.split(' ')[0]
        last_name = player.split(' ')[1]
        player_base_url = f"https://www.pro-football-reference.com/players/{last_name[0].upper()}/{last_name[:4]}{first_name[:2]}00"
        player_url = f"{player_base_url}.htm"
        # Create career data frame for analysis
        career_list = pd.read_html(io=player_url, header=1)
        career_df = career_list[0]
        career_df.set_index('Season', drop=False)
        career_df.to_csv(f'data/players/{player}/{player}_career.csv')

        # We need to stay under 10 requests a minute
        counter += 1
        if counter % 10 == 0:
            print("10 requests reached. Stopping for 60 seconds...")
            time.sleep(60)

        # Get individual seasons for time-based trend analysis
        seasons = [int(season) for season in career_df['Season'] if str(season).strip().isdigit()]
        for season in seasons:
            print(f"Fetching data for {player}'s season in {year}")
            season_url = f"{player_base_url}/gamelog/{season}"
            season_df = pd.read_html(io=season_url, header=1)[0]
            
            counter += 1
            if counter % 10 == 0:
                print("10 requests reached. Stopping for 60 seconds...")
                time.sleep(60)
            
            season_df.to_csv(f'data/players/{player}/{player}_{season}.csv')
    except Exception as e:
        print(f"Error processing {player}: {str(e)}")
        return False

#If the 2025 fantasy rankings don't already exist - get them
for i in range(2024, 2019, -1):
  if Path(f"data/seasons/{i}_fantasy.csv").exists():
      print(f'Data for the {i} season already exists. Continuing to the next season...')
      continue
  else:
      get_season(i)

#Getting player info from the most recent season, going through the top 100 and getting career stats 
ff24_df = pd.read_csv('data/seasons/2024_fantasy.csv')

# We only want top 200 performs and skip unnamed 0 column
top_performers = ff24_df.iloc[:200, 1:]

players = top_performers['Player']

for player in players:
    if Path(f"data/players/{player}").exists():
        print(f'Data for {player} already exists. Continuing to the next player...')
        continue
    else:
        get_player(player)
