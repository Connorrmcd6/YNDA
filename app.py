from functions import *
from configs import *
import time


#'''------------------------------------------------------------PAGE CONFIGS------------------------------------------------------------'''
st.set_page_config(
    page_title="YNDA",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="🍺",
)
start = time.time()
#'''------------------------------------------------------------CACHE------------------------------------------------------------'''

#'''------------------------------------------------------------cached resources------------------------------------------------------------'''
gs_connection = connect_to_gs(st.secrets["gcp_service_account"])
#fpl session here if needed



#'''------------------------------------------------------------cached data------------------------------------------------------------'''

#caching data
max_stored_gw = fetch_max_gw(gs_connection, gameweek_results_table, google_sheet_key)
current_week = 38 #
#find event number of is_current week:

if max_stored_gw > current_week:
    #update data from fpl
    print('couldnt fetch data from fpl')
else:
    gameweek_df = fetch_gameweek_data(
        gs_connection,
        gameweek_results_table,
        google_sheet_key,
        ["event", "points", "total_points", "event_transfers_cost", "points_on_bench"],
    )
    

drinks = fetch_drinks_data(gs_connection, drinks_table, google_sheet_key, ['event','drink_size', 'start_time', 'end_time'])

drinks_display = build_drinks_display(drinks, current_week)
drinks_display.index = np.arange(1, len(drinks_display) + 1)


managers = sorted(fetch_manager_data(gs_connection, managers_table, google_sheet_key, [])["player_name"])
managers.insert(0, "")

uno_data = fetch_uno_data(gs_connection, managers_table, google_sheet_key, [])
uno_data_display = uno_data.iloc[:, [1, 3]].sort_values(["uno_reverse", "player_name"], ascending=(False, True))
uno_data_display.rename(columns={"player_name": "Name", "uno_reverse": "Has Uno Reverse"}, inplace=True)
uno_data_display.index = np.arange(1, len(uno_data) + 1)


(
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
) = create_metrics(gameweek_df)



#'''------------------------------------------------------------WORK IN PROGRESS-----------------------------------------------------------'''



if "last_place" not in st.session_state:
    last_place = "Alex Wietzorrek"  # change to function
    st.session_state.last_place = last_place
else:
    last_place = st.session_state.last_place



if "first_place" not in st.session_state:
    first_place = "Ryan Shacks"  # change to function
    st.session_state.first_place = first_place
else:
    first_place = st.session_state.first_place



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


