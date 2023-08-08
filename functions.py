import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from random import sample
from gspread_dataframe import set_with_dataframe
import gspread
from google.oauth2 import service_account
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import matplotlib.pyplot as plt
import altair as alt
from placeholder_events import *
import requests
from configs import *


#'''------------------------------------------------------------CACHE FUNCTIONS------------------------------------------------------------'''

# function to create api connection to google sheets
@st.cache_resource(max_entries = 1,)
def connect_to_gs(_service_account_key):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = service_account.Credentials.from_service_account_info(_service_account_key, scopes=scopes)
    gs_connection = gspread.authorize(credentials)
    return gs_connection


# function to fetch gw data from google sheets
@st.cache_data(ttl='6h',max_entries = 1,)
def fetch_gameweek_data(_gc, sheet_name, sheet_key, columns_list):
    try:
        # Open specific sheet
        gs = _gc.open_by_key(sheet_key)

        # Open specific tab within the sheet
        tab = gs.worksheet(sheet_name)

        data = tab.get_all_values()
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)

        # to handle numeric columns that are imported as strings
        for column in columns_list:
            df[column] = pd.to_numeric(df[column])

        return df

    except gspread.exceptions.APIError as e:
        print("Error accessing Google Sheets API:", e)
        return None
    except gspread.exceptions.WorksheetNotFound as e:
        print("Error: Worksheet not found:", e)
        return None
    except Exception as e:
        print("An error occurred:", e)
        return None


# function to fetch drinks data from google sheets
@st.cache_data(ttl='6h', max_entries = 1,)
def fetch_drinks_data(_gc, sheet_name, sheet_key, columns_list):
    try:
        # Open specific sheet
        gs = _gc.open_by_key(sheet_key)

        # Open specific tab within the sheet
        tab = gs.worksheet(sheet_name)

        data = tab.get_all_values()
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)

        # to handle numeric columns that are imported as strings
        for column in columns_list:
            df[column] = pd.to_numeric(df[column])

        return df

    except gspread.exceptions.APIError as e:
        print("Error accessing Google Sheets API:", e)
        return None
    except gspread.exceptions.WorksheetNotFound as e:
        print("Error: Worksheet not found:", e)
        return None
    except Exception as e:
        print("An error occurred:", e)
        return None

#build drinks display table
@st.cache_data(ttl='6h', max_entries = 1,)
def build_drinks_display(drinks, current_week):
    drinks_display = drinks[drinks.event > current_week - 2]
    drinks_display = drinks_display.iloc[:, [0, 2, 3, 5, 6]]
    drinks_display.rename(
        columns={
            "event": "Game Week",
            "drinker_name": "Name",
            "drink_type": "Drink Type",
            "nomination_deadline_date": "Deadline",
            "nomination_completed_date": "Completed Date",
        },
        inplace=True,
        )
    return drinks_display


# function to fetch managers from google sheets
@st.cache_data(ttl='6h', max_entries = 1,)
def fetch_manager_data(_gc, sheet_name, sheet_key, columns_list):
    try:
        # Open specific sheet
        gs = _gc.open_by_key(sheet_key)

        # Open specific tab within the sheet
        tab = gs.worksheet(sheet_name)

        data = tab.get_all_values()
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)

        # to handle numeric columns that are imported as strings
        for column in columns_list:
            df[column] = pd.to_numeric(df[column])

        return df

    except gspread.exceptions.APIError as e:
        print("Error accessing Google Sheets API:", e)
        return None
    except gspread.exceptions.WorksheetNotFound as e:
        print("Error: Worksheet not found:", e)
        return None
    except Exception as e:
        print("An error occurred:", e)
        return None


# function to fetch uno data from google sheets
@st.cache_data(ttl='6h', max_entries = 1,)
def fetch_uno_data(_gc, sheet_name, sheet_key, columns_list):
    try:
        # Open specific sheet
        gs = _gc.open_by_key(sheet_key)

        # Open specific tab within the sheet
        tab = gs.worksheet(sheet_name)

        data = tab.get_all_values()
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)

        # to handle numeric columns that are imported as strings
        for column in columns_list:
            df[column] = pd.to_numeric(df[column])

        return df

    except gspread.exceptions.APIError as e:
        print("Error accessing Google Sheets API:", e)
        return None
    except gspread.exceptions.WorksheetNotFound as e:
        print("Error: Worksheet not found:", e)
        return None
    except Exception as e:
        print("An error occurred:", e)
        return None


