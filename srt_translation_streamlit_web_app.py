import os
import streamlit as st
from flask import Flask, request, jsonify
from threading import Thread
import openai
from openai import OpenAI
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2.service_account import Credentials
import io
import requests
from PIL import Image  # Import this to handle the image file

# Set up the Streamlit page
st.set_page_config(
    page_title="Filmbright SRT Translator",
    layout="centered"
)

# Display the Filmbright logo at the top
logo_path = "/Users/david/Documents/Filmbright/SRT_Files_Translation/Project_Files/filmbright_logo.png"
logo_image = Image.open(logo_path)

# Use Streamlit columns to center the logo
col1, col2, col3 = st.columns([1.4, 1.6, 1])  # Adjust column widths to center the logo
with col2:
    st.image(logo_image, width=180)

# ----------------------
#  STREAMLIT PAGE SETUP
# ----------------------
# Set up the Streamlit page with Filmbright branding.

# Inject custom CSS to style the app (Filmbright green #8DC83D and white).
st.markdown(
    """
    <style>
    /* Use a clean, modern font */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Montserrat', sans-serif;
        background-color: #FFFFFF; /* White background */
    }

    /* Logo styling */
    .filmbright-logo {
        display: block;
        margin: 0 auto 1rem auto;
        text-align: center;
    }

    /* Title styling */
    .main-title {
        color: #8DC83D;
        font-size: 2.2rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 0.2rem;
    }

    /* Subtitle styling */
    .subtitle {
        color: #333333;
        font-size: 1rem;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Streamlit Button styling */
    .stButton button {
        background-color: #8DC83D;
        color: #FFFFFF;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 5px;
        cursor: pointer;
        font-weight: 600;
        transition: background-color 0.3s ease;
    }
    .stButton button:hover {
        background-color: #7BB02E;
    }

    /* Streamlit warnings, errors, successes */
    .stAlert {
        border-radius: 5px;
    }
    .stWarning, .stError, .stSuccess {
        padding: 1rem;
    }
    /* Table or widget text color */
    .css-1kyxreq {
        color: #333333;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Main title and subtitle
st.markdown('<h1 class="main-title">Filmbright - SRT File Translator</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Easily translate SRT files into a different language and download them conveniently.</p>', unsafe_allow_html=True)

# ----------------------
#       FLASK APP
# ----------------------
MAKE_WEBHOOK_URL = "https://hook.eu2.make.com/usgwgvrh2d6fn5n5dh8ggvabgeb6rl7l"
flask_app = Flask(__name__)

# Google Drive authentication
def authenticate_google_drive():
    creds = Credentials.from_service_account_file("credentials_srt_files_translation.json")
    drive_service = build("drive", "v3", credentials=creds)
    return drive_service

# Download SRT file from Google Drive
def download_srt_file(service, file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(file_name, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    return file_name

# Upload file to Google Drive
def upload_file_to_drive(service, file_name, folder_id):
    file_metadata = {"name": file_name, "parents": [folder_id]}
    media = MediaFileUpload(file_name, mimetype="text/plain")
    uploaded_file = service.files().create(body=file_metadata, media_body=media).execute()
    return uploaded_file.get("id")

# Parse SRT file
def parse_srt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.readlines()

# Translate subtitles using OpenAI (Updated for API >=1.0.0)
def translate_text(text, target_language):

    client = OpenAI(api_key=os.getenv("OPEN_AI_KEY_SRT_FILMBRIGHT"))

    # Define the translation prompt
    prompt = f"""
    You are a professional subtitle translator. Your task is to translate the content of an SRT file into {target_language}. 
    Ensure the following:

    1. Maintain natural flow and readability typical of subtitles in movies or videos.
    2. Keep each translated subtitle's duration and text length approximately similar to the original for synchronization purposes.
    3. Preserve context and cultural nuances while adapting to the linguistic style of the target language.
    4. Ensure consistent formatting, avoiding any changes to the timecodes or the SRT file structure.

    Generate the translated output in the same format, replacing the original text 
    with the translated text. Only output the text and nummbers and timecodes, no additional comments from you or anything.

    Example Input:
    1
    00:00:01,000 --> 00:00:03,000
    Hello, how are you?

    2
    00:00:04,000 --> 00:00:06,000
    I'm doing great, thank you.

    Example Output:
    1
    00:00:01,000 --> 00:00:03,000
    Hola, ¿cómo estás?

    2
    00:00:04,000 --> 00:00:06,000
    Estoy muy bien, gracias.

    Input:
    {text}

    Note: If a word-for-word translation would seem unnatural in {target_language}, adapt the translation to align with 
    commonly used expressions in that language. Try to make use of the overall context in the original language to 
    improve your response. Your output must always be in the format specified by the example output section, 
    and only include the translations and the timecode with the matching numbers and values
    """

    try:
        # Call OpenAI's ChatCompletion API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional translation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7  # Adjust temperature for creative translations
        )

        response_content = response.choices[0].message.content

        # Remove all content before the first '1'
        if '1' in response_content:
            response_content = response_content[response_content.index('1'):]

        return response_content.strip()

    except openai.OpenAIError as e:
        print(f"OpenAI API Error: {e}")
        return f"Error: {e}"
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return f"Error: {e}"

# Translate SRT file
def translate_srt(file_path, target_language):
    # Parse the entire SRT file
    lines = parse_srt(file_path)
    full_srt_text = "".join(lines)

    # Translate the SRT file
    translated_srt = translate_text(full_srt_text, target_language)
    return translated_srt

# Flask webhook endpoint
@flask_app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    file_id = data.get("file_id")
    file_name = data.get("file_name")
    target_language = data.get("target_language")

    if not all([file_id, file_name, target_language]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    try:
        # Authenticate Google Drive and download the file
        drive_service = authenticate_google_drive()
        local_file = download_srt_file(drive_service, file_id, file_name)

        # Translate the SRT file
        translated_content = translate_srt(local_file, target_language)
        translated_file_name = f"translated_{target_language}.srt"
        with open(translated_file_name, "w", encoding="utf-8") as f:
            f.write(translated_content)

        # Upload the translated file to Google Drive
        translated_file_id = upload_file_to_drive(drive_service, translated_file_name, "Translated_Files_Folder_ID")

        return jsonify({"status": "success", "translated_file_id": translated_file_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Run Flask in a separate thread
def run_flask():
    flask_app.run(port=5000)

# ----------------------
#  STREAMLIT INTERFACE
# ----------------------
# Start Flask server in a separate thread (only once per session)
if "flask_thread" not in st.session_state:
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    st.session_state["flask_thread"] = flask_thread

# Collect user email
user_email = st.text_input("Enter your email address", placeholder="example@example.com")

# Manual File Upload
uploaded_file = st.file_uploader("Upload SRT File", type=["srt"])
target_language = st.selectbox(
    "Select Target Language",
    ["French", "Spanish (Spain)", "Spanish (Latin America)", "German", "Italian", "Portuguese (Brazil)"]
)

# Translation Process
if uploaded_file and user_email:
    if st.button("Translate"):
        st.write("Translating... Please wait.")

        # Save the uploaded file locally
        input_file_name = uploaded_file.name
        with open(input_file_name, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.write(f"File '{input_file_name}' uploaded successfully!")

        # Prepare translated filename
        base_name, extension = os.path.splitext(input_file_name)
        translated_file_name = f"{target_language}_{base_name}{extension}"

        # Perform translation
        translated_content = translate_srt(input_file_name, target_language)
        with open(translated_file_name, "w", encoding="utf-8") as f:
            f.write(translated_content)

        # Send data to Make webhook
        with open(translated_file_name, "rb") as f:
            response = requests.post(
                MAKE_WEBHOOK_URL,
                files={"file": (translated_file_name, f, "text/plain")},
                data={
                    "file_name": translated_file_name,
                    "target_language": target_language,
                    "user_email": user_email
                }
            )

            if response.status_code == 200:
                st.success(f"File Translated into {target_language} successfully!")
                # Parse JSON response from Make to retrieve the Google Drive link
                try:
                    make_response_data = response.json()
                    drive_link = make_response_data.get("drive_link")
                    if drive_link:
                        # Remove everything preceding the first 'h'
                        cleaned_drive_link = drive_link[drive_link.index('h'):]
                        # Display a clickable download link in the app
                        st.markdown(f"[Download the translated file from Google Drive]({cleaned_drive_link})")
                    else:
                        st.warning("The Make webhook did not return a Google Drive link.")
                except Exception as e:
                    st.error(f"Could not parse the response from Make. Error: {str(e)}")
            else:
                st.error(f"Failed to send file to Make. Response: {response.text}")
elif not user_email:
    st.warning("Please enter your email address.")
elif not uploaded_file:
    st.warning("Please upload an SRT file.")