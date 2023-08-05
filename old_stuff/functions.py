import requests
import pandas as pd
import numpy as np
from config import *


def get_names():
    with requests.Session() as session:
        league_response = session.get(league_endpoint).json()
        manager_names = (
            pd.DataFrame.from_records(
                league_response["standings"]["results"], columns=["id", "player_name"]
            )
            .set_index("id")
            .sort_values("player_name")
        )
    return manager_names


def get_fixtures():
    with requests.Session() as session:
        fixture_response = session.get(fixture_endpoint).json()
        general_response = session.get(general_endpoint).json()

    fixture_ids = pd.DataFrame.from_records(
        fixture_response, columns=["event", "team_a", "team_h"]
    )
    gameweek_data = (
        pd.DataFrame.from_records(
            general_response["events"],
            columns=[
                "id",
                "deadline_time",
                "is_current",
                "most_captained",
                "most_vice_captained",
                "top_element",
            ],
        )
        .fillna(0)
        .astype({"most_captained": int, "most_vice_captained": int, "top_element": int})
        .set_index("id")
    )  # <-- manually sets current week, remove once fpl is live
    gameweek_data.iloc[0, 1] = True
    current_week = gameweek_data.index[gameweek_data["is_current"]].item()
    current_fixtures = fixture_ids[fixture_ids["event"] == current_week]
    # <--fixtures need to be mapped to people
    return current_fixtures.iloc[:, [1, 2]]
