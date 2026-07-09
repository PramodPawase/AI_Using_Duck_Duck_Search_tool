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

# Custom CSS for styling
st.markdown("""
    <style>
        /* Header */
        .main-header {
            background-color: #2E86C1;
            color: white;
            padding: 12px;
            text-align: center;
            font-size: 26px;
            font-weight: bold;
            border-radius: 8px;
        }
        /* Footer */
        .main-footer {
            background-color: #2E86C1;
            color: white;
            padding: 8px;
            text-align: center;
            font-size: 14px;
            border-radius: 8px;
            margin-top: 20px;
        }
        /* Sidebar history items */
        .history-item {
            font-style: italic;
            color: #34495E;
            cursor: pointer;
            padding: 6px;
            border-bottom: 1px solid #ddd;
        }
        .history-item:hover {
            background-color: #f0f0f0;
        }
        /* Chat styling */
        .user-msg {
            font-weight: bold;
            color: #1A5276;
            font-family: "Trebuchet MS", sans-serif;
        }
        .assistant-msg {
            font-weight: bold;
            color: #117A65;
            font-family: "Georgia", serif;
        }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🌍 The Live Internet Agent</div>', unsafe_allow_html=True)
st.write("Ask me anything about current events. I will browse the web to find the answer.")

# Sidebar configuration
with st.sidebar:
    st.header('⚙️ System Config')
    user_api_key = st.text_input('Groq API Key:', type='password')
    # Hardcoded for testing
    user_api_key = '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'
    st.info('Equipped with: DuckDuckGo Web Search Tool')

    # Show summarized chat history
    st.header("💬 Chat History")
    if 'messages' in st.session_state and st.session_state.messages:
        for i, msg in enumerate(st.session_state.messages):
            summary = msg['content'][:40] + ("..." if len(msg['content']) > 40 else "")
            if st.button(summary, key=f"history_{i}"):
                st.session_state.selected_history = i

# Memory
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'selected_history' not in st.session_state:
    st.session_state.selected_history = None

# Show selected history on left side
if st.session_state.selected_history is not None:
    selected_msg = st.session_state.messages[st.session_state.selected_history]
    role = "🧑 User" if selected_msg['role'] == 'user' else "🤖 Assistant"
    css_class = "user-msg" if selected_msg['role'] == 'user' else "assistant-msg"
    st.markdown(f'<div class="{css_class}">{role}: {selected_msg["content"]}</div>', unsafe_allow_html=True)

# Core Agentic AI Loop
if user_query := st.chat_input("Ask about today's news..."):
    if not user_api_key:
        st.error('Please enter your API Key in the sidebar')
    else:
        # Display user message
        st.session_state.messages.append({'role': 'user', 'content': user_query})
        st.markdown(f'<div class="user-msg">🧑 User: {user_query}</div>', unsafe_allow_html=True)

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
        with st.spinner("🤖 Browsing the web and analyzing results..."):
            try:
                result_state = agent.invoke({'messages': langgraph_history})
                bot_answer = result_state['messages'][-1].content.strip()

                if not bot_answer:
                    bot_answer = "⚠️ Sorry, I couldn’t find reliable information right now."

            except Exception as e:
                print(f"Error details: {e}")
                try:
                    fallback_prompt = f"User asked: {user_query}\nProvide a helpful answer even without web search."
                    bot_answer = llm.invoke([HumanMessage(content=fallback_prompt)]).content.strip()
                except Exception as inner_e:
                    print(f"Fallback error: {inner_e}")
                    bot_answer = "⚠️ Unable to process your request at the moment, but I’m here to help."

        st.markdown(f'<div class="assistant-msg">🤖 Assistant: {bot_answer}</div>', unsafe_allow_html=True)

        # Save answer back to memory
        st.session_state.messages.append({"role": "assistant", "content": bot_answer})

# Footer
st.markdown('<div class="main-footer">© 2026 The Live Internet Agent | Powered by Groq + DuckDuckGo</div>', unsafe_allow_html=True)

# Ngrok setup
ngrok.set_auth_token("3FwzijMKi0H4nJC8bmHq8qvid54_7aC4TJDwJzohNij73b5iV")
