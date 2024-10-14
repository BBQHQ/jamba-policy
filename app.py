import streamlit as st
import os
import json
from ai21 import AI21Client
from ai21.models.chat import ChatMessage

# Set up the main title of the Streamlit app
st.title("Insurance Plan Comparison with Jamba-1.5-Large :health_worker::clipboard:")

# Load data from text files
@st.cache_data
def load_data():
    data_folder = 'data'
    plans = {}
    for filename in [
        "HMO Blue Copayment.txt",
        "HMO Blue New England Basic Saver.txt",
        "HMO Blue Saver.txt",
        "HMO Blue Select $2000 Deductible with Copayment.txt",
        "Preferred Blue PPO $4500 Deductible.txt"
    ]:
        plan_name = os.path.splitext(filename)[0]
        with open(os.path.join(data_folder, filename), 'r') as file:
            plans[plan_name] = file.read()
    return plans

plans_data = load_data()

st.write("""
    Welcome to the Insurance Plan Comparison App! This tool empowers you to compare various healthcare plans 
    offered by Blue Cross Blue Shield. With the help of the Jamba-1.5-Large model, you can pose specific 
    questions to guide your decision-making process. Whether your focus is on out-of-pocket costs, prescription 
    coverage, or options for families, this app facilitates the comparison of up to two plans simultaneously!

    For more information about specific plans, you can access the [coverage policy documents here](https://www.bluecrossma.org/myblue/learn-and-save/plans-and-benefits/coverage-policy-documents).
""")

# Function to get insurance plans
def get_insurance_plans():
    return list(plans_data.keys())

# Function to run a query using Jamba-1.5-Large
def run_jamba_query(question, plan_names):
    client = AI21Client(api_key=st.secrets["AI21_API_KEY"])
    
    # Fetch details for selected plans
    selected_plans = {name: plans_data[name] for name in plan_names if name in plans_data}
    
    # Concatenate plan details with delimiters
    concatenated_details = " ".join([
        f'<plan name="{name}">{details}</plan>'
        for name, details in selected_plans.items()
    ])
    
    # Construct the message for Jamba
    messages = [
        ChatMessage(role='system', content='You are a helpful assistant specializing in comparing Blue Cross Blue Shield insurance plans. Provide concise, accurate comparisons based on the plans given.'),
        ChatMessage(role='user', content=f'{question} {concatenated_details}')
    ]
    
    # Make the API call
    response = client.chat.completions.create(
        messages=messages,
        model="jamba-1.5-large",
        temperature=0.3,
        max_tokens=5000
    )
    
    return json.dumps(response.dict())  # Convert the response to a JSON string

# Get all available plans
all_plans = get_insurance_plans()

# Allow user to select up to 2 plans
selected_plans = st.multiselect("Select up to 2 plans to compare:", all_plans, max_selections=2)

st.write("""
    Below, you can select one of the pre-canned questions or enter your own custom question. 
    The app uses this question to analyze the selected plans and provide a tailored response.
""")

# Pre-canned questions
pre_canned_questions = [
    "Which plan has the lowest deductible?",
    "Compare the out-of-pocket maximums for these plans.",
    "How do the copayments for primary care visits differ between these plans?",
    "What are the differences in prescription drug coverage?",
    "Which plan offers better coverage for specialists?",
    "How do these plans handle emergency room visits?",
    "Compare the coverage for preventive care services.",
    "Custom question"
]

# Dropdown for pre-canned questions
selected_question = st.selectbox("Select a pre-canned question or choose 'Custom question':", pre_canned_questions)

st.markdown("---")
st.header("Health Care Plan Comparison Question")

# Text input for user's question
if selected_question == "Custom question":
    question = st.text_input("Enter your custom question about the selected plans:")
else:
    question = st.text_input("Question about the selected plans:", value=selected_question)

st.write("""
    The model response will appear below, offering detailed comparisons based on your selected question and plans. 
""")

# Button to run the comparison
if st.button('Compare Plans') and len(selected_plans) > 0:
    with st.spinner("Analyzing plans..."):
        # Run Jamba query for selected plans
        jamba_response = run_jamba_query(question, selected_plans)
        
        if jamba_response:
            try:
                # Parse the JSON response
                parsed_response = json.loads(jamba_response)
                
                # Extract the message content from the nested structure
                if 'choices' in parsed_response and len(parsed_response['choices']) > 0:
                    choice = parsed_response['choices'][0]
                    if 'messages' in choice:
                        message = choice['messages']
                    elif 'mesages' in choice:  # Handle potential typo in key name
                        message = choice['mesages']
                    else:
                        message = str(choice)  # Fallback: convert the entire choice to string
                else:
                    message = str(parsed_response)  # Fallback: convert the entire response to string
                
                st.subheader("Model Response:")
                # Escape common Markdown characters and display with st.write
                escaped_message = (
                    message.replace("$", "\\$")
                           .replace("*", "\\*")
                           .replace("_", "\\_")
                           .replace("[", "\\[")
                           .replace("]", "\\]")
                           .replace("(", "\\(")
                           .replace(")", "\\)")
                           .replace("#", "\\#")
                           .replace("+", "\\+")
                           .replace("-", "\\-")
                           .replace(".", "\\.")
                           .replace("!", "\\!")
                )
                
                st.write(escaped_message)
                
                # Add button to view full response JSON
                with st.expander('View Full Response'):
                    st.json(parsed_response)
                
            except json.JSONDecodeError:
                st.error("Failed to parse JSON response. Raw response:")
                st.write(f"<pre>{jamba_response}</pre>")
        else:
            st.error("No response from Jamba-1.5-Large.")
    st.success('Comparison complete!')

st.markdown("---")
st.write("Note: This app uses the Jamba-1.5-Large model to analyze insurance plans. The app makes a single call to Jamba with concatenated plan details for efficient comparison.")