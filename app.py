import streamlit as st
import requests
import base64
import json
from io import BytesIO
import os

# ---------------------------
# Utility functions for OpenAI API calls
# ---------------------------

def get_api_key():
    """Retrieve API key from session state."""
    return st.session_state.get("api_key", "")


def generate_image(prompt):
    """Generate an image using DALL-E via OpenAI API."""
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        image_url = data["data"][0]["url"]
        return image_url
    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        return None


def summarize_text(text):
    """Summarize text using GPT-3.5 Turbo."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    messages = [
        {"role": "system", "content": "Summarize the following text."},
        {"role": "user", "content": text},
    ]
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        return ""


def rewrite_text(text):
    """Rewrite text using GPT-3.5 Turbo."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    messages = [
        {"role": "system", "content": "Rewrite the following text in a clearer manner."},
        {"role": "user", "content": text},
    ]
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        return ""


def generate_voice(text):
    """Generate speech from text using OpenAI TTS."""
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "tts-1",
        "input": text,
        "voice": "alloy",
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        return None


def chat_with_gpt(prompt):
    """Simple chat function using GPT-3.5 Turbo."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    messages = [
        {"role": "user", "content": prompt},
    ]
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        return ""

# ---------------------------
# UI Rendering functions
# ---------------------------

def login_page():
    """Render login page."""
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin":
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")


def image_tool():
    """Image generation UI."""
    st.header("Image Generation (DALL-E)")
    prompt = st.text_input("Enter prompt")
    if st.button("Generate Image") and prompt:
        with st.spinner("Generating..."):
            url = generate_image(prompt)
            if url:
                st.image(url)
                try:
                    img_bytes = requests.get(url).content
                    st.download_button(
                        "Download Image", img_bytes, file_name="image.png", mime="image/png"
                    )
                except Exception as e:
                    st.error(f"Error downloading image: {e}")


def text_tool():
    """Text summarization and rewrite UI."""
    st.header("Text Tools")
    text = st.text_area("Enter text", height=200)
    col1, col2 = st.columns(2)
    if col1.button("Summarize") and text:
        with st.spinner("Generating..."):
            summary = summarize_text(text)
            st.text_area("Summary", value=summary, height=200)
    if col2.button("Rewrite") and text:
        with st.spinner("Generating..."):
            rewritten = rewrite_text(text)
            st.text_area("Rewritten Text", value=rewritten, height=200)


def voice_tool():
    """Voice generation UI."""
    st.header("Voice Generation (TTS)")
    text = st.text_area("Enter text for speech", height=200)
    if st.button("Generate Voice") and text:
        with st.spinner("Generating..."):
            audio_bytes = generate_voice(text)
            if audio_bytes:
                st.audio(audio_bytes)


def chat_tool():
    """Simple chat UI."""
    st.header("Chat")
    prompt = st.text_area("Enter prompt", height=150)
    if st.button("Send") and prompt:
        with st.spinner("Generating..."):
            response = chat_with_gpt(prompt)
            st.text_area("Response", value=response, height=200)


def main_app():
    """Main application after login."""
    st.sidebar.header("Settings")
    api_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.get("api_key", ""),
    )
    if api_key:
        st.session_state.api_key = api_key
    # NOTE: For production use, store the API key securely in environment variables
    # (e.g., os.environ) rather than exposing it in the UI or code.

    tool = st.sidebar.selectbox(
        "Select Tool",
        ["Image", "Text", "Voice", "Chat"],
    )

    if tool == "Image":
        image_tool()
    elif tool == "Text":
        text_tool()
    elif tool == "Voice":
        voice_tool()
    elif tool == "Chat":
        chat_tool()


# ---------------------------
# Application start
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
else:
    main_app()
