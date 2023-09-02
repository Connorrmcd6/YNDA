import numpy as np
import pandas as pd
import streamlit as st
import json
from datetime import datetime, timedelta
from random import sample
import time
from gspread_dataframe import set_with_dataframe
import gspread
from google.oauth2 import service_account
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import matplotlib.pyplot as plt
import altair as alt
import base64
import textwrap
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

@st.cache_data(max_entries = 1,)
def render_logo(path):
    with open(path, "r") as f:
        svg_content = f.read()

    b64_svg = base64.b64encode(svg_content.encode('utf-8')).decode("utf-8")
    img_tag = f'<img src="data:image/svg+xml;base64,{b64_svg}"/>'
    
    st.write(img_tag, unsafe_allow_html=True)
    st.markdown("###")

@st.cache_data(max_entries = 1,)
def render_svg_banner(path, width=None, height=None, gw_number=None, first_place_name=None, team_name=None):
    with open(path, "r") as f:
        svg_content = f.read()

    if gw_number is not None:
        svg_content = svg_content.replace("@gw_number", str(gw_number))
    if first_place_name is not None:
        svg_content = svg_content.replace("@first_place_name", first_place_name.upper())
    if team_name is not None:
        svg_content = svg_content.replace("@team_name", team_name.upper())

    b64_svg = base64.b64encode(svg_content.encode('utf-8')).decode("utf-8")

    style = ""
    if width is not None:
        style += f"width: {width}%;"
    if height is not None:
        style += f"height: {height}%;"
        
    img_tag = f'<img src="data:image/svg+xml;base64,{b64_svg}" style="{style}"/>'
    
    st.write(img_tag, unsafe_allow_html=True)


def render_svg_metric(path, width=None, height=None, name=None, metric_name=None, value_str=None):
    with open(path, "r") as f:
        svg_content = f.read()

    if name is not None:
        svg_content = svg_content.replace("@name", str(name).upper())
    if metric_name is not None:
        svg_content = svg_content.replace("@metric_name", metric_name.upper())
    if value_str is not None:
        svg_content = svg_content.replace("@value", value_str)


    b64_svg = base64.b64encode(svg_content.encode('utf-8')).decode("utf-8")

    style = ""
    if width is not None:
        style += f"width: {width}%;"
    if height is not None:
        style += f"height: {height}%;"
        
    img_tag = f'<img src="data:image/svg+xml;base64,{b64_svg}" style="{style}"/>'
    
    st.write(img_tag, unsafe_allow_html=True)




# function to fetch gw data from google sheets
@st.cache_data(max_entries = 1,)
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

@st.cache_data(ttl='6h', max_entries = 1,)
def render_svg_summary(path, width=None, height=None, ls=None, mps=None, rcs=None, ogs=None, nms=None):
    with open(path, "r") as f:
        svg_content = f.read()

    if ls is not None:
        svg_content = svg_content.replace("@litres", str(ls))
    if mps is not None:
        svg_content = svg_content.replace("@missed_pens", str(mps))
    if rcs is not None:
        svg_content = svg_content.replace("@red_cards", str(rcs))
    if ogs is not None:
        svg_content = svg_content.replace("@own_goals", str(ogs))
    if nms is not None:
        svg_content = svg_content.replace("@nominations", str(nms))

    b64_svg = base64.b64encode(svg_content.encode('utf-8')).decode("utf-8")

    style = ""
    if width is not None:
        style += f"width: {width}%;"
    if height is not None:
        style += f"height: {height}%;"
        
    img_tag = f'<img src="data:image/svg+xml;base64,{b64_svg}" style="{style}"/>'
    
    st.write(img_tag, unsafe_allow_html=True)
    st.markdown(" #####")

#build drinks display table
@st.cache_data(ttl='6h', max_entries = 1,)
def build_drinks_display(drinks, current_week):
    drinks_display = drinks[drinks.event == current_week]
    drinks_display = drinks[drinks.nomination_completed_date == "Not Completed"]
    drinks_display['formatted_deadline_date'] = drinks_display['nomination_deadline_date'].apply(lambda x: format_date(x))
    drinks_display = drinks_display.iloc[:, [2, 3, 11]]
    drinks_display.rename(
        columns={
            "drinker_name": "Name",
            "drink_type": "Drink Type",
            "formatted_deadline_date": "Deadline",
        },
        inplace=True,
        )
    return drinks_display


