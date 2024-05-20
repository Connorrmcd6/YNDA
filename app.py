from functions import *
from configs import *
import time
import streamlit as st
import  streamlit_toggle as tog


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
all_managers = fetch_manager_data(gs_connection, managers_table, prod_google_sheet_key, [])

# Filter active managers and sort their player names
active_managers = all_managers[all_managers.active == 'Yes']["player_name"].tolist()
active_managers.insert(0, "")
active_managers.sort()

# Sort all managers' player names
managers = all_managers["player_name"].tolist()
managers.insert(0, "")
managers.sort()


#this has a cache reset every 6 hours because people can nominate or uno reverse and the change should be reflected
drinks = fetch_drinks_data(gs_connection, drinks_table, prod_google_sheet_key, ['event','drink_size', 'start_time', 'end_time'])
drinks_display = build_drinks_display(drinks, current_week)
drinks_display.index = np.arange(1, len(drinks_display) + 1)

drinks_display_expanded = build_drinks_display_expanded(drinks)
drinks_display_expanded.index = np.arange(1, len(drinks_display_expanded) + 1)

litres, missed_pen_count, red_card_count, own_goal_count, nomination_count = analyze_drinks(drinks)
first_place, last_place, first_team_name = get_first_last(gameweek_df, current_gw, drinks)
red_cards, own_goals, missed_pen = get_illegible_nominees(drinks, current_gw)

#this has a cache reset every 6 hours because it can change during the week
uno_data = fetch_uno_data(gs_connection, managers_table, prod_google_sheet_key, [])
if needs_new_uno(uno_data,last_place) == True:
    give_new_uno(gs_connection, prod_google_sheet_key, uno_data, last_place)
    print(f"{last_place} got a new uno reverse card")
    fetch_uno_data.clear()
    uno_data = fetch_uno_data(gs_connection, managers_table, prod_google_sheet_key, [])
else:
    print("no one needed a new uno card this week")

uno_data_display = uno_data.iloc[:, [1, 4]].sort_values(["uno_reverse", "player_name"], ascending=(False, True))
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

update_time = time_since_last_update()

time_to_update = time_until_specified_time(update_time)

laps_df = build_laps(drinks)

rank_df = build_rank_df(gameweek_df, current_week)

#'''------------------------------------------------------------SIDE BAR------------------------------------------------------------'''

with st.sidebar:
    render_logo("assets/static/logo.svg")

with st.sidebar.expander("🎖️ Nominate Someone?", expanded=False):

    nominator = st.selectbox(label="Your Name", options=active_managers, key="nominate_name")

    nominee = st.selectbox("Nominate", active_managers)

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

            # elif nominee in red_cards:
            #     st.error("This person got a red card, pick someone else")

            # elif nominee in own_goals:
            #     st.error("This person got an own goal, pick someone else")

            # elif nominee in missed_pen:
            #     st.error("This person got negative points, pick someone else")

            # elif nominee == last_place:
            #     st.error("This person came last, pick someone else")

            else:
                with st.spinner(text="Submitting..."):
                    created_date = int(time.time()) + (60*60*2) # add two hours to adjust for server time
                    deadline_date = created_date + (7 * 24 * 60 * 60) + (60*60*2)

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
            st.error("Nominations have already been submitted for the week")

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
                    managers_temp = active_managers[:]
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

                    #incase halaand misses another pen and no one can nominate
                    if len(managers_temp) <= 3:
                        managers_temp = active_managers[:]
                        managers_temp.remove("")
                        managers_temp.remove(last_place)

                    # random_nominees = sample(managers_temp, random_choice_amount)
                    random_nominees = ["Alex Wietzorrek", "Cole Floyd", "Alex Wietzorrek", "Cole Floyd"]
                    random_choice_amount = 4
                    created_date = int(time.time()) + (60*60*2) # add two hours to adjust for server time
                    deadline_date = created_date + (7 * 24 * 60 * 60) + (60*60*2)

                    data = {
                        "event": [current_week]*random_choice_amount,
                        "nominator_name": [nominator]*random_choice_amount,
                        "drinker_name": random_nominees,
                        "drink_type": ["nomination"]*random_choice_amount,
                        "created_date": [created_date]*random_choice_amount,
                        "deadline_date": [deadline_date]*random_choice_amount,
                        "completed_date": ["Not Completed"]*random_choice_amount
                    }
                
                    df = pd.DataFrame(data)
                    write_google_sheets_data(
                        gs_connection, df, drinks_table, prod_google_sheet_key
                    )


                    for i in range(random_choice_amount):
                        st.text(f"{i+1}.{random_nominees[i]}")

                    st.success("Nomination Submitted")
        else:
            st.error("Nominations have already been submitted for the week")

