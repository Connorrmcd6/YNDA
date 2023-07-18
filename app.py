from functions import *

st.set_page_config(page_title='YNDA',
                   layout='centered',
                   initial_sidebar_state='collapsed',
                   page_icon='🍺',
                   )

if 'data' not in st.session_state:
    # create connection
    gs_connection = connect_to_gs(st.secrets["gcp_service_account"])

    # fetch gameweek data
    gameweek_df = google_sheets_data(
        gs_connection, gameweek_results_table, google_sheet_key, ['event', 'points', 'total_points', 'event_transfers_cost', 'points_on_bench'])
    st.session_state.data = gameweek_df
    
else: 
    gameweek_df = st.session_state.data
    # generate gameweek metrics


most_1st_place_player, most_1st_place_count, most_last_place_player, most_last_place_count, player_with_highest_cost, player_with_highest_cost_count, player_with_highest_points_on_bench, player_with_highest_points_on_bench_count, lowest_score_player_name, lowest_score_event, lowest_score_points = create_metrics(
        gameweek_df)



with st.sidebar:
    nominee = st.selectbox('Nominate someone to drink:',
                           ['Alex', 'Div', 'Marco'])

    completed_drink = st.selectbox('Record a completed drink:', [
                                   'Alex', 'Div', 'Marco'])
# names = get_names()
# nominee = st.selectbox(
#     'Pick a person to drink:',
#     names)
# if st.button("Update Dashboard"):
#     # displays the nominee
#     st.text(nominee)


awards_tab, stats_tab, drinks_tab, rules_tab = st.tabs(
    ["🏆 Awards", "📈 Stats", "🍺 Drinks", "ℹ️ Rules"])


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


with stats_tab:
    st.write("Total Drinks")
    st.bar_chart(np.random.randn(50, 3))
    st.divider()

    st.write("Rank Chart Last 10 Game Weeks")
    data = np.random.randn(10, 1)
    st.line_chart(data)


with drinks_tab:
    st.write("Drink Streaks")
    df = pd.DataFrame(
        np.random.randn(10, 3),
        columns=('col %d' % i for i in range(3)))

    st.table(df)

    st.write("Current Chain")

with rules_tab:
    st.markdown('''
                ## Rules of the game
                - Rule 1
                - Rule 2
                - Rule 3
                                    ''')