#'''------------------------------------------------------------SIDE BAR------------------------------------------------------------'''
with st.sidebar:
    # capture week of nomination from backend
    st.header("🎖️ Nominations")

    nominator = st.selectbox(label="Your Name", options=managers, key="nominate_name")

    nominee = st.selectbox("Nominate", managers)

    if st.button(label="Submit", key="nominate_submit"):
        if "nominate" not in st.session_state:
            if not select_box_validator(nominator):
                st.error("Please fill in your name")

            elif not select_box_validator(nominee):
                st.error("Please select a person to nominate")

            elif nominator == nominee:
                st.error("You can't nominate yourself")

            elif nominator != st.session_state.first_place:
                st.error("You did not win the Game Week")

            elif nominee in st.session_state.red_cards:
                st.error("This person got a red card, pick someone else")

            elif nominee in st.session_state.own_goals:
                st.error("This person got an own goal, pick someone else")

            elif nominee in st.session_state.negative_points:
                st.error("This person got negative points, pick someone else")

            elif nominee == st.session_state.last_place:
                st.error("This person came last, pick someone else")

            else:
                with st.spinner(text="Submitting..."):
                    created_date = (datetime.now() + timedelta(hours=2)).strftime(
                        "%d/%m/%y %H:%M:%S"
                    )
                    deadline_date = (
                        datetime.now() + timedelta(hours=2) + timedelta(days=7)
                    ).strftime("%d/%m/%y %H:00")

                    data = {
                        "event": [current_week],
                        "nominator_name": [nominator],
                        "drinker_name": [nominee],
                        "drink_type": ["nomination"],
                        "created_date": [created_date],
                        "deadline_date": [deadline_date],
                        "completed_date": ["Not Completed"],
                    }

                    df = pd.DataFrame(data)
                    write_google_sheets_data(
                        gs_connection, df, drinks_table, google_sheet_key
                    )
                    st.session_state.nominate = True
                    st.success("Nomination Submitted")
        else:
            st.error("You have already nominated")

    st.header("OR")

    if st.button("🔄 Randomly pick 3"):
        if "nominate" not in st.session_state:
            if not select_box_validator(nominator):
                st.error("Please fill in your name")
            elif nominator != st.session_state.first_place:
                st.error("You did not win the Game Week")
            else:
                with st.spinner(text="Picking..."):

                    # remove "" and remove last_place
                    managers_temp = managers[:]
                    managers_temp.remove("")
                    managers_temp.remove(last_place)

                    if len(red_cards) > 0:
                        managers_temp = [i for i in managers_temp if i not in red_cards]

                    if len(own_goals) > 0:
                        managers_temp = [i for i in managers_temp if i not in own_goals]

                    if len(negative_points) > 0:
                        managers_temp = [
                            i for i in managers_temp if i not in negative_points
                        ]

                    random_nominees = sample(managers_temp, 3)
                    created_date = (datetime.now() + timedelta(hours=2)).strftime(
                        "%d/%m/%y %H:%M:%S"
                    )
                    deadline_date = (
                        datetime.now() + timedelta(hours=2) + timedelta(days=7)
                    ).strftime("%d/%m/%y %H:00")

                    data = {
                        "event": [current_week, current_week, current_week],
                        "nominator_name": [nominator, nominator, nominator],
                        "drinker_name": random_nominees,
                        "drink_type": ["nomination", "nomination", "nomination"],
                        "created_date": [created_date, created_date, created_date],
                        "deadline_date": [deadline_date, deadline_date, deadline_date],
                        "completed_date": [
                            "Not Completed",
                            "Not Completed",
                            "Not Completed",
                        ],
                    }
                
                    df = pd.DataFrame(data)
                    write_google_sheets_data(
                        gs_connection, df, drinks_table, google_sheet_key
                    )

                    st.session_state.nominate = True

                    st.text(f"1.{random_nominees[0]}")
                    st.text(f"2.{random_nominees[1]}")
                    st.text(f"3.{random_nominees[2]}")
                    st.success("Nomination Submitted")
        else:
            st.error("You have already nominated")

    st.divider()

    st.header("🍺 Submissions")

    drink_submitter = st.selectbox(
        label="Your Name", options=managers, key="submit_name"
    )

    drink_size = st.text_input(
        label="Drink Size (ml)", key="drink_size", value=330,
    )
    button_container = st.container()
    with button_container:
        left_button, right_button = st.columns([1, 1])
        with left_button:
            if st.button(label="Submit", key="drink_submit"):
                with st.spinner(text="Submitting..."):
                    r = submit_drink(
                        gs_connection,
                        drinks,
                        google_sheet_key,
                        drink_submitter,
                        drink_size,
                    )

                    if r == None:
                        st.success("Done")
                    else:
                        st.error(r)
        with right_button:
            if st.button(label="🫵 Uno", key="uno_reverse"):
                if not select_box_validator(drink_submitter):
                    st.error("Please fill in your name")
                else:
                    with st.spinner(text="Reversing..."):
                        r = uno_reverse(
                            gs_connection,
                            drinks,
                            uno_data,
                            google_sheet_key,
                            drink_submitter,
                        )
                        if r == None:
                            st.success("Done")
                        else:
                            st.error(r)

# '''------------------------------------------------------------APP------------------------------------------------------------'''
drinks_tab, stats_tab, awards_tab, rules_tab = st.tabs(
    ["🍺 Drinks", "📈 Stats", "🏆 Awards", "ℹ️ Rules"]
)


