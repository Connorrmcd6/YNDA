import numpy as np
import pandas as pd
import streamlit as st
import os
import gspread
from google.oauth2 import service_account
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from configs import *


# function to create api connection to google sheets
def connect_to_gs(service_account_key):
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = service_account.Credentials.from_service_account_info(
        service_account_key, scopes=scopes)
    gs_connection = gspread.authorize(credentials)
    return gs_connection

# function to fetch data from google sheets


def google_sheets_data(gc, sheet_name, sheet_key, columns_list):
    try:
        # Open specific sheet
        gs = gc.open_by_key(sheet_key)

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
def create_metrics(df):

    # Sort the DataFrame in descending order of points, then descending order of total_points then alphabetically
    df_sorted = df.sort_values(['event', 'points', 'total_points', 'player_name'], ascending=[
                               True, False, False, True])

    # Group the DataFrame by event and get the first place finisher for each event
    first_place_df = df_sorted.groupby('event').head(1)

    # Count the occurrences of each entry in the filtered DataFrame
    first_place_player_counts = first_place_df['player_name'].value_counts()

    # Find the player with the most 1st place finishes
    most_1st_place_player = first_place_player_counts.idxmax()
    most_1st_place_count = first_place_player_counts.max()

    # Sort the DataFrame in descending order of points, then descending order of total_points then alphabetically
    df_sorted = df.sort_values(['event', 'points', 'total_points', 'player_name'], ascending=[
                               True, False, False, False])

    # Group the DataFrame by event and get the last place finisher for each event
    last_place_df = df_sorted.groupby('event').tail(1)

    # Count the occurrences of each player in the last place DataFrame
    last_place_player_counts = last_place_df['player_name'].value_counts()

    # Find the player with the most last place finishes
    most_last_place_player = last_place_player_counts.idxmax()
    most_last_place_count = last_place_player_counts.max()

    # Group the DataFrame by player_name and calculate the sum of event_transfer_cost for each player
    player_transfer_cost = df.groupby(
        'player_name')['event_transfers_cost'].sum()

    # Find the player with the highest total event_transfer_cost
    player_with_highest_cost = player_transfer_cost.idxmax()
    player_with_highest_cost_count = player_transfer_cost.max()

    # Group the DataFrame by player_name and calculate the sum of points_on_bench for each player
    player_points_on_bench = df.groupby('player_name')['points_on_bench'].sum()

    # Find the player with the highest total points_on_bench
    player_with_highest_points_on_bench = player_points_on_bench.idxmax()
    player_with_highest_points_on_bench_count = player_points_on_bench.max()

    # Find the row with the lowest points across all events
    min_score_row = df.loc[df['points'].idxmin()]

    # Extract the player_name and event for the row with the lowest score
    lowest_score_player_name = min_score_row['player_name']
    lowest_score_event = min_score_row['event']
    lowest_score_points = min_score_row['points']

    return most_1st_place_player, most_1st_place_count, most_last_place_player, most_last_place_count, player_with_highest_cost, player_with_highest_cost_count, player_with_highest_points_on_bench, player_with_highest_points_on_bench_count, lowest_score_player_name, lowest_score_event, lowest_score_points
