import base64
import io
import json
import os
from typing import List

import requests
import streamlit as st

# ----------------------------------------------------------------------
# Helper functions for interacting with OpenAI API
# ----------------------------------------------------------------------

def call_openai(url: str, payload: dict, api_key: str, stream: bool = False) -> requests.Response:
    """Send a POST request to the OpenAI API with basic error handling."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(url, headers=headers, json=payload, stream=stream, timeout=60)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(str(exc)) from exc


def generate_image(api_key: str) -> None:
    """UI and logic for DALL-E image generation."""
    st.header("Image Generation (DALL-E 3)")
    prompt = st.text_input("Image prompt")
    if st.button("Generate Image"):
        if not prompt:
            st.warning("Please enter a prompt.")
            return
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
        }
        try:
            with st.spinner("Generating image..."):
                response = call_openai(
                    "https://api.openai.com/v1/images/generations", payload, api_key
                )
                data = response.json()
                image_url = data["data"][0]["url"]
                img_bytes = requests.get(image_url).content
            st.image(img_bytes)
            st.download_button("Download Image", img_bytes, file_name="generated.png")
        except Exception as e:  # noqa: BLE001
            st.error(f"OpenAI API Error: {e}")


def text_tools(api_key: str) -> None:
    """UI and logic for text summarization and rewriting."""
    st.header("Text Tools (GPT-3.5 Turbo)")
    user_text = st.text_area("Enter text")
    col1, col2 = st.columns(2)
    action = None
    with col1:
        if st.button("Summarize"):
            action = "summarize"
    with col2:
        if st.button("Rewrite"):
            action = "rewrite"

    if action and user_text.strip():
        if action == "summarize":
            system_prompt = "Summarize the following text."
        else:
            system_prompt = "Rewrite the following text to improve clarity."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]
        payload = {"model": "gpt-3.5-turbo", "messages": messages}
        try:
            with st.spinner("Generating..."):
                response = call_openai(
                    "https://api.openai.com/v1/chat/completions", payload, api_key
                )
                out_text = response.json()["choices"][0]["message"]["content"]
            st.text_area("Output", value=out_text, height=200)
        except Exception as e:  # noqa: BLE001
            st.error(f"OpenAI API Error: {e}")


def tts_tool(api_key: str) -> None:
    """UI and logic for text-to-speech generation."""
    st.header("Voice Generation (OpenAI TTS)")
    text = st.text_area("Text to convert to speech")
    voice = st.selectbox(
        "Voice", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    )
    if st.button("Generate Voice"):
        if not text.strip():
            st.warning("Please enter text.")
            return
        payload = {"model": "tts-1", "input": text, "voice": voice}
        try:
            with st.spinner("Generating audio..."):
                response = call_openai(
                    "https://api.openai.com/v1/audio/speech", payload, api_key
                )
                audio_bytes = response.content
            st.audio(audio_bytes)
            st.download_button("Download Audio", audio_bytes, file_name="speech.mp3")
        except Exception as e:  # noqa: BLE001
            st.error(f"OpenAI API Error: {e}")


def chat_tool(api_key: str) -> None:
    """UI and logic for a simple chat interface."""
    st.header("Simple Chat (GPT-3.5 Turbo)")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history: List[dict] = []

    user_input = st.text_area("Your message", key="chat_input")
    if st.button("Send"):
        if user_input.strip():
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                *st.session_state.chat_history,
            ]
            payload = {"model": "gpt-3.5-turbo", "messages": messages}
            try:
                with st.spinner("Generating response..."):
                    response = call_openai(
                        "https://api.openai.com/v1/chat/completions", payload, api_key
                    )
                    reply = response.json()["choices"][0]["message"]["content"]
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": reply}
                )
            except Exception as e:  # noqa: BLE001
                st.error(f"OpenAI API Error: {e}")

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.write(f"**You:** {msg['content']}")
        else:
            st.write(f"**Assistant:** {msg['content']}")


def login() -> bool:
    """Simple session based login."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin":
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")
    return False


def main() -> None:
    """Main entry point for the Streamlit app."""
    st.set_page_config(page_title="AI Service App")

    if not login():
        st.stop()

    # Sidebar configuration for API key and tool selection
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.api_key,
            type="password",
            key="api_key_input",
        )
        st.session_state.api_key = api_key
        # In production, store the API key securely in environment variables
        # e.g., os.environ.get("OPENAI_API_KEY") and do not expose it in the UI.
        tool = st.selectbox(
            "Select Tool",
            ["Image", "Text", "Voice", "Chat"],
        )

    if not st.session_state.api_key:
        st.warning("Please enter your OpenAI API key in the sidebar to continue.")
        st.stop()

    if tool == "Image":
        generate_image(st.session_state.api_key)
    elif tool == "Text":
        text_tools(st.session_state.api_key)
    elif tool == "Voice":
        tts_tool(st.session_state.api_key)
    elif tool == "Chat":
        chat_tool(st.session_state.api_key)


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
