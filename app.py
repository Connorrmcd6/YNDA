from functions import *
from configs import *

#'''------------------------------------------------------------PAGE CONFIGS------------------------------------------------------------'''
st.set_page_config(page_title='YNDA',
                   layout='centered',
                   initial_sidebar_state='collapsed',
                   page_icon='🍺',
                   )

#'''------------------------------------------------------------GOOGLE CONNECTION------------------------------------------------------------'''
gs_connection = connect_to_gs(st.secrets['gcp_service_account'])


#'''------------------------------------------------------------FPL API CALLS------------------------------------------------------------'''
# use this section to update all google sheets data to latest data

if "current_week" not in st.session_state:
    current_week = 1  # change to function
    st.session_state.current_week = current_week
else:
    current_week = st.session_state.current_week


#'''------------------------------------------------------------GOOGLE API CALLS------------------------------------------------------------'''
if 'managers' not in st.session_state:
    managers = sorted(fetch_google_sheets_data(
        gs_connection, managers_table, google_sheet_key, [])['player_name'])
    managers.insert(0, "")
    st.session_state.managers = managers
else:
    managers = st.session_state.managers


if "last_place" not in st.session_state:
    last_place = "Alex Wietzorrek"  # change to function
    st.session_state.last_place = last_place
else:
    last_place = st.session_state.last_place


if "red_cards" not in st.session_state:
    red_cards = []  # change to function
    st.session_state.red_cards = red_cards
else:
    red_cards = st.session_state.red_cards

if "own_goals" not in st.session_state:
    own_goals = []  # change to function
    st.session_state.own_goals = own_goals
else:
    own_goals = st.session_state.own_goals

if "negative_points" not in st.session_state:
    negative_points = []  # change to function
    st.session_state.negative_points = negative_points
else:
    negative_points = st.session_state.negative_points


if 'data' not in st.session_state:
    # fetch gameweek data
    gameweek_df = fetch_google_sheets_data(gs_connection, gameweek_results_table, google_sheet_key, [
                                           'event', 'points', 'total_points', 'event_transfers_cost', 'points_on_bench'])
    st.session_state.data = gameweek_df

else:
    gameweek_df = st.session_state.data


# generate gameweek metrics
most_1st_place_player, most_1st_place_count, most_last_place_player, most_last_place_count, player_with_highest_cost, player_with_highest_cost_count, player_with_highest_points_on_bench, player_with_highest_points_on_bench_count, lowest_score_player_name, lowest_score_event, lowest_score_points = create_metrics(
    gameweek_df)

