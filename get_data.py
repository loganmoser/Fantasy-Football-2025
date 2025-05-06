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
        add_request()

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

def get_player(player, header_row):
    try:
        global counter
        # To track requests and comply with rate limits
        # Check for players directory if not present -- create it
        check_dir(f'players/{player}')
        # Each player has a unique url for their stats page made up of /first letter of last name /first four of last name first two of first name00
        first_name = player.split(' ')[0].strip('.')
        last_name = player.split(' ')[1]
        # Some players have names like Amon-Ra St. Brown and need different formatting
        if "." in last_name:
            last_name = last_name.split('.')[0]
            last_name = last_name+'xx'
        combo_num = "00" # This represents the players that have the combination of last_name[0]/last_name[:4]first_name[:2] if there are more than 1 we'll need to make sure most recent season is 2024
        player_base_url = f"https://www.pro-football-reference.com/players/{last_name[0].upper()}/{last_name[:4]}{first_name[:2]}{combo_num}"
        player_url = f"{player_base_url}.htm"
        # Create career data frame for analysis Qbs do not have distinctions between rushing and receiving stats so their tables are different
        career_list = pd.read_html(io=player_url, header=header_row)
        career_df = career_list[0]
        # If season not in columns we do not have the correct header_row
        while 'Season' not in career_df.columns:
            combo_num = str(int(combo_num) + 1).zfill(2)
            player_base_url = f"https://www.pro-football-reference.com/players/{last_name[0].upper()}/{last_name[:4]}{first_name[:2]}{combo_num}"
            player_url = f"{player_base_url}.htm"

            career_list = pd.read_html(io=player_url, header=header_row)

            add_request()

            career_df = career_list[0]

        # Get individual seasons for time-based trend analysis
        seasons = [int(season) for season in career_df['Season'] if str(season).strip().isdigit()]

        while seasons[-1] != 2024:
            combo_num = str(int(combo_num) + 1).zfill(2)
            player_base_url = f"https://www.pro-football-reference.com/players/{last_name[0].upper()}/{last_name[:4]}{first_name[:2]}{combo_num}"
            player_url = f"{player_base_url}.htm"

            career_list = pd.read_html(io=player_url, header=header_row)

            add_request()

            career_df = career_list[0]

            # Get individual seasons for time-based trend analysis
            seasons = [int(season) for season in career_df['Season'] if str(season).strip().isdigit()]

        career_df.set_index('Season', drop=False)
        career_df.to_csv(f'data/players/{player}/{player}_career.csv')

        # We need to stay under 10 requests a minute
        add_request()

        # Get individual seasons for time-based trend analysis
        seasons = [int(season) for season in career_df['Season'] if str(season).strip().isdigit()]

        for season in seasons:
            season_csv = f'data/players/{player}/{player}_{season}.csv'
            if Path(season_csv).exists():
                print(f"{player}_{season}.csv already exists. Continuing...")
                continue
            print(f"Fetching data for {player}'s season in {season}")
            season_url = f"{player_base_url}/gamelog/{season}"
            season_df = pd.read_html(io=season_url, header=1)[0]
            
            add_request()

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
positions = top_performers['FantPos']

for player, position in zip(players,positions):
    if position == 'QB':
        get_player(player, 0)
    else:
        get_player(player, 1)
