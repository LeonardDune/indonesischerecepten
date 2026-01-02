import streamlit as st
from services.chat_agent import generate_response
from utils import write_message

st.set_page_config(page_title="Chat", page_icon="💬")
from components.sidebar import render_sidebar
render_sidebar()

st.title("Recepten Assistant 💬")
st.markdown("Stel een vraag over recepten, ingrediënten of vraag om inspiratie!")

# Set up Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hoi, ik ben een chatbot die je kan helpen met recepten uit Indonesië. Hoe kan ik je helpen?"},
    ]

# Display messages in Session State
for message in st.session_state.messages:
    write_message(message['role'], message['content'], save=False)

# Handle any user input
if prompt := st.chat_input("Wat wil je weten?"):
    # Display user message in chat message container
    write_message('user', prompt)
    
    with st.spinner('Thinking...'):
        try:
            response = generate_response(prompt)
            write_message('assistant', response)
        except Exception as e:
            st.error(f"Er ging iets mis: {e}")