@st.cache_data(ttl='6h', max_entries = 1,)
def build_drinks_display_expanded(drinks):
    drinks_display = drinks
    drinks_display['formatted_deadline_date'] = drinks_display['nomination_deadline_date'].apply(lambda x: format_date(x))
    drinks_display['formatted_completed_date'] = drinks_display['nomination_completed_date'].apply(lambda x: format_date(x))
    drinks_display = drinks.iloc[:, [0, 2, 3, 11, 12]]
    drinks_display.rename(
        columns={
            "event": "Game Week",
            "drinker_name": "Name",
            "drink_type": "Drink Type",
            "formatted_deadline_date": "Deadline",
            "formatted_completed_date": "Completed Date",
        },
        inplace=True,
        )
    return drinks_display


# function to fetch managers from google sheets
@st.cache_data(max_entries = 1,)
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
@st.cache_data(max_entries = 1,)
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


@st.cache_data(max_entries = 1,)
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
        gw = 0
        return False, gw, False, False
    
    gw = int(events[events["is_current"] == True]["id"])
    finished = bool(events[events["is_current"] == True]["finished"].values)
    data_checked = bool(events[events["is_current"] == True]["data_checked"].values)
    
    if finished and data_checked:
        print(f"finished: {finished}\nchecked: {data_checked}\ngame week: {gw}")
        max_stored_gw = fetch_max_gw(_gc, gameweek_results_table, prod_google_sheet_key)
        if max_stored_gw < gw:      
            print('max stored_gw < current week')
            print('we will update here')
            return True, gw,  finished, data_checked
        
        else: 
            print('data is already latest - pull from gs')
            return False, max_stored_gw, finished, data_checked
    else:
        print("its either a new week or the old week hasnt completetly finished - pull from gs")
        print(f"finished: {finished}\nchecked: {data_checked}\ngame week: {gw}")
        return False, gw, finished, data_checked
    

@st.cache_data(max_entries = 1,)
def get_illegible_nominees(df, current_gw):
    red_card_players = df[(df['event'] == current_gw) & (df['drink_type'] == 'red card')]['drinker_name'].tolist()
    own_goal_players = df[(df['event'] == current_gw) & (df['drink_type'] == 'own goal')]['drinker_name'].tolist()
    missed_pen_players = df[(df['event'] == current_gw) & (df['drink_type'] == 'missed pen')]['drinker_name'].tolist()
    return red_card_players, own_goal_players, missed_pen_players

@st.cache_data(max_entries = 1,)
def get_first_last(df, current_gw):
    # Filter the DataFrame for the given current_gw
    current_gw_df = df[df['event'] == current_gw]

    if len(current_gw_df) == 0:
        return None, None, None  # gw not finished

    # Sort the filtered DataFrame based on points, total_points, and player_name
    sorted_df = current_gw_df.sort_values(by=["points", "total_points", "player_name"],
                                          ascending=[False, False, True])

    # Get the player names of the first and last place
    first_place_name = sorted_df.iloc[0].player_name
    last_place_name = sorted_df.iloc[-1].player_name
    first_team_name = sorted_df.iloc[0].entry_name

    return first_place_name, last_place_name,first_team_name

@st.cache_data(max_entries = 1,)
def get_previous_first_last(df, current_gw):
    # Filter the DataFrame for the given current_gw
    current_gw_df = df[df['event'] == current_gw-1]

    if len(current_gw_df) == 0:
        return None, None, None  # gw not finished

    # Sort the filtered DataFrame based on points, total_points, and player_name
    sorted_df = current_gw_df.sort_values(by=["points", "total_points", "player_name"],
                                          ascending=[False, False, True])

    # Get the player names of the first and last place
    first_place_name = sorted_df.iloc[0].player_name
    last_place_name = sorted_df.iloc[-1].player_name
    first_team_name = sorted_df.iloc[0].entry_name

    return first_place_name, last_place_name,first_team_name

@st.cache_data(max_entries = 1,)
def build_rank_df(gameweek_df, current_week):
    last_10 = gameweek_df[gameweek_df.event >= current_week - 10][["event", "player_name", "total_points"]]
    # last_10 = gameweek_df[gameweek_df.event<=10].iloc[:,[0,2,4]]
    last_10["rank"] = (
        last_10.groupby(["event"])["total_points"].rank(ascending=False).astype(int)
    )
    return last_10

