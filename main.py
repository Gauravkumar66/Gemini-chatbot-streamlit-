
import os
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

st.set_page_config(
    page_title="Gemini AI Chatbot",
    page_icon="🧠",
    layout="centered"
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    try:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    except (KeyError, FileNotFoundError):
        st.error("Gemini API key not configured.")
        st.stop()
MODEL_NAME = "gemini-2.5-flash"

if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY not found. Check your .env file.")
    st.stop()

def initialize_gemini():
    st.session_state.gemini_client_v2 = genai.Client(
        api_key=GOOGLE_API_KEY,
        http_options=types.HttpOptions(timeout=120000)
    )
    st.session_state.chat_v2 = st.session_state.gemini_client_v2.chats.create(
        model=MODEL_NAME
    )

if "gemini_client_v2" not in st.session_state or "chat_v2" not in st.session_state:
    initialize_gemini()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🧠 Gemini AI Chatbot")
st.caption("Powered by Google Gemini")

if st.button("Clear Chat"):
    st.session_state.messages = []
    initialize_gemini()
    st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_prompt = st.chat_input("Ask Gemini anything...")

if user_prompt:

    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt
    })

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Gemini is thinking..."):

            response = None

            for attempt in range(3):
                try:
                    response = st.session_state.chat_v2.send_message(
                        message=user_prompt
                    )
                    break

                except errors.APIError as e:
                    if e.code in (503, 504, 429, 500, 502) and attempt < 2:
                        wait_time = 2 ** (attempt + 1)
                        st.warning(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        st.error(f"Gemini API Error: {e}")
                        break

                except Exception as e:
                    if "client has been closed" in str(e).lower() and attempt == 0:
                        try:
                            initialize_gemini()
                        except Exception as init_error:
                            st.error(f"Client initialization failed: {init_error}")
                            break
                    else:
                        st.error(f"Unexpected Error: {e}")
                        break

            if response is not None:
                answer = response.text

                if answer:
                    st.markdown(answer)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })
                else:
                    st.error("Gemini returned an empty response.")
