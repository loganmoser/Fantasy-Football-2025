import requests
import pandas as pd
import os
from pathlib import Path

# If seasons or player subdirectory does not exist create it
def check_dir(subdir):
    if not os.path.isdir(os.path.join(os.getcwd(), f"data/{subdir}/")):
        print(f"Directory 'data/{subdir}' does not exist")
        print(f"Creating 'data/{subdir}'...")
        os.mkdir(os.path.abspath(os.path.join(os.getcwd(), f"data/{subdir}/")))


def get_season(season):
    try:
        # Check for the directory and if it does not exist create it
        check_dir('seasons')
        # By passing in unique seasons we can quickly get the url
        url = f"https://www.pro-football-reference.com/years/{season}/fantasy.htm" 
        # Pandas implementation using read_html we can get the 2025 season and skip the first row for headers
        print(f"Fetching data for {season} season...")
        curr_season = pd.read_html(io=url, header=1)
        season_df = curr_season[0]
        
        #Data cleaning to clean up player names and drop headers
        # Every 31 lines the headers of the file reappear so we need to drop these rows where Rk = Rk
        season_df = season_df.drop(season_df[season_df['Rk'] == 'Rk'].index)

        players = season_df['Player']
        pro_bowl = [1 if "*" in player else 0  for player in players]
        all_pro = [1 if "+" in player else 0 for player in players]
        season_df['Pro_bowl'] = pro_bowl
        season_df['All_pro'] = all_pro
        season_df['Player'] = season_df['Player'].str.strip('\*+')
        

        # Saving 2025 season for future use
        file_path = os.path.abspath(os.path.join(os.getcwd(), f"data/seasons/{season}_fantasy.csv"))
        print(f"Attempting to save to: {file_path}")
        season_df.to_csv(file_path)
    except Exception as e:
        print(f"Error processing {season} season: {str(e)}")
        return False

def get_player(player):
    try:
        check_dir('players')
    except Exception as e:
        print(f"Error processing {player}: {str(e)}")
        return False

#If the 2025 fantasy rankings don't already exist - get them
for i in range(2024, 2019, -1):
    if os.path.isfile(os.path.join(os.getcwd(), f"data/seasons/{i}_fantasy.csv")):
        user_input = input(f"Data for the {i} season already exists do you want to replace it? Y/n: ")
        if (user_input == 'n'):
            continue
        elif (user_input == '' or user_input.toUpper() == 'Y'):
            get_season(i)
    else:
        get_season(i)

#Getting player info from the most recent season, going through the top 100 and getting career stats 
ff24_df = pd.read_csv('data/seasons/2024_fantasy.csv')

