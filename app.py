import streamlit as st
from functions import *

st.set_page_config(page_title='YNDA', layout='wide',
                   initial_sidebar_state='collapsed')

with st.sidebar:
    names = get_names()
    nominee = st.selectbox(
        'Pick a person to drink:',
        names)
    if st.button("Update Dashboard"):
        # displays the nominee
        st.text(nominee)


regular_league, spacer1, upcoming_fixtures, spacer2, previous_results, spacer3, current_standings = st.columns([
    2, 0.1, 1, 0.05, 1, 0.05, 1])

with regular_league:
    st.markdown("Regular League")
    st.divider()

    with st.container():
        st.write("This is inside the container")

        # You can call any Streamlit command, including custom components:
        st.bar_chart(np.random.randn(50, 3))

        st.write("This is outside the container")

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
