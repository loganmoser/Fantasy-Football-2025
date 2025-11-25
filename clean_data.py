import pandas as pd
from pathlib import Path
from sklearn.preprocessing import LabelEncoder

# Set display option to show all columns
pd.set_option('display.max_columns', None)

def get_position(career: pd.DataFrame) -> str:
    positions = list(set(career['Pos'].dropna()))[0]
    return positions

def get_year(season: pd.DataFrame) -> int:
    year = pd.to_datetime(season['Date'])[0].year
    return year

def rename_columns(season: pd.DataFrame, position: str) -> None:
    """Renaming passing and rushing columns so they are more easily distinguished"""
    if position == 'WR':
        season.rename(columns={'Yds': 'Recieving Yards', 'TD': 'Receiving TD', 'Yds.1': 'Rushing Yards', 'TD.1': 'Rushing TD'}, inplace=True)

def home_or_away_game(season: pd.DataFrame) -> None:
    """
    This method will replace the unnamed 6 column with a 1 if the game was away and 0 if it was a home game
    :param season:
    :return:
    """
    df['Unnamed: 6'] = [1 if game == '@' else 0 for game in season['Unnamed: 6']]
    df.rename(columns={'Unnamed: 6': 'Home or Away'}, inplace=True)

def did_start(season: pd.DataFrame) -> None:
    """
    This method will take in a df and encode the GS (game started) column for ML use
    :param season: a dataframe for a season
    :return:
    """
    df['GS'] = [1 if game == '*' else 0 for game in season['GS']]

def drop_columns(season: pd.DataFrame) -> pd.DataFrame:
    """
    Dropping unwanted or unuseful columns like defensive stats
    """
    season = season[:-1] # remove the last row
    season = season.drop(columns=['Unnamed: 0', 'Week', 'DefSnp', 'Def%', 'STSnp', 'ST%'], axis=1) # There are no defensive players that we are scoring
    return season

def encode_categories(season: pd.DataFrame) -> None:
    """Use the label encoder to transform categorical variables.
    """
    season['Team'] = le.transform(season['Team'])
    season['Opp'] = le.transform(season['Opp'])

def calculate_fantasy_points(season: pd.DataFrame) -> None:
    """According to PPR scoring rules create a field for the points scored in this game
    Passing: Yds.1
    """


# list player directories in data dir
data = Path('data/')
players = data / 'players'
player_dirs = [player for player in players.iterdir() if player.is_dir()]

# Encode Team values
teams = ['TEN', 'CLE', 'IND', 'JAX','ATL', 'BUF', 'DEN', 'LAC', 'TAM', 'CAR', 'KAN', 'OAK', 'HOU', 'NOR',
         'NWE' 'MIA', 'NYJ', 'BAL', 'PIT', 'CIN', 'LVR','PHI', 'DAL', 'WSH', 'NYG', 'CHI', 'GNB', 'DET', 'MIN'
         'LAR', 'SEA', 'SFO', 'ARI']

le = LabelEncoder()

le.fit(teams)

# iterate through players and create ML ready data
for player in player_dirs:
    player_name = str(player).split('\\')[-1] # Get Player name to append to data
    # Get file paths for each file in the player directory
    player_files = [file for file in player.iterdir()]

    # Get player position
    career_df = pd.read_csv(player_files[0])
    position = get_position(career_df)

    player_files.pop(0)
    #Iterate through each file and clean
    for file in player_files:
        df = pd.read_csv(file)

        # Make certain columns more machine learning friendly
        home_or_away_game(df)
        did_start(df)
        df = drop_columns(df)
        rename_columns(df, position)
        season = get_year(df)
        encode_categories(df)
        print(df.head())
        break

    break