@st.cache_data(ttl='6h', max_entries = 1,)
def build_laps(df):
    # Filter rows with relevant columns and non-null values
    drinks_lap_times = df[['drinker_name', 'nomination_completed_date', 'nomination_deadline_date', 
                          'start_time', 'end_time', 'drink_size']].dropna()
    
    # Convert date columns to datetime objects
    drinks_lap_times["nomination_completed_date"] = drinks_lap_times["nomination_completed_date"].apply(lambda x: create_unix(x))
    drinks_lap_times["nomination_deadline_date"] = drinks_lap_times["nomination_deadline_date"].apply(lambda x: create_unix(x))


    # Filter rows with valid nomination completion date
    drinks_lap_times = drinks_lap_times[drinks_lap_times['nomination_completed_date'] < drinks_lap_times['nomination_deadline_date']]

    # Compute the lap times
    drinks_lap_times['completion_time'] = np.round((drinks_lap_times['end_time'] - drinks_lap_times['start_time']) * (330 / drinks_lap_times['drink_size']), 3)

    # Group by drinker_name and find the minimum completion_time
    fastest_times = drinks_lap_times.groupby('drinker_name')['completion_time'].min()

    # Create a DataFrame with fastest times
    fastest_times_df = pd.DataFrame({'drinker_name': fastest_times.index, 'completion_time': fastest_times.values})

    # Compute the gap from the fastest time
    fastest_time = fastest_times_df['completion_time'].min()
    fastest_times_df['gap'] = fastest_times_df['completion_time'] - fastest_time
    
    fastest_times_df['gap'] = fastest_times_df['gap'].apply(lambda x: f"+{x:.3f}s" if pd.notna(x) and x != 0 else '')

    # Sort by completion_time
    fastest_times_df = fastest_times_df.sort_values(by='completion_time')

    # Select and format the relevant columns
    display_times = fastest_times_df[['drinker_name', 'completion_time', 'gap']]
    display_times.index = np.arange(1, len(display_times) + 1)

    # Rename the columns
    display_times.rename(
        columns={"drinker_name": "Driver", "completion_time": "Lap Time", "gap": "Gap"},
        inplace=True
    )
    return display_times

@st.cache_data(ttl='6h',max_entries=1)
def time_since_last_update():
    time_plus_6_hours = datetime.now() + timedelta(hours=6)
    return time_plus_6_hours

@st.cache_data(ttl='6h',max_entries=1)
def analyze_drinks(df):
    # Calculate the sum of the drink_size column
    total_drink_size = f"{df['drink_size'].sum()/1000:.2f}"

    # Count occurrences of specific drink types
    drink_type_counts = df['drink_type'].value_counts()

    # Get counts for specific drink types
    missed_pen_count = drink_type_counts.get('missed pen', 0)
    red_card_count = drink_type_counts.get('red card', 0)
    own_goal_count = drink_type_counts.get('own goal', 0)
    nomination_count = drink_type_counts.get('nomination', 0)

    return total_drink_size, missed_pen_count, red_card_count, own_goal_count, nomination_count

#'''------------------------------------------------------------REGULAR FUNCTIONS------------------------------------------------------------'''
def fetch_google_sheets_data(gc, sheet_name, sheet_key, columns_list):
    try:
        # Open specific sheet
        gs = gc.open_by_key(sheet_key)

        # Open specific tab within the sheet
        tab = gs.worksheet(sheet_name)

        data = tab.get_all_values()
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)

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
    
def time_until_specified_time(target_time):
    current_time = datetime.now()
    time_difference = target_time - current_time
    time_difference = target_time - current_time
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes = remainder // 60
    time_format = f"{hours:02d}h:{minutes:02d}min"
    return time_format

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
        first_record_index = filtered_df.index[0]  # Get the index of the first record
        
        # Use Unix time (seconds since epoch) instead of formatted time
        now_unix = int(time.time()) + 2 * 3600  # Adding 2 hours in seconds
        df.at[first_record_index, "nomination_completed_date"] = now_unix
        df.at[first_record_index, "drink_size"] = drink_size
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



    df['nomination_completed_date'] = df['nomination_completed_date'].apply(lambda x: create_unix(x))
    df['nomination_deadline_date'] = df['nomination_deadline_date'].apply(lambda x: create_unix(x))

    # Initialize an empty list to store the categories
    categories = []

    for index, row in df.iterrows():
        completed_date = row["nomination_completed_date"]
        deadline_date = row["nomination_deadline_date"]

        if completed_date == "Not Completed":
            categories.append("Outstanding")
        elif completed_date <= deadline_date:
            categories.append("Completed")
        else:
            categories.append("Late")

    # Add the categories list as a new column in the DataFrame
    df["Category"] = categories

    return df



