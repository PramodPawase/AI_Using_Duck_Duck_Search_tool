# The Live Web Surfing Assistant
# %%writefile app.py
import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pyngrok import ngrok
import subprocess
import time

# Initialize DuckDuckGo tool
web_tool = DuckDuckGoSearchRun()

def web_search(query: str) -> str:
    """Searches the web for current events, facts, or up-to-date information."""
    print(f"⭐ Web Search function called for: '{query}'")
    return web_tool.invoke(query)

tools = [web_search]

# Streamlit UI
st.title('🌍 The Live Internet Agent')
st.write("Ask me anything about current events. I will browse the web to find the answer.")

# Sidebar configuration
with st.sidebar:
    st.header('⚙️ System Config')
    user_api_key = st.text_input('Groq API Key:', type='password')
    # For testing, you hardcoded the key here
    user_api_key = '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'
    st.info('Equipped with: DuckDuckGo Web Search Tool')

    # Show chat history in sidebar
    st.header("💬 Chat History")
    if 'messages' in st.session_state and st.session_state.messages:
        for msg in st.session_state.messages:
            role = "🧑 User" if msg['role'] == 'user' else "🤖 Assistant"
            st.markdown(f"**{role}:** {msg['content']}")

# Memory
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Core Agentic AI Loop
if user_query := st.chat_input("Ask about today's news..."):
    if not user_api_key:
        st.error('Please enter your API Key in the sidebar')
    else:
        # Display user message
        st.session_state.messages.append({'role': 'user', 'content': user_query})
        with st.chat_message('user'):
            st.markdown(user_query)

        # Initialize LLM
        llm = ChatGroq(
            temperature=0,
            model_name='llama-3.3-70b-versatile',
            api_key=user_api_key
        )
        llm = llm.bind_tools(tools)

        system_prompt_text = """
        You are a live research assistant.
        You MUST use the web search tool to find the current information before answering.
        Answer the query clearly.
        """
        system_message = SystemMessage(content=system_prompt_text)

        agent = create_react_agent(llm, tools, prompt=system_message)

        # Translate Streamlit memory -> Langgraph memory
        langgraph_history = []
        for msg in st.session_state.messages:
            if msg['role'] == 'user':
                langgraph_history.append(HumanMessage(content=msg['content']))
            else:
                langgraph_history.append(AIMessage(content=msg['content']))

        # Execute agent with error handling and fallback
        with st.chat_message('assistant'):
            with st.spinner("🤖 Browsing the web and analyzing results..."):
                try:
                    # Try running the agent normally
                    result_state = agent.invoke({'messages': langgraph_history})
                    bot_answer = result_state['messages'][-1].content.strip()

                    if not bot_answer:
                        bot_answer = "⚠️ Sorry, I couldn’t find reliable information right now."

                except Exception as e:
                    # Log error for debugging
                    print(f"Error details: {e}")

                    # Fallback: use LLM directly without agent
                    try:
                        fallback_prompt = f"User asked: {user_query}\nProvide a helpful answer even without web search."
                        bot_answer = llm.invoke([HumanMessage(content=fallback_prompt)]).content.strip()
                    except Exception as inner_e:
                        print(f"Fallback error: {inner_e}")
                        bot_answer = "⚠️ Unable to process your request at the moment, but I’m here to help."

            st.markdown(bot_answer)

        # Save answer back to memory
        st.session_state.messages.append({"role": "assistant", "content": bot_answer})

# Ngrok setup
ngrok.set_auth_token("3FwzijMKi0H4nJC8bmHq8qvid54_7aC4TJDwJzohNij73b5iV")
