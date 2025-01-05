# frontend/Home.py

import streamlit as st

# Set the page title and other properties
st.set_page_config(
    page_title="Textlogic - Subtitle Generator",  # Title displayed in the browser tab
    page_icon="🎥",  # Optional, a favicon for the page
    layout="centered",  # Layout can be "centered" or "wide"
    initial_sidebar_state="expanded",  # Default state of the sidebar
)

# Inject custom CSS to style the app (Filmbright green #8DC83D and white). NEW
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
st.markdown(
    """
    <style>
    /* Hide Streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    /* Hide Streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

def main():
    st.title("Welcome to SRT Functionalities")
    st.write("Navigate through the sidebar to access different tools.")
    st.image("assets/filmbright_logo.png", width=200)
    st.markdown("""
    ## About This Application

    SRT Functionalities offers a suite of tools to assist you with subtitle translations, transcript generation, and more. Use the sidebar to navigate between different functionalities.

    ### Current Tools:
    - **SRT File Translation:** Translate your subtitle files effortlessly.
    - **Transcript Generator from MP4:** (Coming Soon) Generate transcripts from your video files.
    """)


if __name__ == "__main__":
    main()