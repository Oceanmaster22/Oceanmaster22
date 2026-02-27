# File: badminton_app.py
import random
from itertools import combinations
import streamlit as st
import pandas as pd

st.set_page_config(page_title="🏸 Badminton Scheduler", layout="wide")
st.title("🏸 Weekly Badminton Scheduler")

# Players and skill points (1-5)
names = ['Benji','Gopika','Ioannis','Jazzi','Kamal','Simon','Sooraj']
skills = {
    'Benji': 3,
    'Gopika': 2,
    'Ioannis': 2,
    'Jazzi': 5,
    'Kamal': 4,
    'Simon': 3,
    'Sooraj': 3
}

def best_team_split(group):
    """Return the most balanced 2v2 split based on skill."""
    best_diff = float('inf')
    best_pairing = None
    for team1 in combinations(group, 2):
        team2 = tuple(p for p in group if p not in team1)
        skill1 = sum(skills[p] for p in team1)
        skill2 = sum(skills[p] for p in team2)
        diff = abs(skill1 - skill2)
        if diff < best_diff:
            best_diff = diff
            best_pairing = (team1, team2)
    return best_pairing

def generate_week(players):
    players = players.copy()
    random.shuffle(players)
    game_counts = {p: 0 for p in players}
    games = []
    
    while len(games) < 5:
        possible = list(combinations(players, 4))
        random.shuffle(possible)
        found_game = False
        for group in possible:
            if all(game_counts[p] < 3 for p in group):
                team1, team2 = best_team_split(group)
                games.append((team1, team2))
                for p in group:
                    game_counts[p] += 1
                found_game = True
                break
        if not found_game:
            break
    return games, game_counts

# Button to generate schedule
if st.button("Generate This Week's Games"):
    games, counts = generate_week(names)
    
    # Display games in a table
    game_list = []
    for i, (t1, t2) in enumerate(games, 1):
        s1 = sum(skills[p] for p in t1)
        s2 = sum(skills[p] for p in t2)
        game_list.append({
            "Game": f"Game {i}",
            "Team 1": f"{t1[0]} & {t1[1]}",
            "Team 1 Skill": s1,
            "Team 2": f"{t2[0]} & {t2[1]}",
            "Team 2 Skill": s2
        })
    df_games = pd.DataFrame(game_list)
    st.subheader("🏸 This Week's Games")
    st.table(df_games)
    
    # Display game count per player
    st.subheader("Game Count Per Player")
    df_counts = pd.DataFrame({
        "Player": list(counts.keys()),
        "Games Played": list(counts.values())
    })

    st.table(df_counts)
