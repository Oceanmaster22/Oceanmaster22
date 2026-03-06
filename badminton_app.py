# ==========================================
# 🏸 Badminton Weekly League Manager
# ==========================================

import streamlit as st
import pandas as pd
import random
import os
from itertools import combinations
from datetime import datetime

st.set_page_config(page_title="🏸 Badminton League", layout="wide")
st.title("🏸 Weekly Badminton League Manager")

# ==========================================
# 📁 FILES
# ==========================================

SCHEDULE_FILE = "weekly_schedule.csv"
STATS_FILE = "player_stats.csv"

# Create files if missing
if not os.path.exists(SCHEDULE_FILE):
    pd.DataFrame(columns=[
        "Week_Key","Timestamp","Game",
        "Team 1","Team 2",
        "Team 1 Skill","Team 2 Skill",
        "Result"
    ]).to_csv(SCHEDULE_FILE, index=False)

if not os.path.exists(STATS_FILE):
    pd.DataFrame(columns=["Player","Wins","Losses"]).to_csv(STATS_FILE, index=False)

# ==========================================
# 👥 PLAYER MANAGEMENT (session only)
# ==========================================

st.sidebar.header("➕ Add Players")

if "players" not in st.session_state:
    st.session_state.players = {}

with st.sidebar.form("add_player"):
    name = st.text_input("Player Name")
    skill = st.slider("Skill Level", 1, 5, 3)
    submitted = st.form_submit_button("Add Player")

    if submitted and name:
        st.session_state.players[name] = skill
        st.success(f"{name} added!")
        st.rerun()

if st.session_state.players:
    remove_player = st.sidebar.selectbox(
        "Remove Player",
        ["None"] + list(st.session_state.players.keys())
    )

    if remove_player != "None":
        if st.sidebar.button("Remove Selected Player"):
            del st.session_state.players[remove_player]
            st.rerun()

players = list(st.session_state.players.keys())
skills = st.session_state.players

if players:
    st.subheader("👥 Current Players")
    st.table(pd.DataFrame({
        "Player": players,
        "Skill": [skills[p] for p in players]
    }))

# ==========================================
# 🗓 WEEK KEY
# ==========================================

def get_current_week():
    now = datetime.now()
    year, week, _ = now.isocalendar()
    return f"{year}-W{week}"

# ==========================================
# ⚖️ TEAM BALANCING
# ==========================================

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

def generate_5_games(players):
    players = players.copy()
    random.shuffle(players)

    game_counts = {p: 0 for p in players}
    used_teams = set()  # Track teams already used
    games = []

    attempts = 0
    max_attempts = 500

    while len(games) < 5 and attempts < max_attempts:
        attempts += 1

        possible_groups = list(combinations(players, 4))
        random.shuffle(possible_groups)

        for group in possible_groups:

            # Player max games condition
            if not all(game_counts[p] < 3 for p in group):
                continue

            team1, team2 = best_team_split(group)

            team1_sorted = tuple(sorted(team1))
            team2_sorted = tuple(sorted(team2))

            # 🚫 Prevent repeating same team
            if team1_sorted in used_teams or team2_sorted in used_teams:
                continue

            # Accept game
            games.append((team1, team2))

            used_teams.add(team1_sorted)
            used_teams.add(team2_sorted)

            for p in group:
                game_counts[p] += 1

            break

    return games

# ==========================================
# 🏸 GENERATE WEEK
# ==========================================

if len(players) >= 4:
    available = st.multiselect(
        "Select Available Players This Week",
        players,
        default=players
    )

    if st.button("🏸 Generate This Week's 5 Games"):
        if len(available) < 4:
            st.warning("Need at least 4 players.")
        else:
            week_key = get_current_week()
            history = pd.read_csv(SCHEDULE_FILE)

            if week_key in history["Week_Key"].values:
                st.warning("This week already generated!")
            else:
                games = generate_5_games(available)

                if len(games) < 5:
                    st.warning("Could not generate 5 fair games.")
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    rows = []
                    for i, (t1, t2) in enumerate(games, 1):
                        rows.append({
                            "Week_Key": week_key,
                            "Timestamp": timestamp,
                            "Game": f"Game {i}",
                            "Team 1": f"{t1[0]} & {t1[1]}",
                            "Team 2": f"{t2[0]} & {t2[1]}",
                            "Team 1 Skill": sum(skills[p] for p in t1),
                            "Team 2 Skill": sum(skills[p] for p in t2),
                            "Result": ""
                        })
                    updated = pd.concat([history, pd.DataFrame(rows)])
                    updated.to_csv(SCHEDULE_FILE, index=False)
                    st.success("5 Games Created!")
                    st.rerun()

