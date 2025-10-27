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
    3. Use only supplies the user has available. Do not use supplies if its excessive for the severity of the wound.
    4. Do not use em dashes (—), en dashes (–), or hyphens (-) for separating phrases; instead use commas or semicolons.
    5. Carefully consider the expertise-level when choosing the language for the instructions
    6. Keep your output as a **numbered list** (1., 2., 3., etc.) with concise, actionable wound-care steps.
    7. Places spaces between each step for readability.

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

# Initialize session state for terms acceptance if not exists
if 'terms_accepted' not in st.session_state:
    st.session_state.terms_accepted = False

# Initialize session state for page navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = "input"  # "input" or "results"
if 'assessment_data' not in st.session_state:
    st.session_state.assessment_data = None

def show_terms():
    st.markdown("""
    # Terms and Conditions of Use
    ### Effective Date: October 24, 2025
    
    
    This AI wound-care tool is for research and educational purposes only. 
    It must not be used for medical diagnosis, treatment, or patient care — including at home.
    """)
    
    with st.expander("Click to Read Full Terms", expanded=True):
        st.markdown("""
        ### 1. Acceptance of Terms
        By accessing or using this wound care AI tool ("the Tool"), you agree to be bound by these Terms and Conditions of Use ("Terms"). If you do not agree to these Terms, you may not access or use the Tool.
        
        ### 2. Purpose of the Tool
        This Tool is provided exclusively for research, educational, and informational purposes. It is a demonstration of artificial-intelligence models applied to wound-care scenarios. The Tool is not intended or approved for use in any medical, clinical, or home-care setting.
        
        ### 3. No Medical Advice
        The Tool does not provide medical advice and must not be used to diagnose, treat, or manage any health condition. Do not rely on any output of the Tool to make healthcare or personal medical decisions. Use of the Tool for any clinical or home-care purpose is strictly prohibited.
        
        ### 4. User Obligations
        - Use it only for research, education, or personal curiosity, not for patient care.
        - Do not upload identifiable patient or personal health information.
        - Do not redistribute outputs as medical guidance.
        - Comply with all laws and ethical research standards.
        
        ### 5. No Warranty
        The Tool is provided "as is" and "as available" without any warranty or guarantee of accuracy, reliability, or fitness for purpose. Outputs may be incomplete or inconsistent.
        """)
    
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("I Accept These Terms", use_container_width=True, type="primary"):
            st.session_state.terms_accepted = True
            # Backward compatibility: Streamlit < 1.27 uses experimental_rerun
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()
    with col2:
        if st.button("Decline", use_container_width=True, type="secondary"):
            st.error("You must accept the terms to use this application.")
            st.stop()
    
    st.markdown("---")

# Show terms if not accepted
if not st.session_state.terms_accepted:
    show_terms()
    st.stop()
else:
    # Scroll to top when terms are accepted
    st.components.v1.html("""
        <script>
            window.parent.document.querySelector('section.main').scrollTo(0, 0);
        </script>
    """, height=0)

# Show terms if not accepted
if not st.session_state.terms_accepted:
    show_terms()
    st.stop()

# PAGE ROUTING: Show input page or results page
if st.session_state.current_page == "input":
    # ==================== INPUT PAGE ====================
    st.title("Wound Care Assessment Tool")

    st.markdown("---")
    # Add user-friendly instructions
    st.markdown("""
    ### Instructions:

    1. Fill out all the questions
    2. Upload a clear, well-lit photo of the wound
    3. Click "Generate Assessment" to get a personalized wound care plan

    """)
    st.markdown("---")

    # Create single column for input
    st.markdown("## Input Parameters")
    st.markdown("---")
    
    # Supply options with checkboxes
    st.markdown("### 1. Available Supplies")
    st.markdown("*Select all that apply:*")
    supply_options = [
        "BandAid",
        "Bandage",
        "Fabric or elastic bandages",
        "Sterile gauze pads",
        "Sterile gauze rolls",
        "Non-stick wound pads",
        "Adhesive wound dressings",
        "Transparent film dressings",
        "Medical adhesive tape",
        "Sterile saline solution",
        "Antiseptic wipes",
        "Antibacterial or antibiotic ointment",
        "Barrier cream or ointment",
        "Disposable gloves",
        "Other"
    ]
    supplies = []
    for option in supply_options:
        checked = st.checkbox(option, key=f"supply_{option}")
        if checked:
            if option == "Other":
                other_supplies = st.text_input("Please specify other supplies:", key="other_supplies_input")
                if other_supplies:
                    supplies.append(f"Other: {other_supplies}")
            else:
                supplies.append(option)
    st.markdown("---")

    # Other input fields
    st.markdown("### 2. Care Setting")
    setting = st.selectbox(
        "*Where is the care being provided?*",
        ["Harm reduction clinic", "Outpatient clinic", "Home", "Other"]
    )
    # If the user selects Other, show a text box to capture the custom setting
    if setting == "Other":
        other_setting = st.text_input("Please specify care setting:", key="other_setting_input")
        if other_setting:
            setting = f"Other: {other_setting}"
    st.markdown("---")

    st.markdown("### 3. Provider Expertise")
    st.markdown("""
        <style>
        div[data-testid="stSelectbox"] label p {
            white-space: normal !important;
            word-wrap: break-word !important;
        }
        </style>
    """, unsafe_allow_html=True)
    expertise = st.selectbox(
        "*What is your level of experience with wounds?*",
        [
            "Healthcare professional with wound care experience",
            "Healthcare professional without wound care experience",
            "Non-healthcare professional"
        ]
    )
    st.markdown("---")

    st.markdown("### 4. Hospital Access")
    willingness = st.radio(
        "*Is the individual willing to go to hospital if needed?*",
        ["Yes", "No"]
    )
    st.markdown("---")

    st.markdown("### 5. Clinic Visits")
    frequency = st.selectbox(
        "*How often can the individual visit the clinic?*",
        ["Daily", "Weekly", "Other"]
    )
    if frequency == "Other":
        other_frequency = st.text_input("Please specify visit frequency:", key="other_frequency_input")
        if other_frequency:
            frequency = f"Other: {other_frequency}"
    st.markdown("---")

    st.markdown("### 6. Infection Status")
    infected = st.radio(
        "*Does the wound show signs of infection?*",
        ["Yes", "No", "Not sure"]
    )
    st.markdown("---")

    st.markdown("### 7. Moisture Level")
    moisture = st.radio(
        "*What is the wound's moisture condition?*",
        ["Dry", "Wet", "Normal"]
    )
    st.markdown("---")

    # File uploader for image
    uploaded_file = st.file_uploader("Choose a wound image...", type=["jpg", "jpeg", "png"])

    # Submit button
    if st.button("Generate Assessment", type="primary", use_container_width=True):
        if uploaded_file is None:
            st.error("Please upload an image first.")
        elif not supplies:
            st.error("Please select at least one available supply.")
        else:
            # Store data and switch to results page
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
                st.session_state.assessment_data = {
                    'assessment': assessment,
                    'image': uploaded_file,
                    'supplies': supplies,
                    'setting': setting,
                    'expertise': expertise,
                    'willingness': willingness,
                    'frequency': frequency,
                    'infected': infected,
                    'moisture': moisture
                }
                st.session_state.current_page = "results"
                # Reset follow-up state for new assessment
                st.session_state.conversation_history = []
                st.session_state.continue_conversation = True
                # Use compatible rerun
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()

