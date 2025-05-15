import streamlit as st
import openai

# Load OpenAI API key securely from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

def ask_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message["content"]

st.title("Campaign Link Generator Chatbot")

st.write("Ask me to generate campaign links or explain elements.")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.text_input("Your question or request:")

if user_input:
    # Add user input to history
    st.session_state.history.append({"role": "user", "content": user_input})
    
    # Prepare context: explain your domain-specific terms for GPT
    context = """
You are a marketing chatbot helping users generate campaign links. 
Explain or generate links based on these inputs:
Brand (e.g. PS = Pokerstars), Region (UK), Platform (DIS = iOS/Android/Web), 
Campaign, Budget Code, Agency, DSP, Publisher, Targeting, Vertical, AMS code, etc.
Links like:
Click tag = https://www.pokerstars.uk/poker/pages/stars-season/?source=19975077&utm_medium=display&utm_source=youtube&utm_campaign=starsseason&review=true
AF link = https://amaya.onelink.me/197923601?c=PS-UK-DIS-STARSSEASON-TPP-TSG-Direct-REDDIT-ROS-ALL-POKER-GENERIC-NO-19975101-VOD-P-X&af_sub4=19975101...

Use the information above to answer user queries.
"""

    full_prompt = context + "\nUser: " + user_input

    # Call GPT
    bot_response = ask_gpt(full_prompt)

    # Add bot response to history
    st.session_state.history.append({"role": "assistant", "content": bot_response})

# Display chat history
for chat in st.session_state.history:
    if chat["role"] == "user":
        st.markdown(f"**You:** {chat['content']}")
    else:
        st.markdown(f"**Bot:** {chat['content']}")
