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

# ------------------------------------------
#            VISUAL CUSTOMIZATIONS
# ------------------------------------------
# Set the page config (title, wide layout)
st.set_page_config(
    page_title="Filmbright SRT Translator",
    layout="wide"
)

# Inject custom CSS to style the app
st.markdown(
    """
    <style>
    /* Make the main background white */
    .main {
        background-color: #FFFFFF;
        padding: 2rem;
    }

    /* Style the top header and subheader texts */
    h1, h2, h3, h4 {
        color: #2F2F2F;
        font-family: "Arial", sans-serif;
    }

    /* Customize the file uploader text and border */
    .css-19u4pbh, .css-16huue1 {
        border: 2px solid #8DC83D !important;
        padding: 10px;
        border-radius: 10px;
        color: #2F2F2F;
    }

    /* Customize the button */
    .stButton button {
        background-color: #8DC83D !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem 1rem;
        border: none;
    }

    /* Style the selectbox */
    .stSelectbox > div:first-child {
        color: #2F2F2F;
        font-weight: 600;
    }
    .stSelectbox div[data-baseweb="select"] .css-1wa3eu0, 
    .stSelectbox div[data-baseweb="select"] .css-1hb7zxy  {
        border: 2px solid #8DC83D !important;
        border-radius: 8px !important;
    }

    /* Style success and warning messages */
    .stAlert {
        border-left: 5px solid #8DC83D;
        border-radius: 0.5rem;
    }

    /* Make the entire app a bit more centered and neat */
    .block-container {
        max-width: 800px;
        margin: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------
#            FLASK + MAKE WEBHOOK
# ------------------------------------------
MAKE_WEBHOOK_URL = "https://hook.eu2.make.com/usgwgvrh2d6fn5n5dh8ggvabgeb6rl7l"

flask_app = Flask(__name__)

# ------------------------------------------
#      GOOGLE DRIVE AUTH & FUNCTIONS
# ------------------------------------------
def authenticate_google_drive():
    creds = Credentials.from_service_account_file("credentials_srt_files_translation.json")
    drive_service = build("drive", "v3", credentials=creds)
    return drive_service


def download_srt_file(service, file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(file_name, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    return file_name


def upload_file_to_drive(service, file_name, folder_id):
    file_metadata = {"name": file_name, "parents": [folder_id]}
    media = MediaFileUpload(file_name, mimetype="text/plain")
    uploaded_file = service.files().create(body=file_metadata, media_body=media).execute()
    return uploaded_file.get("id")


def parse_srt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.readlines()


# ------------------------------------------
#         OPENAI TRANSLATION
# ------------------------------------------
def translate_text(text, target_language):
    client = OpenAI(api_key=os.getenv("OPEN_AI_KEY_SRT_FILMBRIGHT"))

    prompt = f"""
    You are a professional subtitle translator. Your task is to translate the content of an SRT file into {target_language}. 
    Ensure the following:

    1. Maintain natural flow and readability typical of subtitles in movies or videos.
    2. Keep each translated subtitle's duration and text length approximately similar to the original for synchronization.
    3. Preserve context and cultural nuances while adapting to the linguistic style of the target language.
    4. Ensure consistent formatting, avoiding any changes to the timecodes or the SRT file structure.
    5. Output the result in SRT format only (numbers, timecodes, and text).

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
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional translation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        response_content = response.choices[0].message.content

        # Remove all content before the first '1' in the SRT
        if '1' in response_content:
            response_content = response_content[response_content.index('1'):]

        return response_content.strip()

    except openai.OpenAIError as e:
        print(f"OpenAI API Error: {e}")
        return f"Error: {e}"
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return f"Error: {e}"


def translate_srt(file_path, target_language):
    lines = parse_srt(file_path)
    full_srt_text = "".join(lines)
    translated_srt = translate_text(full_srt_text, target_language)
    return translated_srt


# ------------------------------------------
#         FLASK WEBHOOK ENDPOINT
# ------------------------------------------
@flask_app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    file_id = data.get("file_id")
    file_name = data.get("file_name")
    target_language = data.get("target_language")

    if not all([file_id, file_name, target_language]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    try:
        drive_service = authenticate_google_drive()
        local_file = download_srt_file(drive_service, file_id, file_name)

        translated_content = translate_srt(local_file, target_language)
        translated_file_name = f"translated_{target_language}.srt"
        with open(translated_file_name, "w", encoding="utf-8") as f:
            f.write(translated_content)

        translated_file_id = upload_file_to_drive(drive_service, translated_file_name, "Translated_Files_Folder_ID")
        return jsonify({"status": "success", "translated_file_id": translated_file_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def run_flask():
    flask_app.run(port=5000)


# ------------------------------------------
#          STREAMLIT INTERFACE
# ------------------------------------------

st.title("Filmbright SRT Translator")
st.write("#### Seamlessly translate SRT files into different languages for your video productions.")
st.write("#### NOTE: If the file is large, it may take some time to complete the translation. Please supply your email so we can let you know once completed.")

# Start the Flask server in a separate thread (only once)
if "flask_thread" not in st.session_state:
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    st.session_state["flask_thread"] = flask_thread

# Collect user email
user_email = st.text_input(
    "Enter your email address",
    placeholder="example@example.com"
)

# Manual File Upload
uploaded_file = st.file_uploader(
    "Upload your SRT File here",
    type=["srt"]
)

target_language = st.selectbox(
    "Select Target Language",
    [
        "French",
        "Spanish (Spain)",
        "Spanish (Latin America)",
        "German",
        "Italian",
        "Portuguese (Brazil)"
    ]
)

if uploaded_file and user_email:
    if st.button("Translate"):
        st.info("Translating... Please wait.")

        # Save the uploaded file locally
        input_file_name = uploaded_file.name
        with open(input_file_name, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File '{input_file_name}' uploaded successfully!")

        base_name, extension = os.path.splitext(input_file_name)
        translated_file_name = f"{target_language}_{base_name}{extension}"

        # Translate the SRT file
        translated_content = translate_srt(input_file_name, target_language)
        with open(translated_file_name, "w", encoding="utf-8") as f:
            f.write(translated_content)

        # Send the translated file and user email to Make webhook
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
                st.success("File Translated Successfully!")
                # Parse JSON response from Make to retrieve the Google Drive link
                try:
                    make_response_data = response.json()  # Parse the JSON response
                    drive_link = make_response_data.get("drive_link")  # Get the Drive link

                    if drive_link:
                        # Modify the link to remove everything preceding the first 'h'
                        drive_link = drive_link[drive_link.index('h'):] if 'h' in drive_link else drive_link

                        # Display a clickable download link in the app
                        st.markdown(f"[Download the translated file from Google Drive]({drive_link}) Here")
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