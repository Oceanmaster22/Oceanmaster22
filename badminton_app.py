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
    st.info("Add at least 4 players to generate a team.")

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
# 🏸 Generate Weekly Team
# ================================

if st.button("🏸 Generate This Week's Team"):

    if len(available_players) < 4:
        st.warning("Need at least 4 available players.")
    else:
        week_key = get_current_week()
        history = pd.read_csv(DATA_FILE)

        existing = history[history["Week_Key"] == week_key]

        if not existing.empty:
            st.success(f"Team already generated for {week_key}")
            st.table(existing)
        else:
            group = random.sample(available_players, 4)
            team1, team2 = best_team_split(group)

            s1 = sum(skills[p] for p in team1)
            s2 = sum(skills[p] for p in team2)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            new_row = pd.DataFrame([{
                "Week_Key": week_key,
                "Timestamp": timestamp,
                "Team 1": f"{team1[0]} & {team1[1]}",
                "Team 2": f"{team2[0]} & {team2[1]}",
                "Team 1 Skill": s1,
                "Team 2 Skill": s2,
                "Result": ""
            }])

            updated = pd.concat([history, new_row])
            updated.to_csv(DATA_FILE, index=False)

            st.success(f"Team created for {week_key}")
            st.table(new_row)

# ================================
# 📅 Show Weekly History
# ================================

st.subheader("📅 Weekly History")

history = pd.read_csv(DATA_FILE)

if not history.empty:

    edited = st.data_editor(history, num_rows="fixed")

    if st.button("💾 Save Results"):
        edited.to_csv(DATA_FILE, index=False)
        st.success("Results saved successfully!")

else:
    st.info("No teams generated yet.")
