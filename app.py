import streamlit as st
from functions import *

st.set_page_config(page_title='YNDA',
                   layout='centered',
                   initial_sidebar_state='collapsed',
                   page_icon='🍺',
                   )


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
    col1.metric("Golden Boot", "Divyam Dixit",
                help='Most first place finishes over the season')

    col1.metric("Relegation Warrior", "Hethe Brinkman",
                help='Most last place finishes over the season')

    col1.metric("The Origi Award", "Devon Hodgson",
                help='Most bench points accumulated over the season')

    # column 2
    col2.metric("The Chelsea Award", "Connor McDonald",
                help='Most -4s (hits) accumulated over the season')

    col2.metric("Serial Streaker", "Cole Floyd",
                help='Longest drinks streak of the season')

    col2.metric("The Bot Award", "Ryan Shackleton",
                help='Lowest game week score of the season')


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