#'''------------------------------------------------------------SIDE BAR------------------------------------------------------------'''
with st.sidebar:
    # capture week of nomination from backend
    st.header("🎖️ Nominations")

    nominator = st.selectbox(
        label="Your Name", options=managers, key='nominate_name')

    nominee = st.selectbox("Nominate", managers)

    if st.button(label="Submit", key="nominate_submit"):
        if 'nominate' not in st.session_state:
            if not select_box_validator(nominator):
                st.error('Please fill in your name', icon="🚨")

            elif not select_box_validator(nominee):
                st.error('Please select a person to nominate', icon="🚨")

            elif nominator == nominee:
                st.error("You can't nominate yourself", icon="🚨")

            elif nominee in red_cards:
                st.error("This person got a red card, pick someone else", icon="🚨")

            elif nominee in own_goals:
                st.error(
                    "This person got an own goal, pick someone else", icon="🚨")

            elif nominee in negative_points:
                st.error(
                    "This person got negative points, pick someone else", icon="🚨")

            elif nominee == last_place:
                st.error(
                    "This person came last, pick someone else", icon="🚨")

            else:
                with st.spinner(text="Submitting..."):
                    created_date = (datetime.now() + timedelta(hours=2)
                                    ).strftime("%d/%m/%y %H:%M:%S")
                    deadline_date = (datetime.now() + timedelta(hours=2) +
                                     timedelta(days=7)).strftime("%d/%m/%y %H:00")

                    data = {'event': [current_week],
                            'nominator_name': [nominator],
                            "drinker_name": [nominee],
                            "drink_type": ["nomination"],
                            "created_date": [created_date],
                            "deadline_date": [deadline_date],
                            "completed_date": [None]}

                    df = pd.DataFrame(data)
                    write_google_sheets_data(
                        gs_connection, df, drinks_table, google_sheet_key)
                    st.session_state.nominate = True
                    st.success('Nomination Submitted')
        else:
            st.error('You have already nominated', icon="🚨")

    st.header("OR")

    if st.button('🔄 Randomly pick 3'):
        if "nominate" not in st.session_state:
            if not select_box_validator(nominator):
                st.error('Please fill in your name', icon="🚨")
            else:
                with st.spinner(text="Submitting..."):

                    # remove "" and remove last_place
                    managers_temp = managers[:]
                    managers_temp.remove('')
                    managers_temp.remove(last_place)

                    if len(red_cards) > 0:
                        managers_temp = [
                            i for i in managers_temp if i not in red_cards]

                    if len(own_goals) > 0:
                        managers_temp = [
                            i for i in managers_temp if i not in own_goals]

                    if len(negative_points) > 0:
                        managers_temp = [
                            i for i in managers_temp if i not in negative_points]

                    random_nominees = sample(managers_temp, 3)
                    created_date = (
                        datetime.now() + timedelta(hours=2)).strftime("%d/%m/%y %H:%M:%S")
                    deadline_date = (datetime.now(
                    ) + timedelta(hours=2) + timedelta(days=7)).strftime("%d/%m/%y %H:00")

                    data = {'event': [current_week, current_week, current_week],
                            'nominator_name': [nominator, nominator, nominator],
                            "drinker_name": random_nominees,
                            "drink_type": ["nomination", "nomination", "nomination"],
                            "created_date": [created_date, created_date, created_date],
                            "deadline_date": [deadline_date, deadline_date, deadline_date],
                            "completed_date": [None, None, None]}

                    df = pd.DataFrame(data)
                    write_google_sheets_data(
                        gs_connection, df, drinks_table, google_sheet_key)
                    st.text(f"1.{random_nominees[0]}")
                    st.text(f"2.{random_nominees[1]}")
                    st.text(f"3.{random_nominees[2]}")
                    st.session_state.nominate = True
                    st.success('Nomination Submitted')
        else:
            st.error('You have already nominated', icon="🚨")

    st.divider()
    st.header("🍺 Submissions")
    drink_submitter = st.selectbox(label="Your Name", options=[
                                   '', 'Alex', 'Div', 'Marco'], key='drink_name')
    if st.button(label="Submit", key="drink_submit"):
        x = 1


# '''------------------------------------------------------------APP------------------------------------------------------------'''
drinks_tab, stats_tab, awards_tab, rules_tab = st.tabs(
    ["🍺 Drinks", "📈 Stats", "🏆 Awards", "ℹ️ Rules"])


with drinks_tab:
    st.write("Latest Drinks")
    df2 = pd.DataFrame(
        # colums = gw, nominee, nominator, completed on time
        np.random.randn(5, 4),
        columns=('col %d' % i for i in range(4)))
    st.table(df2)

    st.write("Drink Streaks")
    df1 = pd.DataFrame(
        np.random.randn(10, 2),
        columns=('col %d' % i for i in range(2)))
    st.table(df1)

with stats_tab:
    st.write("Total Drinks")
    st.bar_chart(np.random.randn(50, 3))
    st.divider()

    st.write("Rank Chart Last 10 Game Weeks")
    data = np.random.randn(10, 1)
    st.line_chart(data)

with awards_tab:
    col1, col2, = st.columns(2)

    # column 1
    col1.metric("Golden Boot", f"{most_1st_place_player}",
                help=f'{most_1st_place_player} has finished first more than anyone else this season with a total of {most_1st_place_count} wins')

    col1.metric("Relegation Warrior", f'{most_last_place_player}',
                help=f'{most_last_place_player} has finished last more than anyone else this season with a total of {most_last_place_count} last place finishes')

    col1.metric("The Origi Award", f'{player_with_highest_points_on_bench}',
                help=f'{player_with_highest_points_on_bench} has accumulated the most points on bench this season with a total of {player_with_highest_points_on_bench_count} points')
    # column 2
    col2.metric("The Chelsea Award", f"{player_with_highest_cost}",
                help=f'{player_with_highest_cost} has taken the most hits this season, sacrificing a total of {player_with_highest_cost_count} points')

    col2.metric("Serial Streaker", "Cole Floyd",
                help='Longest drinks streak of the season')

    col2.metric("The Bot Award", f"{lowest_score_player_name}",
                help=f"{lowest_score_player_name} had the worst gameweek of the season with just {lowest_score_points} points in gameweek {lowest_score_event}")


with rules_tab:
    st.markdown('''
                ## Rules of the game
                - Rule 1
                - Rule 2
                - Rule 3
                                    ''')
