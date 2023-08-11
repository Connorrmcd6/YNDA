## You'll Never Drink Alone - Fantasy Premier League Drinking Game

The app pulls data from the [Fantasy Premier League Api](https://buildmedia.readthedocs.org/media/pdf/fpl/latest/fpl.pdf) to game-ify the mini league experience.
It use google sheets as a database and interacts with google drive using a service account

### Rules of the game

1. Each week the person that has the **highest scoring game week** will be allowed to allocate a drink to one player of their choice or randomly pick 3 (with the risk of choosing themselves).
2. Each week the person that has the **lowest scoring game week** will automatically be assigned a drink.
3. Any person who has a player with red card, own goal, or missed penalty in their **final 11**, will be assigned a drink.
4. Anyone that falls under points 2 and 3 **cannot** be nominated again until the next game week.
5. Every manager will get one "Uno reverse card" per season, you may use this to give your drink back to the person who nominated you. You have to do this within 48 hours of nomination.
6. You can't Uno reverse someone else's Uno reverse.
7. All drinks are to be completed within 7 days of the nomination.

### Features

- You can nominate and submit drinks on the app.
- You can uno reverse on the app.
- The app keeps track of who has and hasn't completed their drinks
- There are other insights that show league ranks over the last 10 game weeks
- An awards tab to show most frequent winner, most points on bench, most hits taken etc...

### Lap times (beta)

Essentially this feature is a list of the fastest time to complete a drink. Since we can't automate this in the app we require a stopwatch to be in the video submission. Then the admin of the app can manually add the start and stop time under the drinks tab on google sheets and the app will do the rest.

### Recomendations & Considerations:

- Be aware that the app uses a cache to help it load faster and provide a better user experience. Anything that doesnt change between game weeks such as first and last place will only update at the end of each game week. Drinks and Uno reverse cards can update during the time between game weeks due to nominations, submissions etc... **These will update every 6 hours** so if you don't see a nomination showing up in the latest drinks table, wait a few hours and check again.
- Create a group chat where you can submit videos of your drinks.
- Adjust the `random_choice_amount` in the configs.py file to suit your group size, (currently testing out 3 for a group of 20).

## Set up & Installation

### Google Service Account Setup

### Google Drive Setup

### Configs Setup

### Streamlit Setup
