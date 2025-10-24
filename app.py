import streamlit as st
import base64
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file (local development) or environment (cloud)
load_dotenv()  # will load from .env if present, no error if not found
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("""
    No OpenAI API key found. Please set up your API key:
    - Local development: Add OPENAI_API_KEY to your .env file
    - Streamlit Cloud: Add OPENAI_API_KEY in the app settings under Secrets
    """)
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def process_image(image_file, supplies, setting, expertise, willingness, frequency, infected, moisture):
    # Convert image to base64
    image_bytes = image_file.getvalue()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    # Construct prompt
    prompt = f"""
    You are an educational AI assistant helping to identify visual features in wound images
    for research and model development.

    Your goal is to generate a step-by-step treatment plan **based on both the text context and the visible landmarks in the image.**

    User-provided context:
    - Supplies available: {supplies}
    - Setting: {setting}
    - Expertise-level: {expertise}
    - Willing to visit hospital: {willingness}
    - Frequency of clinic visits: {frequency}
    - Wound infection status: {infected}
    - Wound moisture: {moisture}

    ### Instructions ###
    1. Carefully examine **visual landmarkers** in the wound image — e.g., color changes, necrotic tissue, swelling, drainage, redness, or exposed structures.
    2. Incorporate those landmarks explicitly into the treatment plan (e.g., "Clean around the dark necrotic edge" or "Protect the red granulating area with Xeroform").
    3. Use only supplies the user has available. Do not use supplies if its excessive for the severity of the wound. If warranted include a statement at the end that details what other supplies would be needed for optium care.
    4. Do not use em dashes (—), en dashes (–), or hyphens (-) for separating phrases; instead use commas or semicolons.
    5. Carefully consider the expertise-level when choosing the language for the instructions
    6. Keep your output as a **numbered list** (1., 2., 3., etc.) with concise, actionable wound-care steps.
    7. Include a brief statement at the beginning as to what the wound is (eg. xylazine-induced or abcess, etc.)
    """

    # Prepare API request
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}"
                    }
                }
            ]
        }
    ]

    try:
        # Call GPT-4 Vision API
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error calling OpenAI API: {e}"

# Set up the Streamlit page
st.set_page_config(page_title="Wound Care Assessment", layout="wide")
st.title("Wound Care Assessment Tool")

# Create two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Input Parameters")
    
    # Supply options with checkboxes
    st.markdown("#### Available Supplies")
    supply_options = ["Gauze", "Xeroform", "Tape", "Saline", "Antibiotics", "Bandages", "Gloves", "Other"]
    supplies = []
    for option in supply_options:
        if st.checkbox(option):
            supplies.append(option)

    # Other input fields
    setting = st.selectbox(
        "Setting",
        ["Harm reduction clinic", "Outpatient clinic", "Home", "Other"]
    )

    expertise = st.selectbox(
        "Expertise level with these wounds",
        [
            "Healthcare professional with wound care experience",
            "Healthcare professional without wound care experience",
            "Non-healthcare professional"
        ]
    )

    willingness = st.radio(
        "Willing to go to hospital?",
        ["Yes", "No"]
    )

    frequency = st.selectbox(
        "Clinic visit frequency",
        ["Daily", "Weekly", "Other"]
    )

    infected = st.radio(
        "Wound infected?",
        ["Yes", "No", "Not sure"]
    )

    moisture = st.radio(
        "Wound moisture",
        ["Dry", "Wet"]
    )

    # File uploader for image
    uploaded_file = st.file_uploader("Choose a wound image...", type=["jpg", "jpeg", "png"])

    # Submit button
    if st.button("Generate Assessment"):
        if uploaded_file is None:
            st.error("Please upload an image first.")
        elif not supplies:
            st.error("Please select at least one available supply.")
        else:
            with col2:
                st.subheader("Assessment Results")
                if uploaded_file:
                    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
                    with st.spinner("Analyzing image..."):
                        assessment = process_image(
                            uploaded_file,
                            supplies,
                            setting,
                            expertise,
                            willingness,
                            frequency,
                            infected,
                            moisture
                        )
                        st.markdown(assessment)