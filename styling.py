import streamlit as st
import base64

bg_image = 'background.jpg'

def set_blurred_background(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()

    css = f"""
        <style>
        .stApp {{
            background: none;
        }}

        body::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            filter: blur(8px);
            z-index: -2;
        }}

        body::after {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0, 0, 0, 0.4);  /* Dark overlay */
            z-index: -1;
        }}

        section.main > div {{
            position: relative;
            z-index: 1;
        }}

        h1, h2, h3, h4, h5, h6, p, label, div {{
            color: white !important;
            font-weight: bold !important;
        }}
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

css_2 = """
    <style>
/* Force all button text to black */
button[kind="primary"] > div[data-testid="stMarkdownContainer"] > p,
button[kind="secondary"] > div[data-testid="stMarkdownContainer"] > p {
    color: black !important;
    font-weight: bold;
}

/* Optional: darken button background slightly for contrast */
button[kind="primary"],
button[kind="secondary"] {
    background-color: #ffffffcc !important;  /* Slight transparency */
    border: 1px solid #ccc !important;
}
</style>

    """