# function to return season metrics
@st.cache_data(ttl='6h', max_entries = 1,)
def create_metrics(df):

    # Sort the DataFrame in descending order of points, then descending order of total_points then alphabetically
    df_sorted = df.sort_values(
        ["event", "points", "total_points", "player_name"],
        ascending=[True, False, False, True],
    )

    # Group the DataFrame by event and get the first place finisher for each event
    first_place_df = df_sorted.groupby("event").head(1)

    # Count the occurrences of each entry in the filtered DataFrame
    first_place_player_counts = first_place_df["player_name"].value_counts()

    # Find the player with the most 1st place finishes
    most_1st_place_player = first_place_player_counts.idxmax()
    most_1st_place_count = first_place_player_counts.max()

    # Sort the DataFrame in descending order of points, then descending order of total_points then alphabetically
    df_sorted = df.sort_values(
        ["event", "points", "total_points", "player_name"],
        ascending=[True, False, False, False],
    )

    # Group the DataFrame by event and get the last place finisher for each event
    last_place_df = df_sorted.groupby("event").tail(1)

    # Count the occurrences of each player in the last place DataFrame
    last_place_player_counts = last_place_df["player_name"].value_counts()

    # Find the player with the most last place finishes
    most_last_place_player = last_place_player_counts.idxmax()
    most_last_place_count = last_place_player_counts.max()

    # Group the DataFrame by player_name and calculate the sum of event_transfer_cost for each player
    player_transfer_cost = df.groupby("player_name")["event_transfers_cost"].sum()

    # Find the player with the highest total event_transfer_cost
    player_with_highest_cost = player_transfer_cost.idxmax()
    player_with_highest_cost_count = player_transfer_cost.max()

    # Group the DataFrame by player_name and calculate the sum of points_on_bench for each player
    player_points_on_bench = df.groupby("player_name")["points_on_bench"].sum()

    # Find the player with the highest total points_on_bench
    player_with_highest_points_on_bench = player_points_on_bench.idxmax()
    player_with_highest_points_on_bench_count = player_points_on_bench.max()

    # Find the row with the lowest points across all events
    min_score_row = df.loc[df["points"].idxmin()]

    # Extract the player_name and event for the row with the lowest score
    lowest_score_player_name = min_score_row["player_name"]
    lowest_score_event = min_score_row["event"]
    lowest_score_points = min_score_row["points"]

    return (
        most_1st_place_player,
        most_1st_place_count,
        most_last_place_player,
        most_last_place_count,
        player_with_highest_cost,
        player_with_highest_cost_count,
        player_with_highest_points_on_bench,
        player_with_highest_points_on_bench_count,
        lowest_score_player_name,
        lowest_score_event,
        lowest_score_points,
    )


@st.cache_data(ttl='6h',max_entries=1)
#checks the latest data to see if it needs to be refreshed
def fetch_max_gw(_gc, sheet_name, sheet_key):
    try:
        # Open specific sheet
        gs = _gc.open_by_key(sheet_key)

        # Open specific tab within the sheet
        tab = gs.worksheet(sheet_name)

        data = tab.get_all_values()
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)

        # Convert the first column to numeric
        df[headers[0]] = pd.to_numeric(df[headers[0]])

        # Get the maximum value of the first column
        max_value = df[headers[0]].max()

        return int(max_value)

    except gspread.exceptions.APIError as e:
        print("Error accessing Google Sheets API:", e)
        return None
    except gspread.exceptions.WorksheetNotFound as e:
        print("Error: Worksheet not found:", e)
        return None
    except Exception as e:
        print("An error occurred:", e)
        return None

@st.cache_data(ttl='6h',max_entries=1)
def most_litres(df, name_col, qty_col):
    grouped_data = df.groupby(name_col)[qty_col].sum()
    highest_category = grouped_data.idxmax()
    highest_sum = np.round(grouped_data.max()/1000, 2)
    return highest_category, highest_sum