with st.sidebar.expander("🍺 Submit a Drink?", expanded=False):


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

drinks_tab, stats_tab, awards_tab, rules_tab= st.tabs(
    ["Drinks", "Stats", "Awards", "Info"]
)


with drinks_tab.expander("🍺 Latest Drinks", expanded= True):
    
    if current_gw > 0 and finished and checked:
        render_svg_banner("assets/static/first_place_banner.svg", width=100, height=50, gw_number=current_gw, first_place_name=first_place, team_name=first_team_name)

    elif current_gw > 0 and (not finished or not checked):
        first_place, last_place, first_team_name = get_previous_first_last(gameweek_df, current_gw, drinks)
        render_svg_banner("assets/static/first_place_banner.svg", width=100, height=50, gw_number=(current_gw-1), first_place_name=first_place, team_name=first_team_name)

    drinks_toggle = tog.st_toggle_switch(label='See Drinks Details', 
                key="Key1", 
                default_value=False, 
                label_after = False, 
                inactive_color = '#69db67', 
                active_color="#984249", 
                track_color="#ff4c4b"
                )

    if drinks_toggle == True:
        st.table(drinks_display_expanded)
    else: 
        st.table(drinks_display)

        
with drinks_tab.expander("🔁 Uno Reverse Cards", expanded= False):
    st.markdown(""" #### Who still has their Uno reverse cards?""" , help="This table shows who still has an Uno reverse card, you can use this card once per season to give your drink back to the person that nominated you")
    st.table(uno_data_display)


with stats_tab:
    render_svg_summary("assets/static/summary_stats.svg", width=None, height=None, ls=litres, mps=missed_pen_count, rcs=red_card_count, ogs=own_goal_count, nms=nomination_count)


with stats_tab.expander("📊     Total Drinks", expanded= True):
    st.text("" , help="The chart below shows the number of drinks assigned to each person throughout the season")

    df = categories(drinks)
    domain = ['Completed', 'Late', 'Outstanding']
    range_ = ['#c62828', '	#ef9a8d', '#777777']

    bar_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X("Name:O", axis=alt.Axis(title="Name"), sort="-y"),
            alt.Y("sum(quantity):Q", axis=alt.Axis(title="Drinks")),
            alt.Order("sum(quantity):Q", sort="descending"),
            alt.Color(
                "Category:N",
                scale=alt.Scale(domain=domain, range=range_),
                legend=alt.Legend(orient="top", direction="horizontal", title=None),
            ),
        )
    )
    st.altair_chart(bar_chart, use_container_width=True)



if current_gw <= 1:
    league_rank_expand = False
if current_gw == 2 and not finished and not checked:
    league_rank_expand = False
else:
    league_rank_expand = True

with stats_tab.expander("📈     League Ranks", expanded = league_rank_expand):

    if current_gw <= 1:
        st.info("Wait until game week 2 finishes to see a chart here")
    if current_gw == 2 and not finished and not checked:
        st.info("Wait until game week 2 finishes to see a chart here")
    else:
        st.text("" , help="This shows player rank changes for the last 10 gameweeks")

        rank_chart = alt.Chart(rank_df).mark_line().encode(
                alt.X("event:O", axis=alt.Axis(title="Game Week")),
                alt.Y("rank:O", axis=alt.Axis(title="League Rank")),
                alt.Color(
                    "player_name:N",
                    scale=alt.Scale(scheme='category20'),
                    legend=alt.Legend(orient="bottom", columns=2, title=None),
                ),
            )

        st.altair_chart(rank_chart, use_container_width=True)