def uno_reverse(gc, drinks, uno_data, sheet_key, nominee):
    try:
        # Find the last record for the specified nominee with "Not Completed" nomination
        filtered_drinks = drinks[
            (drinks["drinker_name"] == nominee)
            & (drinks["nomination_completed_date"] == "Not Completed")
            & (drinks["drink_type"] == "nomination")
        ]
        
        if filtered_drinks.empty:
            return "You don't have any valid drinks to reverese"

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
        #this if is useless, was added by chatgpt
        filtered_uno_data = uno_data[(uno_data["player_name"] == nominee)]
        if filtered_uno_data.empty:
            raise Exception("You haven't used your uno reverse card this season")

        uno_index = filtered_uno_data.index[0]

        if filtered_uno_data.iloc[0, uno_data.columns.get_loc('uno_reverse')] == 'No':
            raise Exception("You have already used your uno reverse card this season")

        # Convert "nomination_created_date" to a datetime object for comparison
        nomination_created_datetime = int(filtered_drinks.nomination_created_date.iloc[0])

        current_timestamp = int(time.time()) + 2*60*60 #adjust for sever time
        two_days_in_seconds = 2 * 24 * 60 * 60  # 2 days in seconds

        if current_timestamp > (nomination_created_datetime + two_days_in_seconds):
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

def fetch_max_gw_helper(_gc, sheet_name, sheet_key):
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

def get_player_stats(player_id, live_gw_data):
    for element in live_gw_data["elements"]:
        if element["id"] == player_id:
            return element["stats"]
    return None

def append_missing_rows(df1, df2, current_gw):
    # Extract relevant columns
    t1 = df1[["entry", "player_name", "entry_name"]]
    t2 = df2[["entry", "player_name", "entry_name"]]
    
    # Find missing rows
    missing_rows = t2[~t2['entry'].isin(t1['entry'])]
    
    if missing_rows.empty:
        return None
    
    # Add new columns
    missing_rows["event_joined"] = current_gw
    missing_rows["uno_reverse"] = "Yes"
    
    return missing_rows

def managers_update(_gc, league_endpoint, current_gw):
    # Fetch league data using a session
    with requests.Session() as session:
        league_response = session.get(league_endpoint).json()

    # Create DataFrame from league standings
    league_data = league_response["standings"]["results"]
    df2 = pd.DataFrame(league_data)

    #convert columns to numerics
    numerical_columns = ['entry', 'event_joined']
    df1 = fetch_manager_data(_gc, managers_table, prod_google_sheet_key, numerical_columns)

    # Append missing rows and handle the result
    missing_rows = append_missing_rows(df1, df2, current_gw)
    if missing_rows is None:
        return df1[["entry", "player_name", 'entry_name']]

    # Write missing rows to the Google Sheet
    write_google_sheets_data(_gc, missing_rows, managers_table, prod_google_sheet_key)
    return missing_rows[["entry", "player_name", 'entry_name']]

def analyze_picks(picks, live_gw_data):
    red_card = 0
    own_goal = 0
    penalties_missed = 0

    for player_id in picks:
        player_stats = get_player_stats(player_id, live_gw_data)
        if player_stats:
            red_card += player_stats["red_cards"]
            own_goal += player_stats["own_goals"]
            penalties_missed += player_stats["penalties_missed"]

    return red_card > 0, own_goal > 0, penalties_missed > 0