elif st.session_state.current_page == "results":
    # ==================== RESULTS PAGE ====================
    st.title("Wound Care Assessment Results")
    
    # Back button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back to Input", type="secondary"):
            st.session_state.current_page = "input"
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()
    
    st.markdown("---")
    
    # Force scroll to the title anchor using the auto-generated anchor link
    st.markdown("""
        <script>
            setTimeout(function() {
                var titleElement = window.parent.document.querySelector('h1');
                if (titleElement) {
                    titleElement.scrollIntoView({behavior: 'instant', block: 'start'});
                }
            }, 100);
        </script>
    """, unsafe_allow_html=True)
    
    # Display uploaded image
    if st.session_state.assessment_data:
        uploaded_file = st.session_state.assessment_data['image']
        assessment = st.session_state.assessment_data['assessment']
        
        # Display image in a version-compatible way
        try:
            st.image(uploaded_file, caption="Uploaded Image", width='stretch')
        except TypeError:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        
        st.markdown("---")
        st.markdown("## Assessment")
        st.markdown(assessment)

        # Follow-up question UI - Multi-turn conversation
        st.markdown("---")
        st.markdown("### Follow-up")
        
        # Initialize session state for conversation history
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        if 'continue_conversation' not in st.session_state:
            st.session_state.continue_conversation = True
        
        # Display conversation history
        if st.session_state.conversation_history:
            st.markdown("#### Conversation:")
            for i, exchange in enumerate(st.session_state.conversation_history):
                st.markdown(f"**Q{i+1}:** {exchange['question']}")
                st.markdown(f"**A{i+1}:** {exchange['answer']}")
                st.markdown("---")
        
        # Show follow-up UI if conversation is active
        if st.session_state.continue_conversation:
            st.write("Do you have any questions or clarifications?")
            
            followup_choice = st.radio(
                "Would you like to ask a question?",
                ["Yes", "No"],
                key=f"followup_choice_{len(st.session_state.conversation_history)}"
            )
            
            if followup_choice == "No":
                if st.button("Finish", key="finish_conversation"):
                    st.session_state.continue_conversation = False
                    st.success("Thank you for using the wound assistant.")
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
            else:
                followup_question = st.text_area(
                    "Please enter your question or clarification:",
                    key=f"followup_question_{len(st.session_state.conversation_history)}"
                )
                
                if st.button("Ask", key=f"ask_followup_{len(st.session_state.conversation_history)}"):
                    if not followup_question or not followup_question.strip():
                        st.warning("Please enter a question before asking.")
                    else:
                        with st.spinner("Getting assistant response..."):
                            try:
                                # Build context from conversation history
                                context = f"Original assessment:\n\n{assessment}\n\n"
                                if st.session_state.conversation_history:
                                    context += "Previous conversation:\n"
                                    for i, exchange in enumerate(st.session_state.conversation_history):
                                        context += f"Q{i+1}: {exchange['question']}\n"
                                        context += f"A{i+1}: {exchange['answer']}\n\n"
                                
                                follow_messages = [
                                    {
                                        "role": "user",
                                        "content": (
                                            f"{context}"
                                            f"Current question: {followup_question}\n\n"
                                            "Please answer the question clearly, referencing the assessment and previous conversation where helpful. "
                                            "Be concise and actionable. Make answer only paragraph long maximum."
                                        ),
                                    }
                                ]
                                
                                follow_resp = client.chat.completions.create(
                                    model="gpt-4.1",
                                    messages=follow_messages,
                                    max_tokens=500,
                                )
                                
                                response_text = follow_resp.choices[0].message.content
                                
                                # Add to conversation history
                                st.session_state.conversation_history.append({
                                    'question': followup_question,
                                    'answer': response_text
                                })
                                
                                # Rerun to show updated conversation
                                if hasattr(st, "rerun"):
                                    st.rerun()
                                else:
                                    st.experimental_rerun()
                                    
                            except Exception as e:
                                st.error(f"⚠️ Error calling OpenAI API: {e}")
        else:
            st.success("Thank you for using the wound assistant.")