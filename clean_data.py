import pandas as pd
from pathlib import Path


# list player directoriesin data dir
data = Path('data/')
players = data / 'players'
player_dirs = [player for player in players.iterdir()]

for player in player_dirs:
    # Get file paths for each file in the player directory
    player_files = [file for file in player.iterdir()]
    
    #Iterate through each file and clean
    for file in player_files:
        df = pd.read_csv(file)
        print(df.head())

    break

