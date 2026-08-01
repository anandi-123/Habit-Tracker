import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Habit Tracker",
    page_icon="🔥",
    layout="centered"
)

# ---------- FILES ----------
HABITS_FILE = "habits.csv"
COMPLETIONS_FILE = "completions.csv"

if not os.path.exists(HABITS_FILE):
    pd.DataFrame(columns=["name", "description", "created_date"]).to_csv(HABITS_FILE, index=False)

if not os.path.exists(COMPLETIONS_FILE):
    pd.DataFrame(columns=["habit_name", "date"]).to_csv(COMPLETIONS_FILE, index=False)

# ---------- FUNCTIONS ----------
def load_habits():
    try:
        df = pd.read_csv(HABITS_FILE)
        if df.empty or len(df.columns) == 0:
            return []
        return df.to_dict("records")
    except:
        return []

def save_habits(habits):
    pd.DataFrame(habits).to_csv(HABITS_FILE, index=False)

def load_completions():
    try:
        df = pd.read_csv(COMPLETIONS_FILE)
        if df.empty or len(df.columns) == 0:
            return pd.DataFrame(columns=["habit_name", "date"])
        return df
    except:
        return pd.DataFrame(columns=["habit_name", "date"])

def save_completion(habit_name):
    df = load_completions()
    new_row = pd.DataFrame([{"habit_name": habit_name, "date": str(date.today())}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(COMPLETIONS_FILE, index=False)

def is_completed_today(habit_name):
    df = load_completions()
    today = str(date.today())
    return ((df["habit_name"] == habit_name) & (df["date"] == today)).any()

def get_streak(habit_name):
    df = load_completions()
    habit_dates = df[df["habit_name"] == habit_name]["date"].tolist()
    habit_dates = sorted(set(habit_dates), reverse=True)  # latest first

    if not habit_dates:
        return 0

    streak = 0
    current_day = date.today()

    for d in habit_dates:
        try:
            completion_date = date.fromisoformat(d)
        except:
            continue

        if completion_date == current_day:
            streak += 1
            current_day -= timedelta(days=1)
        elif completion_date == current_day - timedelta(days=1):
            # gap of 1 day allowed only if today not completed yet
            streak += 1
            current_day = completion_date - timedelta(days=1)
        else:
            break

    return streak

def delete_habit(habit_name):
    habits = load_habits()
    habits = [h for h in habits if h["name"] != habit_name]
    save_habits(habits)

    df = load_completions()
    df = df[df["habit_name"] != habit_name]
    df.to_csv(COMPLETIONS_FILE, index=False)

def update_habit(old_name, new_name, new_description):
    habits = load_habits()
    for h in habits:
        if h["name"] == old_name:
            h["name"] = new_name
            h["description"] = new_description
    save_habits(habits)

    df = load_completions()
    df.loc[df["habit_name"] == old_name, "habit_name"] = new_name
    df.to_csv(COMPLETIONS_FILE, index=False)

def get_last_7_days_data():
    df = load_completions()
    today = date.today()
    days = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    
    counts = []
    for d in days:
        count = len(df[df["date"] == d])
        counts.append(count)
    
    chart_df = pd.DataFrame({
        "Date": [date.fromisoformat(d).strftime("%d %b") for d in days],
        "Completed": counts
    })
    return chart_df

# ---------- LOAD DATA ----------
habits = load_habits()

# ---------- HEADER ----------
st.title("🔥 Habit Tracker")
st.caption("Build better habits, one day at a time.")

# ---------- TODAY'S PROGRESS ----------
total = len(habits)
completed = sum(1 for h in habits if is_completed_today(h["name"]))

st.markdown(f"### Today's Progress: **{completed} / {total}** completed")
if total > 0:
    st.progress(completed / total)
else:
    st.progress(0)

st.divider()

# ---------- ADD NEW HABIT ----------
with st.expander("➕ Add New Habit", expanded=False):
    with st.form("add_habit_form", clear_on_submit=True):
        name = st.text_input("Habit Name")
        description = st.text_input("Description (optional)")
        submitted = st.form_submit_button("Add Habit")

        if submitted:
            if name.strip() == "":
                st.warning("Habit name cannot be empty.")
            else:
                new_habit = {
                    "name": name.strip(),
                    "description": description.strip(),
                    "created_date": str(date.today())
                }
                habits.append(new_habit)
                save_habits(habits)
                st.success("Habit added!")
                st.rerun()

st.divider()

# ---------- HABITS LIST ----------
st.subheader("Your Habits")

if len(habits) == 0:
    st.info("No habits yet. Add your first habit above.")
else:
    for habit in habits:
        col1, col2, col3 = st.columns([5, 2, 2])

        with col1:
            st.markdown(f"**{habit['name']}**")
            if habit.get("description"):
                st.caption(habit["description"])
            
            # Streak
            streak = get_streak(habit["name"])
            st.caption(f"🔥 Current Streak: **{streak} day{'s' if streak != 1 else ''}**")

        with col2:
            if is_completed_today(habit["name"]):
                st.success("Done ✓")
            else:
                if st.button("Mark Done", key=f"done_{habit['name']}"):
                    save_completion(habit["name"])
                    st.rerun()

        with col3:
            if st.button("Edit", key=f"edit_{habit['name']}"):
                st.session_state.editing = habit["name"]
            if st.button("Delete", key=f"delete_{habit['name']}"):
                delete_habit(habit["name"])
                st.rerun()

        # Edit Form
        if st.session_state.get("editing") == habit["name"]:
            with st.form(key=f"edit_form_{habit['name']}"):
                new_name = st.text_input("New Name", value=habit["name"])
                new_desc = st.text_input("New Description", value=habit.get("description", ""))
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.form_submit_button("Save"):
                        if new_name.strip():
                            update_habit(habit["name"], new_name.strip(), new_desc.strip())
                            st.session_state.editing = None
                            st.rerun()
                with col_b:
                    if st.form_submit_button("Cancel"):
                        st.session_state.editing = None
                        st.rerun()

        st.divider()

# ---------- CHART ----------
st.subheader("Last 7 Days Progress")

chart_data = get_last_7_days_data()

import altair as alt

chart = alt.Chart(chart_data).mark_bar(
    cornerRadiusTopLeft=6,
    cornerRadiusTopRight=6,
    color="#FF4B4B"
).encode(
    x=alt.X("Date:N", title="Date", sort=None),
    y=alt.Y("Completed:Q", title="Habits Completed"),
    tooltip=["Date", "Completed"]
).properties(
    height=350
)

st.altair_chart(chart, use_container_width=True)
st.caption("Number of habits completed each day")