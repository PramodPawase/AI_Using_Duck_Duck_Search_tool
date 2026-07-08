import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Initialize DuckDuckGo tool
web_tool = DuckDuckGoSearchRun()

def web_search(query: str) -> str:
    return web_tool.invoke(query)

tools = [web_search]

st.title('🌍 The Live Internet Agent')
st.write("Ask me anything about current events. I will browse the web to find the answer.")

with st.sidebar:
    st.header('⚙️ System Config')
    user_api_key = st.text_input('Groq API Key:', type='password')
    user_api_key='3FwzijMKi0H4nJC8bmHq8qvid54_7aC4TJDwJzohNij73b5iV'
    st.info('Equipped with: DuckDuckGo Web Search Tool')

if 'messages' not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

if user_query := st.chat_input("Ask about today's news..."):
    if not user_api_key:
        st.error('Please enter your API Key in the sidebar')
    else:
        st.session_state.messages.append({'role': 'user', 'content': user_query})
        with st.chat_message('user'):
            st.markdown(user_query)

        llm = ChatGroq(
            temperature=0,
            model_name='llama-3.3-70b-versatile',
            api_key=user_api_key
        ).bind_tools(tools)

        system_message = SystemMessage(content="""
        You are a live research assistant.
        You MUST use the web search tool to find the current information before answering.
        Answer the query clearly.
        """)

        agent = create_react_agent(llm, tools, prompt=system_message)

        langgraph_history = []
        for msg in st.session_state.messages:
            if msg['role'] == 'user':
                langgraph_history.append(HumanMessage(content=msg['content']))
            else:
                langgraph_history.append(AIMessage(content=msg['content']))

        with st.chat_message('assistant'):
            with st.spinner("🤖 Browsing the web and analyzing results..."):
                result_state = agent.invoke({'messages': langgraph_history})
                bot_answer = result_state['messages'][-1].content
            st.markdown(bot_answer)

        st.session_state.messages.append({"role": "assistant", "content": bot_answer})
