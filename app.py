import streamlit as st
from functions import *

st.set_page_config(page_title='YNDA', layout='wide',
                   initial_sidebar_state='collapsed')

with st.sidebar:
    x = 1
    # names = get_names()
    # nominee = st.selectbox(
    #     'Pick a person to drink:',
    #     names)
    # if st.button("Update Dashboard"):
    #     # displays the nominee
    #     st.text(nominee)


regular_league, spacer1, upcoming_fixtures, spacer2, previous_results, spacer3, current_standings = st.columns([
    2, 0.1, 1, 0.05, 1, 0.05, 1])

with regular_league:
    st.markdown("Regular League")
    st.divider()

    metric_container = st.container()
    chart_1_container = st.container()
    chart_2_container = st.container()

    with metric_container:
        col1, col2, col3 = st.columns(3)

        # row 1
        col1.metric("Temperature", "70 °F", "1.2 °F")
        col2.metric("Wind", "9 mph", "-8%")
        col3.metric("Humidity", "86%", "4%")

        # row 2
        col1.metric("Temperature", "23 °C", "-4.8 °F")
        col2.metric("Wind", "16 kph", "+4%")
        col3.metric("Humidity", "65%", "-12%")
        st.divider()

    with chart_1_container:
        st.write("Total Drinks")
        st.bar_chart(np.random.randn(50, 3))
        st.divider()

    with chart_2_container:
        st.write("Rank Chart Last 10 Game Weeks")
        data = np.random.randn(10, 1)
        st.line_chart(data)

with upcoming_fixtures:
    st.markdown("Upcoming Fixtures")
    st.divider()

    df = pd.DataFrame(
        np.random.randn(20, 5),
        columns=('col %d' % i for i in range(5)))

    st.table(df)

with previous_results:
    st.markdown("Previous Results")
    st.divider()

    df = pd.DataFrame(
        np.random.randn(10, 5),
        columns=('col %d' % i for i in range(5)))

    st.table(df)

with current_standings:
    st.markdown("Current Standings")
    st.divider()

    df = pd.DataFrame(
        np.random.randn(10, 5),
        columns=('col %d' % i for i in range(5)))

    st.table(df)
