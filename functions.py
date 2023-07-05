import requests
import pandas as pd
import numpy as np
from config import *


def get_names():
    with requests.Session() as session:
        league_response = session.get(league_endpoint).json()
        manager_names = pd.DataFrame.from_records(league_response['standings']['results'], columns=[
                                                  'id', 'player_name']).set_index('id'). sort_values("player_name")
    return manager_names

