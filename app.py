import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from openai import OpenAI

# Deploy Streamlit app configuration: https://share.streamlit.io/

st.set_page_config(page_title="Chat with OpenAI", page_icon=":robot:")
st.title("HR Interview Chatbot :robot:")

# Session state for setup completion
if 'setup_complete' not in st.session_state:
    st.session_state.setup_complete = False
# Session state for user message count
if 'user_message_count' not in st.session_state:
    st.session_state.user_message_count = 0
# Session state for feedback shown
if 'feedback_shown' not in st.session_state:
    st.session_state.feedback_shown = False
# Session state for chat history messages
if 'messages' not in st.session_state:
    st.session_state.messages = []
# Session state for chat completion
if 'chat_complete' not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True
def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:
    # Setup personal information section
    st.subheader('Personal Information', divider='rainbow')

    # Initialize session state variables for personal information and company/position
    if 'name' not in st.session_state:
        st.session_state['name'] = ''
    if 'experience' not in st.session_state:
        st.session_state['experience'] = ''
    if 'skills' not in st.session_state:
        st.session_state['skills'] = ''
    if 'level' not in st.session_state:
        st.session_state['level'] = 'Junior'
    if 'position' not in st.session_state:
        st.session_state['position'] = 'Data Scientist'
    if 'company' not in st.session_state:
        st.session_state['company'] = 'Amazon'

    st.session_state['name'] = st.text_input(label='Name', max_chars=40, placeholder='Enter your name')
    st.session_state['experience'] = st.text_area(label='Experience', value='', height=None, max_chars=200, placeholder='Describe your experience')
    st.session_state['skills'] = st.text_area(label='Skills', value='', height=None, max_chars=200, placeholder='List your skills')

    # Setup company and position section
    st.subheader('Company and Position', divider='rainbow')
    col1, col2 = st.columns(2)
    with col1:
        st.session_state['level'] = st.radio('Choose level', key='visibility', options=['Junior', 'Mid-level', 'Senior'])
    with col2:
        st.session_state['position'] = st.selectbox('Choose a position', ('Data Scientist', 'ML Engineer', 'BI Analyst', 'Financial Analyst'))
    st.session_state['company'] = st.selectbox('Choose a company', ('Amazon', 'Meta', 'Udemy', '365 Company', 'Nestle', 'LinkedIn', 'Spotify'))

    if st.button('Start Interview', on_click=complete_setup):
        st.write('Setup complete! Starting interview...')
    
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete: # Main chat interface
    # Load API key from .env file
    dotenv_file = ".env"
    file_path = next((os.path.join(root, dotenv_file) for root, dirs, files in os.walk("/") if dotenv_file in files), None)
    dotenv.load_dotenv(file_path)

    st.info(
        '''
Start by introducing yourself.
''', icon="💡")

    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"]) # for remote hosting on share.streamlit.io

    # Session state for OpenAI model selection
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = 'gpt-4o'

    # Session state for chat history messages
    if not st.session_state.messages:
        st.session_state.messages = [{'role': 'system', 'content': f'''You are an HR executive that interviews an interviewee called {st.session_state['name']} 
                                    with experience {st.session_state['experience']} and skills {st.session_state['skills']}. 
                                    You should interview them for the position {st.session_state['level']} {st.session_state['position']} at the company {st.session_state['company']}.'''}]

    for message in st.session_state.messages: # display existing chat messages from session state
        if message["role"] != 'system': # skip system messages
            with st.chat_message(message["role"]): # create chat message container based on role
                st.markdown(message["content"]) # render markdown for message content

    if st.session_state.user_message_count < 5: # limit user to 5 messages
        # create chat model selection box
        if prompt := st.chat_input("Your answer.", max_chars=1000): # get user input from chat input box
            st.session_state.messages.append({"role": "user", "content": prompt}) # add user message to session state messages history

            with st.chat_message("user"): # display user message in chat message container
                st.markdown(prompt) # render markdown for user message

            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"): # create assistant chat message container
                    stream = client.chat.completions.create( # call OpenAI API to get chat completion
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": msg["role"], "content": msg["content"]}
                            for msg in st.session_state.messages # pull message history from session state
                        ],
                        stream=True, # enable streaming as response is generated
                    )
                    response = st.write_stream(stream) # display streaming response and collect content
                st.session_state.messages.append({"role": "assistant", "content": response}) # add assistant response to session state messages history
            
            st.session_state.user_message_count += 1 # increment user message count
    
    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

# Feedback section
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button('Get Feedback', on_click=show_feedback):
        st.write('Fetching feedback...')
# Display feedback section
if st.session_state.feedback_shown:
    st.subheader('Feedback')

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    feedback_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    feedback_completion = feedback_client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {"role": "system", "content": '''You are a helpful tool that provides feedback on the interviewee's performance
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overal Score: //Your score
             Feedback: //Here you put your feedback
             give only the feedback, do not ask any additional queries.'''},
            {"role": "user", "content": f"""This is the interview history.
            Keep in mind you are only a tool and should not engaging conversation: 
            {conversation_history}
            """
            }
        ]
    )
    st.write(feedback_completion.choices[0].message.content) # display feedback response

    # Restart interview button
    if st.button('Restart Interview', type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