with stats_tab.expander("🏎️     Fastest Lap Times", expanded= False):
    st.markdown("""### 🏁 Tops at Spa Grand Prix""", help="Lap times are the time taken to complete a 330ml down. for example if you drank a 500ml in 5s your time will be listed as (330/500)x(5) = 3.3s")
    st.table(laps_df)

with awards_tab:
    (
        col1,
        col2,
    ) = st.columns(2)


    with col1:
        render_svg_metric("assets/static/golden_boot.svg", width=None, height=None, name=most_1st_place_player, metric_name="Golden Boot", value_str=f"{most_1st_place_count} first place finishes")
        render_svg_metric("assets/static/warrior.svg", width=None, height=None, name=most_last_place_player, metric_name="Relegation Warrior", value_str=f"{most_last_place_count} last place finishes")
        render_svg_metric("assets/static/bench.svg", width=None, height=None, name=player_with_highest_points_on_bench, metric_name="Warmest Bench" , value_str=f"{player_with_highest_points_on_bench_count} points on bench")


    with col2: 
        render_svg_metric("assets/static/big_hitter.svg", width=None, height=None, name=player_with_highest_cost, metric_name="Big Hitter", value_str=f"{player_with_highest_cost_count/4:.0f} hits taken" )
        render_svg_metric("assets/static/heavyweight.svg", width=None, height=None, name=most_litres_name, metric_name="Heavy Weight", value_str=f"{most_litres_qty}ℓ of beer consumed")
        render_svg_metric("assets/static/wooden_boot.svg", width=None, height=None, name=lowest_score_player_name, metric_name="Wooden Boot", value_str=f"{lowest_score_points} points in game week {lowest_score_event}")

with rules_tab.expander("✏️ Rules", expanded= False):
    st.markdown(
        """
                1. First place for each week can nominate one person of their choice or randomly nominate three people (with the chance of picking themselves).
                2. Last place for each week will be assigned a drink.
                3. If you have a player with a red card, own goal, or missed penalty in your :red[**final 11**], you will be assigned a drink.
                4. If you want to be included on the lap times leaderboard you will need to have a stop watch visibile in your video submission.
                5. Everyone gets one Uno reverse card per season. You can use this to give your drink back to the person that nominated you. As long as you do it within 2 days of nomination. You will gain an additional uno reverse if you come last. Uno reverse cards don't stack up, you can only have one at a time
                6. You can't Uno reverse someone else's Uno reverse.    
                """
    )



with rules_tab.expander("🤷🏻‍♂️ How to Nominate Submit a Drink or Uno Reverse ", expanded= False):
    st.markdown("""
                #### Nominating:
                1. Click the arrow on the top left to open the side bar.
                2. Click on the `🎖️ Nominate Someone` tab.
                3. Fill in your name, this is so we know who to give the drink to if one of your nominees decides to uno reverse.
                4. If you are choosing a specific person then select their name in the \"Nominate" box and click submit.
                5. If you are randomly nominating, just click the random button and send a screenshot to the group chat.

                ###
                #### Submitting:
                1. Send a video to the group chat of you downing your drink. You can include a stop watch if you want to be included in the Grand Prix (this is optional).
                2. Click the arrow on the top left to open the side bar.
                3. Click on the `🍺 Submit a Drink?` tab.
                4. Fill in your name and the size of your drink.
                5. Click `Submit`.

                ###
                #### Uno Reverse:
                1. Click the arrow on the top left to open the side bar.
                2. Click on the `🍺 Submit a Drink?` tab.
                3. Fill out your name.
                4. Click on the `Uno` button.
                """)
with rules_tab.expander("⏱️ Next Refresh", expanded= True):
    st.markdown(f"Data will be refreshed in: **{time_to_update}**", help="If you have submitted a drink or nominated someone and it hasn't shown up on the app it will be added when the data is next refreshed")

    if st.button('Manual Refresh'):
        update.clear()
        fetch_drinks_data.clear()
        build_drinks_display.clear()
        build_drinks_display_expanded.clear()
        fetch_uno_data.clear()
        most_litres.clear()
        build_laps.clear()
        time_since_last_update.clear()
        st.experimental_rerun()

    st.code(f'status:\ngame week finished: {finished}\ngame week data checked: {checked}')



end = time.time()
print(end - start)