with drinks_tab:
    st.header("Latest Drinks")
    st.table(drinks_display)

    st.header("Uno Reverse Cards 🫵 🔄")
    st.table(uno_data_display)

with stats_tab:
    st.header(
        "Total Drinks",
        help="Number of drinks completed on time, completed late and not completed for each person",
    )
    if "drinks_chart" not in st.session_state:
        df = categories(drinks)
        st.session_state.drinks_chart = df
    else:
        df = st.session_state.drinks_chart

    bar_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X("Name:O", axis=alt.Axis(title="Name"), sort="-y"),
            alt.Y("sum(quantity):Q", axis=alt.Axis(title="Total Drinks")),
            alt.Order("sum(quantity):Q", sort="descending"),
            alt.Color(
                "Category:N",
                legend=alt.Legend(orient="top", direction="horizontal", title=None),
            ),
        )
    )
    st.altair_chart(bar_chart, use_container_width=True)

    st.header(
        "League Ranks",
        help="Each line represents a player, the higher the line the higher your rank in the league",
    )

    if "rank_chart" not in st.session_state:
        rank_df = build_rank_df(gameweek_df, current_week)
        st.session_state.rank_chart = rank_df
    else:
        rank_df = st.session_state.rank_chart

    rank_chart = alt.layer(
        alt.Chart(rank_df)
        .mark_line()
        .encode(
            alt.X("event:O", axis=alt.Axis(title="Game Week")),
            alt.Y("rank:O", axis=alt.Axis(title="League Rank")),
            alt.Color(
                "player_name:N",
                legend=alt.Legend(orient="bottom", columns=2, title=None),
            ),
        )
    ).interactive()

    st.altair_chart(rank_chart, use_container_width=True)

    st.header("Fastest Lap Times")
    
    st.table(build_laps(drinks))

with awards_tab:
    (
        col1,
        col2,
    ) = st.columns(2)

    # column 1
    col1.metric(
        "The Golden Boot",
        f"{most_1st_place_player}",
        help=f"{most_1st_place_player} has the most first place finishes ({most_1st_place_count} times)",
    )

    col1.metric(
        "The Relegation Warrior",
        f"{most_last_place_player}",
        help=f"{most_last_place_player} has the most last place finishes ({most_last_place_count} times)",
    )

    col1.metric(
        "The Warmest Bench",
        f"{player_with_highest_points_on_bench}",
        help=f"{player_with_highest_points_on_bench} has accumulated the most bench points ({player_with_highest_points_on_bench_count} points)",
    )
    # column 2
    col2.metric(
        "The Big Hitter",
        f"{player_with_highest_cost}",
        help=f"{player_with_highest_cost} has taken the most hits ({player_with_highest_cost_count} points)",
    )

    col2.metric(
        "The Speed Demon",
        "Cole Floyd",
        help=f"Cole Floyd has the fastest time complete a nominination (1 day 3 hours)",
    )

    col2.metric(
        "The Wooden Boot",
        f"{lowest_score_player_name}",
        help=f"{lowest_score_player_name} had the worst game week of the season (game week {lowest_score_event}: {lowest_score_points} points)",
    )


with rules_tab:
    st.markdown(
        """
                ## Rules of the game
                1. The winner of each week can nominate one person of their choice or randomly nominate three people (with the chance of picking themselves).
                2. Anyone who finishes last, or has a player that got a red card, scored an own goal or finished with negative points in their :red[**final 11**] will automatically be assigned a drink.
                3. Anyone who falls under point two will be immune from further nominations for that game week.
                4. At the start of the season everyone is given :red[**one**] "Uno Reverse Card". You can use this card to give a drink back to the person that nominated you if you do it :red[**before**] the deadline. 
                5. You can't Uno Reverse someone else's Uno Reverse.                    
                """
    )
end = time.time()
print(end - start)