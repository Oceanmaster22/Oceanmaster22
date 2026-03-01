# File: badminton_app.py
import random
from itertools import combinations
import streamlit as st
import pandas as pd

st.set_page_config(page_title="🏸 Badminton Scheduler", layout="wide")
st.title("🏸 Weekly Badminton Scheduler")

st.sidebar.header("➕ Add Players")

# Store players in session state
if "players" not in st.session_state:
    st.session_state.players = {}

# Add player form
with st.sidebar.form("add_player"):
    name = st.text_input("Player Name")
    skill = st.slider("Skill Level", 1, 5, 3)
    submitted = st.form_submit_button("Add Player")

    if submitted and name:
        st.session_state.players[name] = skill
        st.success(f"{name} added!")

# Remove player option
if st.session_state.players:
    remove_player = st.sidebar.selectbox(
        "Remove Player", ["None"] + list(st.session_state.players.keys())
    )
    if remove_player != "None":
        if st.sidebar.button("Remove Selected Player"):
            del st.session_state.players[remove_player]
            st.sidebar.success(f"{remove_player} removed!")

players = list(st.session_state.players.keys())
skills = st.session_state.players

st.subheader("👥 Current Players")
if players:
    st.table(pd.DataFrame({
        "Player": players,
        "Skill": [skills[p] for p in players]
    }))
else:
    st.info("Add at least 4 players to generate games.")

# Availability selection
if len(players) >= 4:
    st.subheader("✅ Select Available Players for This Week")
    available_players = st.multiselect(
        "Who is playing this week?",
        players,
        default=players
    )
else:
    available_players = []

def best_team_split(group):
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

# Generate schedule
if st.button("🏸 Generate This Week's Games"):
    if len(available_players) < 4:
        st.warning("Need at least 4 available players!")
    else:
        games, counts = generate_week(available_players)

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

        st.subheader("🏸 This Week's Games")
        st.table(pd.DataFrame(game_list))

        st.subheader("📊 Game Count Per Player")
        st.table(pd.DataFrame({
            "Player": list(counts.keys()),
            "Games Played": list(counts.values())
        }))
