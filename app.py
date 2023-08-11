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
#cached indefinitely
gs_connection = connect_to_gs(st.secrets["gcp_service_account"])

#'''------------------------------------------------------------cached data------------------------------------------------------------'''


#the result of the update function is cached for 6 hours 
update_flag, current_gw, finished, checked = update(gs_connection)

if update_flag == True:
    print('There is new data, google sheets will be updated now')
    #update functions
    manager_details = managers_update(gs_connection, league_endpoint, current_gw)
    gameweek_results_update(gs_connection, current_gw, manager_details)
    auto_assign_drinks(gs_connection, gameweek_results_table, gameweek_teams_table, prod_google_sheet_key, current_gw)
    st.cache_data.clear()         #<--- makes sure functions below are rerun 


#make this cache indefintely and reset on update
current_week = fetch_max_gw(gs_connection, gameweek_results_table, prod_google_sheet_key)

#make this cache indefintely and reset on update
gameweek_df = fetch_gameweek_data(
        gs_connection,
        gameweek_results_table,
        prod_google_sheet_key,
        ["event", "points", "total_points", "event_transfers_cost", "points_on_bench"],)
    

#make this cache indefintely and reset on update
managers = sorted(fetch_manager_data(gs_connection, managers_table, prod_google_sheet_key, [])["player_name"])
managers.insert(0, "")


#this has a cache reset every 6 hours because people can nominate or uno reverse and the change should be reflected
drinks = fetch_drinks_data(gs_connection, drinks_table, prod_google_sheet_key, ['event','drink_size', 'start_time', 'end_time'])
drinks_display = build_drinks_display(drinks, current_week)
drinks_display.index = np.arange(1, len(drinks_display) + 1)


first_place, last_place = get_first_last(gameweek_df, current_gw)
red_cards, own_goals, missed_pen = get_illegible_nominees(drinks, current_gw)

#this has a cache reset every 6 hours because it can change during the week
uno_data = fetch_uno_data(gs_connection, managers_table, prod_google_sheet_key, [])
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

#this can change if someone submits so it should have a cache of 6 hours
most_litres_name, most_litres_qty = most_litres(drinks,"drinker_name", 'drink_size')

nominate_flag = can_nominate_flag(drinks, current_gw, first_place)
#'''------------------------------------------------------------SIDE BAR------------------------------------------------------------'''
with st.sidebar:
    # capture week of nomination from backend
    st.header("🎖️ Nominations")

    nominator = st.selectbox(label="Your Name", options=managers, key="nominate_name")

    nominee = st.selectbox("Nominate", managers)

    if st.button(label="Submit", key="nominate_submit"):
        if nominate_flag == True:
            if not select_box_validator(nominator):
                st.error("Please fill in your name")

            elif not select_box_validator(nominee):
                st.error("Please select a person to nominate")

            elif nominator == nominee:
                st.error("You can't nominate yourself")

            elif nominator != first_place:
                st.error("You did not win the Game Week")

            elif nominee in red_cards:
                st.error("This person got a red card, pick someone else")

            elif nominee in own_goals:
                st.error("This person got an own goal, pick someone else")

            elif nominee in missed_pen:
                st.error("This person got negative points, pick someone else")

            elif nominee == last_place:
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
                        gs_connection, df, drinks_table, prod_google_sheet_key
                    )
                    st.success("Nomination Submitted")
        else:
            st.error("You have already nominated this week")

    st.header("OR")

    if st.button(f"Randomly pick {random_choice_amount}"):
        if nominate_flag == True:
            if not select_box_validator(nominator):
                st.error("Please fill in your name")
            elif nominator != first_place:
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

                    if len(missed_pen) > 0:
                        managers_temp = [
                            i for i in managers_temp if i not in missed_pen
                        ]

                    random_nominees = sample(managers_temp, random_choice_amount)
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
                        gs_connection, df, drinks_table, prod_google_sheet_key
                    )


                    for i in range(random_choice_amount):
                        st.text(f"{i}.{random_nominees[i]}")

                    st.success("Nomination Submitted")
        else:
            st.error("You have already nominated this week")

    st.divider()

    st.header("🍺 Submit Drinks")

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
                        prod_google_sheet_key,
                        drink_submitter,
                        drink_size,
                    )

                    if r == None:
                        st.success("Done")
                    else:
                        st.error(r)
        with right_button:
            if st.button(label="Uno", key="uno_reverse"):
                if not select_box_validator(drink_submitter):
                    st.error("Please fill in your name")
                else:
                    with st.spinner(text="Reversing..."):
                        r = uno_reverse(
                            gs_connection,
                            drinks,
                            uno_data,
                            prod_google_sheet_key,
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
    st.header("Latest Drinks",
              help='Drinks for the last 2 game weeks')
    if current_gw > 0 and finished and checked:
        st.write(f"Game week {current_gw} Winner: {first_place}")

    st.table(drinks_display)

    st.header("Uno Reverse Cards",
              help='List of players and if they have used their uno reverse card or not')
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
        help="Each line represents a player, the higher the line the higher your rank in the league for that game week",
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

    st.header("Fastest Lap Times",
              help="Time to complete a down scaled to 330mls ex. if you drank a 500ml in 5s your time will be listed as (330/500)x(5) = 3.3s")
    
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
        help=f"{player_with_highest_cost} has taken the most hits ({player_with_highest_cost_count/4:.0f} hits)",
    )

    col2.metric(
        "The Heavyweight",
        f"{most_litres_name}",
        help=f"{most_litres_name} has drank the most litres of beer this season ({most_litres_qty}ℓ)",
    )

    col2.metric(
        "The Wooden Boot",
        f"{lowest_score_player_name}",
        help=f"{lowest_score_player_name} had the worst game week of the season ({lowest_score_points} points in game week {lowest_score_event})",
    )

with rules_tab:
    st.markdown(
        """
                ## Rules of the game
                1. First place for each week can nominate one person of their choice or randomly nominate three people (with the chance of picking themselves).
                2. Last place for each week will be assigned a drink.
                3. If you have a player with a red card, own goal, or missed penalty in your :red[**final 11**], you will be assigned a drink.
                4. If you want to be included on the lap times leaderboard you will need to have a stop watch visibile in your video submission.
                5. Everyone gets one Uno reverse card per season. You can use this to give your drink back to the person that nominated you. As long as you do it within 2 days of nomination.
                6. You can't Uno reverse someone else's Uno reverse.    
                """
    )
end = time.time()
print(end - start)