def gameweek_results_update(_gc, current_gw, manager_details):
    new_gameweek_results = pd.DataFrame()
    picks_data = pd.DataFrame()

    for entry, player_name, entry_name in zip(manager_details['entry'], manager_details['player_name'], manager_details['entry_name']):
        live_teams_endpoint = f'https://fantasy.premierleague.com/api/entry/{entry}/event/{current_gw}/picks/'
        with requests.Session() as session:
            live_teams_response = session.get(live_teams_endpoint).json()

        live_teams = live_teams_response['entry_history']

        # Create new player row
        new_player_row = {
            'event': current_gw,
            'entry': entry,
            'player_name': player_name,
            'entry_name': entry_name,
            'points': live_teams['points'],
            'total_points': live_teams['total_points'],
            'event_transfers': live_teams['event_transfers'],
            'event_transfers_cost': live_teams['event_transfers_cost'],
            'points_on_bench': live_teams['points_on_bench']}
        
        # Append to new_gameweek_results using concat
        new_gameweek_results = pd.concat([new_gameweek_results, pd.DataFrame([new_player_row])], ignore_index=True)

        # Get player picks
        elements_out = [sub["element_out"] for sub in live_teams_response["automatic_subs"]]
        elements_in = [sub["element_in"] for sub in live_teams_response["automatic_subs"]]
        picks = live_teams_response["picks"]

        element_ids_modified = [pick["element"] for pick in picks if pick["element"] not in elements_out]
        element_ids_modified.extend(elements_in)

        live_gameweek_endpoint = f'https://fantasy.premierleague.com/api/event/{current_gw}/live/'
        with requests.Session() as session:
            live_gameweek_response = session.get(live_gameweek_endpoint).json()

        # Analyze player picks
        red_card_flag, own_goal_flag, penalties_missed_flag = analyze_picks(element_ids_modified, live_gameweek_response)

        new_picks_data = {
            'event': current_gw,
            'entry': entry,
            'player_name': player_name,
            'picks': str(element_ids_modified),
            'red_card': red_card_flag,
            'own_goal': own_goal_flag,
            'missed_pen': penalties_missed_flag
        }

        # Append to picks_data using concat
        picks_data = pd.concat([picks_data, pd.DataFrame([new_picks_data])], ignore_index=True)

    # Update google sheets for new_gameweek_results and picks_data
    write_google_sheets_data(_gc, new_gameweek_results, gameweek_results_table, prod_google_sheet_key)
    write_google_sheets_data(_gc, picks_data, gameweek_teams_table, prod_google_sheet_key)
    
    return None

# Function to filter player names based on conditions
def get_players_by_condition(df, condition_column):
    filtered_players = df[df[condition_column] == 'TRUE']
    return list(filtered_players['player_name'])

def auto_assign_drinks(_gc, gameweek_results_table, gameweek_teams_table, prod_google_sheet_key, current_gw):
    gameweek_results_table_df = fetch_google_sheets_data(_gc, gameweek_results_table, prod_google_sheet_key,  ["event", "points", "total_points", "event_transfers_cost", "points_on_bench"])
    gameweek_teams_table_df = fetch_google_sheets_data(_gc, gameweek_teams_table, prod_google_sheet_key,  ["event"])

    filtered_results = gameweek_results_table_df[gameweek_results_table_df["event"] == current_gw]
    filtered_teams = gameweek_teams_table_df[gameweek_teams_table_df["event"] == current_gw]

    lowest_points_player = filtered_results.sort_values(by=['points', 'total_points', 'player_name']).iloc[0]['player_name']
    created_date = int(time.time()) + (60*60*2) # add two hours to adjust for server time

    deadline_date_str = (datetime.now() + timedelta(days=7)).strftime("%d/%m/%y %23:59:59")
    parsed_datetime = datetime.strptime(deadline_date_str, "%d/%m/%y %H:%M:%S")
    deadline_date = parsed_datetime.timestamp()



    # Get player names with red cards, own goals, and missed penalties
    red_card_players = get_players_by_condition(filtered_teams, 'red_card')
    own_goal_players = get_players_by_condition(filtered_teams, 'own_goal')
    missed_pen_players = get_players_by_condition(filtered_teams, 'missed_pen')

    red_card_drinks_data = {
        "event": [current_gw]*len(red_card_players),
        "nominator_name": ["auto"]*len(red_card_players),
        "drinker_name": red_card_players,
        "drink_type": ["red card"]*len(red_card_players),
        "nomination_created_date": [created_date]*len(red_card_players),
        "nomination_deadline_date": [deadline_date]*len(red_card_players),
        "nomination_completed_date": ["Not Completed"]*len(red_card_players),
    }

    own_goal_players_drinks_data = {
        "event": [current_gw]*len(own_goal_players),
        "nominator_name": ["auto"]*len(own_goal_players),
        "drinker_name": own_goal_players,
        "drink_type": ["own goal"]*len(own_goal_players),
        "nomination_created_date": [created_date]*len(own_goal_players),
        "nomination_deadline_date": [deadline_date]*len(own_goal_players),
        "nomination_completed_date": ["Not Completed"]*len(own_goal_players),
    }

    missed_pen_players_drinks_data = {
        "event": [current_gw]*len(missed_pen_players),
        "nominator_name": ["auto"]*len(missed_pen_players),
        "drinker_name": missed_pen_players,
        "drink_type": ["missed pen"]*len(missed_pen_players),
        "nomination_created_date": [created_date]*len(missed_pen_players),
        "nomination_deadline_date": [deadline_date]*len(missed_pen_players),
        "nomination_completed_date": ["Not Completed"]*len(missed_pen_players),
    }

    last_place_drinks_data = {
        "event": [current_gw],
        "nominator_name": ["auto"],
        "drinker_name": lowest_points_player,
        "drink_type": ["last place"],
        "nomination_created_date": [created_date],
        "nomination_deadline_date": [deadline_date],
        "nomination_completed_date": ["Not Completed"],
    }

    df1 = pd.DataFrame(red_card_drinks_data)
    df2 = pd.DataFrame(own_goal_players_drinks_data)
    df3 = pd.DataFrame(missed_pen_players_drinks_data)
    df4 = pd.DataFrame(last_place_drinks_data)

    concatenated_df = pd.concat([df1, df2, df3, df4], ignore_index=True)

    write_google_sheets_data(_gc, concatenated_df, drinks_table, prod_google_sheet_key)

