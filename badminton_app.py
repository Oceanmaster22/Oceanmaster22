# ================================
# 🏸 Badminton Weekly Scheduler
# ================================

import streamlit as st
import pandas as pd
import random
import os
from itertools import combinations
from datetime import datetime

st.set_page_config(page_title="🏸 Badminton Scheduler", layout="wide")
st.title("🏸 Weekly Badminton Scheduler")

# ================================
# 📁 Persistent Storage File
# ================================

DATA_FILE = "weekly_schedule.csv"

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=[
        "Week_Key",
        "Timestamp",
        "Game",
        "Team 1",
        "Team 2",
        "Team 1 Skill",
        "Team 2 Skill",
        "Result"
    ]).to_csv(DATA_FILE, index=False)

# ================================
# 👥 Player Management
# ================================

st.sidebar.header("➕ Add Players")

if "players" not in st.session_state:
    st.session_state.players = {}

with st.sidebar.form("add_player_form"):
    name = st.text_input("Player Name")
    skill = st.slider("Skill Level", 1, 5, 3)
    submitted = st.form_submit_button("Add Player")

    if submitted and name:
        st.session_state.players[name] = skill
        st.success(f"{name} added!")

# Remove player
if st.session_state.players:
    remove_player = st.sidebar.selectbox(
        "Remove Player",
        ["None"] + list(st.session_state.players.keys())
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

# ================================
# 🗓 Week Helper
# ================================

def get_current_week():
    now = datetime.now()
    year, week, _ = now.isocalendar()
    return f"{year}-W{week}"

# ================================
# ⚖️ Team Balancing
# ================================

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

# ================================
# 🏸 Generate 5 Games Logic
# ================================

def generate_5_games(players):
    players = players.copy()
    random.shuffle(players)

    game_counts = {p: 0 for p in players}
    games = []

    while len(games) < 5:
        possible_groups = list(combinations(players, 4))
        random.shuffle(possible_groups)
        found = False

        for group in possible_groups:
            if all(game_counts[p] < 3 for p in group):
                team1, team2 = best_team_split(group)
                games.append((team1, team2))

                for p in group:
                    game_counts[p] += 1

                found = True
                break

        if not found:
            break

    return games

# ================================
# ✅ Availability Selection
# ================================

if len(players) >= 4:
    st.subheader("✅ Select Available Players This Week")
    available_players = st.multiselect(
        "Who is playing?",
        players,
        default=players
    )
else:
    available_players = []

# ================================
# 🏸 Generate Weekly Schedule
# ================================

if st.button("🏸 Generate This Week's 5 Games"):

    if len(available_players) < 4:
        st.warning("Need at least 4 available players.")
    else:
        week_key = get_current_week()
        history = pd.read_csv(DATA_FILE)

        existing = history[history["Week_Key"] == week_key]

        if not existing.empty:
            st.success(f"Games already generated for {week_key}")
            st.table(existing)
        else:
            games = generate_5_games(available_players)

            if len(games) < 5:
                st.warning("Could not generate 5 fair games.")
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_rows = []

                for i, (team1, team2) in enumerate(games, 1):
                    s1 = sum(skills[p] for p in team1)
                    s2 = sum(skills[p] for p in team2)

                    new_rows.append({
                        "Week_Key": week_key,
                        "Timestamp": timestamp,
                        "Game": f"Game {i}",
                        "Team 1": f"{team1[0]} & {team1[1]}",
                        "Team 2": f"{team2[0]} & {team2[1]}",
                        "Team 1 Skill": s1,
                        "Team 2 Skill": s2,
                        "Result": ""
                    })

                updated = pd.concat([history, pd.DataFrame(new_rows)])
                updated.to_csv(DATA_FILE, index=False)

                st.success(f"5 Games created for {week_key}")
                st.table(pd.DataFrame(new_rows))

# ================================
# 📅 Weekly History + Delete Option
# ================================

st.subheader("📅 Weekly History")

history = pd.read_csv(DATA_FILE)

if not history.empty:

    # Edit results
    edited = st.data_editor(history, num_rows="fixed")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Results"):
            edited.to_csv(DATA_FILE, index=False)
            st.success("Results saved successfully!")

    # Delete week option
    with col2:
        week_list = sorted(history["Week_Key"].unique())
        delete_week = st.selectbox("Select Week to Delete", ["None"] + week_list)

        if delete_week != "None":
            if st.button("🗑 Delete Selected Week"):
                updated_history = history[history["Week_Key"] != delete_week]
                updated_history.to_csv(DATA_FILE, index=False)
                st.success(f"{delete_week} deleted successfully!")
                st.rerun()

else:
    st.info("No games generated yet.")
