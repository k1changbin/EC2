import json, time
import streamlit as st

@st.cache_data
def load_quiz():
    time.sleep(2)
    with open("data/quiz.json", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_players():
    time.sleep(2)
    with open("data/players.json", "r", encoding="utf-8") as f:
        return json.load(f)