@st.cache_data(ttl='6h',max_entries=1)
def update(_gc):
    with requests.Session() as session:
        general_response = session.get(general_endpoint).json()

    events = pd.DataFrame(general_response['events'])[['id', 'is_previous', 'is_current', 'is_next', 'finished', 'data_checked',]]
    if len(events[events['is_current'] == True]) == 0:
        print('season hasn\'t started pull placeholder data')
        events = pd.DataFrame(placeholder_events)[['id', 'is_previous', 'is_current', 'is_next', 'finished', 'data_checked',]]

    
    gw = int(events[events["is_current"] == True]["id"])
    finished = bool(events[events["is_current"] == True]["finished"].values)
    data_checked = bool(events[events["is_current"] == True]["data_checked"].values)
    
    if finished and data_checked:
        print(f"finished: {finished}\nchecked: {data_checked}\ngame week: {gw}")
        max_stored_gw = fetch_max_gw(_gc, gameweek_results_table, google_sheet_key)
        if max_stored_gw < gw:      
            print('max stored_gw < current week')
            print('we will update here')
            return True
        
        else: 
            print('data is already latest - pull from gs')
            return False
    else:
        print("its either a new week or the old week hasnt completetly finished - pull from gs")
        print(f"finished: {finished}\nchecked: {data_checked}\ngame week: {gw}")
        return False
#'''------------------------------------------------------------REGULAR FUNCTIONS------------------------------------------------------------'''


# function to write data to google sheets
def write_google_sheets_data(_gc, df, sheet_name, sheet_key):
    try:
        # Open specific sheet
        gs = _gc.open_by_key(sheet_key)

        # Open specific tab within the sheet
        tab = gs.worksheet(sheet_name)

        df_values = df.values.tolist()
        gs.values_append(sheet_name, {"valueInputOption": "RAW"}, {"values": df_values})

        return None

    except gspread.exceptions.APIError as e:
        print("Error accessing Google Sheets API:", e)
        return None
    except gspread.exceptions.WorksheetNotFound as e:
        print(f"Error: Worksheet not found, please create a new tab named:", e)
        return None
    except Exception as e:
        print("An error occurred:", e)
        return None


# function to validate select box choices
def select_box_validator(input):
    if input == "":
        return False
    else:
        return True


def submit_drink(_gc, df, sheet_key, nominee, drink_size):
    try:
        filtered_df = df[
            (df["drinker_name"] == nominee)
            & (df["nomination_completed_date"] == "Not Completed")
        ]
        last_record_index = filtered_df.index[-1]
        df.at[last_record_index, "nomination_completed_date"] = (datetime.now() + timedelta(hours=2)).strftime("%d/%m/%y %H:%M")
        df.at[last_record_index, "drink_size"] = drink_size
    except IndexError as e:
        r = "You dont have any outstanding drinks"
        return r

    try:
        # Open specific sheet
        gs = _gc.open_by_key(sheet_key)

        # Open specific tab within the sheet
        tab = gs.worksheet("drinks")

        set_with_dataframe(tab, df)

        return None

    except gspread.exceptions.APIError as e:
        print("Error accessing Google Sheets API:", e)
        return None
    except gspread.exceptions.WorksheetNotFound as e:
        print(f"Error: Worksheet not found, please create a new tab named:", e)
        return None
    except Exception as e:
        print("An error occurred:", e)
        return None


def categories(df):
    df["quantity"] = 1
    df = df.iloc[:, [2, 5, 6, 7]]
    df.rename(columns={"drinker_name": "Name"}, inplace=True)
    # Define the conditions for the new column
    condition1 = df["nomination_completed_date"] < df["nomination_deadline_date"]
    condition2 = df["nomination_completed_date"] > df["nomination_deadline_date"]
    condition3 = df["nomination_completed_date"] == "Not Completed"

    # Apply the conditions and create the new column
    # Set a default value if no conditions are met
    df["Category"] = "Default Value"
    df.loc[condition1, "Category"] = "Completed"
    df.loc[condition2, "Category"] = "Late"
    df.loc[condition3, "Category"] = "Outstanding"

    return df