def can_nominate_flag(df, current_gw, first_place):
    return len(df[(df["event"] == current_gw) & (df["nominator_name"] == first_place)]) == 0


def format_date(date_str):
    try:
        timestamp = int(date_str)  # Assuming date_str is a Unix timestamp in string format
        date_obj = datetime.fromtimestamp(timestamp)
        return date_obj.strftime('%d %b')
    except ValueError:
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%y %H:%M')
            return date_obj.strftime('%d %b')
        except ValueError:
            try:
                date_obj = datetime.strptime(date_str, '%d/%m/%y')
                return date_obj.strftime('%d %b')
            except ValueError:
                return "Not Completed"

def create_unix(date_str):
    try:
        timestamp = int(date_str)
        return timestamp
    except ValueError:
        return "Not Completed"
        
def needs_new_uno(df, last_place):
    # Check if there's a match in player_name and uno_reverse is "No"
    match_condition = (df['player_name'] == last_place) & (df['uno_reverse'] == 'No')
    
    # Check if any row satisfies the condition
    if any(match_condition):
        return True
    else:
        return False


def give_new_uno(gc, sheet_key, uno_data, last_place):
    """
    Update the 'uno_reverse' value in the Google Sheet based on the last place player.
    
    Args:
        gc (gspread.Client): Google Sheets API client.
        sheet_key (str): Google Sheet key.
        uno_data (pandas.DataFrame): DataFrame containing Uno data.
        last_place (str): Player name in last place.
    """
    try:
        # Filter and update uno_data
        filtered_uno_data = uno_data[uno_data["player_name"] == last_place]
        if not filtered_uno_data.empty:
            uno_index = filtered_uno_data.index[0]
            uno_data.at[uno_index, 'uno_reverse'] = 'Yes'
        else:
            print(f"Player '{last_place}' not found in Uno data.")
            return

        # Open specific sheet
        gs = gc.open_by_key(sheet_key)

        # Open specific tabs within the sheet
        drinks_tab = gs.worksheet("drinks")
        uno_tab = gs.worksheet("managers")

        # Update the Google Sheet with the modified uno_data DataFrame
        set_with_dataframe(uno_tab, uno_data)

    except gspread.exceptions.APIError as e:
        print("Error accessing Google Sheets API:", e)
    except gspread.exceptions.WorksheetNotFound as e:
        print(f"Error: Worksheet not found, please create a new tab named:", e)
    except Exception as e:
        print("An error occurred:", e)