# ==========================================
# 📅 WEEKLY GAMES
# ==========================================

st.subheader("📅 Weekly Games")
history = pd.read_csv(SCHEDULE_FILE)

# Force Result column to string to prevent Streamlit crash
if "Result" in history.columns:
    history["Result"] = history["Result"].astype(str)
    history["Result"] = history["Result"].replace("nan", "")

if not history.empty:
    edited = st.data_editor(
        history,
        num_rows="fixed",
        column_config={
            "Result": st.column_config.TextColumn(
                "Result (Team1-Team2)",
                help="Enter score like 21-18",
            )
        }
    )

    col1, col2 = st.columns(2)

    # ==========================================
    # 💾 SAVE RESULTS
    # ==========================================

    with col1:
        if st.button("💾 Save Results & Update Leaderboard"):
            edited.to_csv(SCHEDULE_FILE, index=False)

            # Recalculate leaderboard from scratch
            stats = {}
            for _, row in edited.iterrows():
                result = str(row["Result"]).replace(" ", "")
                if result and "-" in result:
                    try:
                        s1, s2 = map(int, result.split("-"))
                        team1 = row["Team 1"].split(" & ")
                        team2 = row["Team 2"].split(" & ")

                        if s1 > s2:
                            winners = team1
                            losers = team2
                        elif s2 > s1:
                            winners = team2
                            losers = team1
                        else:
                            continue

                        for p in winners:
                            stats.setdefault(p, {"Wins":0,"Losses":0})
                            stats[p]["Wins"] += 1
                        for p in losers:
                            stats.setdefault(p, {"Wins":0,"Losses":0})
                            stats[p]["Losses"] += 1
                    except:
                        continue

            stats_df = pd.DataFrame([
                {"Player": p, "Wins": v["Wins"], "Losses": v["Losses"]}
                for p, v in stats.items()
            ])
            stats_df.to_csv(STATS_FILE, index=False)
            st.success("Leaderboard Updated!")
            st.rerun()

    # ==========================================
    # 🗑 DELETE WEEK
    # ==========================================

    with col2:
        week_list = sorted(history["Week_Key"].unique())
        delete_week = st.selectbox("Select Week to Delete", ["None"] + week_list)
        if delete_week != "None":
            if st.button("🗑 Delete Selected Week"):
                updated_history = history[history["Week_Key"] != delete_week]
                updated_history.to_csv(SCHEDULE_FILE, index=False)
                st.success(f"{delete_week} deleted!")
                st.rerun()

# ==========================================
# 🏆 LEADERBOARD
# ==========================================

st.subheader("🏆 Leaderboard")

if os.path.exists(STATS_FILE):
    stats_df = pd.read_csv(STATS_FILE)
    if not stats_df.empty:
        stats_df = stats_df.sort_values("Wins", ascending=False)
        stats_df["Win %"] = (
            stats_df["Wins"] / (stats_df["Wins"] + stats_df["Losses"])
        ).fillna(0).round(2)
        st.table(stats_df)
        st.subheader("📊 Wins vs Losses")
        chart_data = stats_df.set_index("Player")[["Wins", "Losses"]]
        st.bar_chart(chart_data)
    else:
        st.info("No results yet.")

# ==========================================
# ⚠️ CLEAR LEADERBOARD
# ==========================================

st.subheader("⚠️ Leaderboard Management")
if st.button("🧹 Clear Leaderboard (Reset Wins/Losses)"):
    pd.DataFrame(columns=["Player","Wins","Losses"]).to_csv(STATS_FILE, index=False)
    st.success("Leaderboard cleared!")
    st.rerun()