def uno_reverse(gc, drinks, uno_data, sheet_key, nominee):
    try:
        # Find the last record for the specified nominee with "Not Completed" nomination
        filtered_drinks = drinks[
            (drinks["drinker_name"] == nominee)
            & (drinks["nomination_completed_date"] == "Not Completed")
        ]
        
        if filtered_drinks.empty:
            return "You don't have any outstanding drinks"

        last_record_index = filtered_drinks.index[-1]

        # Perform the uno reverse operation on the last record
        drinks.at[last_record_index, "drinker_name"] = filtered_drinks["nominator_name"][
            last_record_index
        ]
        drinks.at[last_record_index, "drink_type"] = "uno reverse"

    except IndexError:
        return "You don't have any outstanding drinks"

    # Check if the nominee has already used their uno reverse card this season
    try:
        filtered_uno_data = uno_data[(uno_data["player_name"] == nominee)]
        if filtered_uno_data.empty:
            raise Exception("You haven't used your uno reverse card this season")

        uno_index = filtered_uno_data.index[0]

        if filtered_uno_data.iloc[0, uno_data.columns.get_loc('uno_reverse')] == 'No':
            raise Exception("You have already used your uno reverse card this season")

        # Convert "nomination_created_date" to a datetime object for comparison
        nomination_created_datetime = datetime.strptime(filtered_drinks.nomination_created_date.iloc[0], "%d/%m/%y %H:%M:%S")

        if (datetime.now() + timedelta(hours=2)) > (nomination_created_datetime + timedelta(days=2)):
            raise Exception("You took more than 2 days to use your uno reverse card, try again next time")
        else: 
            # Use a single equal sign (=) for assignment
            uno_data.at[uno_index, 'uno_reverse'] = 'No'
    except Exception as e:
        return str(e)


    try:
        # Open specific sheet
        gs = gc.open_by_key(sheet_key)

        # Open specific tab within the sheet
        drinks_tab = gs.worksheet("drinks")
        uno_tab =  gs.worksheet("managers")

        # Update the Google Sheet with the modified drinks DataFrame
        set_with_dataframe(drinks_tab, drinks)
        set_with_dataframe(uno_tab, uno_data)

    except gspread.exceptions.APIError as e:
        print("Error accessing Google Sheets API:", e)
        return None
    except gspread.exceptions.WorksheetNotFound as e:
        print(f"Error: Worksheet not found, please create a new tab named:", e)
        return None
    except Exception as e:
        print("An error occurred:", e)
        return None

    return None



def build_rank_df(gameweek_df, current_week):
    last_10 = gameweek_df[gameweek_df.event >= current_week - 10].iloc[:, [0, 2, 4]]
    # last_10 = gameweek_df[gameweek_df.event<=10].iloc[:,[0,2,4]]
    last_10["rank"] = (
        last_10.groupby(["event"])["total_points"].rank(ascending=False).astype(int)
    )
    return last_10


def build_laps(df):
    # Filter rows with relevant columns and non-null values
    drinks_lap_times = df[['drinker_name', 'nomination_completed_date', 'nomination_deadline_date', 
                          'start_time', 'end_time', 'drink_size']].dropna()

    # Filter rows with valid nomination completion date
    drinks_lap_times = drinks_lap_times[drinks_lap_times['nomination_completed_date'] < drinks_lap_times['nomination_deadline_date']]

    # Compute the lap times
    drinks_lap_times['completion_time'] = np.round((drinks_lap_times['end_time'] - drinks_lap_times['start_time']) * (330 / drinks_lap_times['drink_size']), 3)

    # Sort by completion_time
    drinks_lap_times = drinks_lap_times.sort_values(by='completion_time')

    # Compute the gap from the fastest time
    fastest_time = drinks_lap_times['completion_time'].min()
    drinks_lap_times['gap'] = drinks_lap_times['completion_time'] - fastest_time
    drinks_lap_times['gap'] = drinks_lap_times['gap'].apply(lambda x: f"+{x:.3f}" if pd.notna(x) and x != 0 else '')

    # Select and format the relevant columns
    display_times = drinks_lap_times[[ 'drinker_name', 'completion_time', 'gap']]
    display_times.index = np.arange(1, len(display_times) + 1)

    # Rename the columns
    display_times.rename(
        columns={"drinker_name": "Driver", "completion_time": "Lap Time", "gap": "Gap"},
        inplace=True
    )
    return display_times

