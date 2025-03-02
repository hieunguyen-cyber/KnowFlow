import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
GOOGLE_API_KEY = st.secrets["secrets"]["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

for model in genai.list_models():
    print(model)