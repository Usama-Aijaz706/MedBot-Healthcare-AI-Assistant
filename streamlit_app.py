import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from streamlit_chat import message
import markdown
import re

# Page Configuration
st.set_page_config(
    page_title="MedBot - AI Healthcare Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .chat-container {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .bot-message {
        background: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: #333 !important;
    }
    
    .bot-message p {
        color: #333 !important;
        line-height: 1.6;
        margin: 0.2rem 0;
    }
    
    .bot-message div {
        color: #333 !important;
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Form submit button styling */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        font-size: 16px !important;
        margin-top: 10px !important;
    }
    
    .stFormSubmitButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }
    
    .chat-input {
        background: white;
        border: 2px solid #e9ecef;
        border-radius: 25px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .chat-input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Streamlit text input styling */
    .stTextInput > div > div > input {
        border-radius: 25px !important;
        border: 2px solid #e9ecef !important;
        padding: 12px 20px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #9ca3af !important;
        font-style: italic !important;
    }
    
    .response-type-selector {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .source-item {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 5px;
    }
    
    .disclaimer {
        background: linear-gradient (135deg, #ffeaa7 0%, #fab1a0 100%);
        border-left: 5px solid #e17055;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .enhanced-prompt {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border: 1px solid #74b9ff;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #333 !important;
    }
    
    .enhanced-prompt p {
        color: #333 !important;
        line-height: 1.6;
        margin: 0.5rem 0;
    }
    
    .final-response {
        background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
        border: 1px solid #a29bfe;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #333 !important;
    }
    
    .final-response p {
        color: #333 !important;
        line-height: 1.6;
        margin: 0.5rem 0;
    }
    
    /* Enhanced list styling */
    .bot-message ul {
        margin: 0.2rem 0;
        padding-left: 1.2rem;
    }
    
    .bot-message li {
        margin: 0.15rem 0;
        line-height: 1.4;
        color: #333;
        list-style: none;
    }
    
    .bot-message li:before {
        content: "•";
        color: #667eea;
        font-weight: bold;
        margin-right: 0.5rem;
        font-size: 1.2em;
    }
    
    /* Enhanced prompt styling */
    .enhanced-prompt ul {
        margin: 0.2rem 0;
        padding-left: 1.2rem;
    }
    
    .enhanced-prompt li {
        margin: 0.15rem 0;
        line-height: 1.4;
        color: #333;
        list-style: none;
    }
    
    .enhanced-prompt li:before {
        content: "•";
        color: #667eea;
        font-weight: bold;
        margin-right: 0.5rem;
        font-size: 1.2em;
    }
    
    /* Enhanced header styling with proper spacing */
    .bot-message h2 {
        color: #667eea;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
        page-break-after: avoid;
    }
    
    .bot-message h3 {
        color: #764ba2;
        font-size: 1.3rem;
        font-weight: bold;
        margin: 1.2rem 0 0.8rem 0;
        border-left: 3px solid #764ba2;
        padding-left: 0.8rem;
        page-break-after: avoid;
    }
    
    .bot-message h4 {
        color: #667eea;
        font-size: 1.1rem;
        font-weight: bold;
        margin: 1rem 0 0.6rem 0;
        page-break-after: avoid;
    }
    
    /* Add spacing between sections */
    .bot-message h2 + p,
    .bot-message h3 + p,
    .bot-message h4 + p {
        margin-top: 0.3rem;
    }
    
    /* Add spacing between paragraphs */
    .bot-message p {
        margin: 0.3rem 0;
        line-height: 1.5;
    }
    
    /* Add spacing between list items */
    .bot-message li {
        margin: 0.2rem 0;
        line-height: 1.4;
    }
    
    /* Add spacing between sections with visual separators */
    .bot-message h2:not(:first-child) {
        margin-top: 1rem;
        padding-top: 0.5rem;
        border-top: 2px solid #667eea;
        position: relative;
    }
    
    .bot-message h2:not(:first-child)::before {
        content: "";
        position: absolute;
        top: -1px;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
        border-radius: 1px;
    }
    
    .bot-message h3:not(:first-child) {
        margin-top: 0.8rem;
        padding-top: 0.3rem;
        border-top: 1px solid #e9ecef;
    }
    
    /* Ensure proper spacing after lists */
    .bot-message ul + p,
    .bot-message ol + p {
        margin-top: 1rem;
    }
    
    /* Add spacing before lists */
    .bot-message p + ul,
    .bot-message p + ol {
        margin-top: 0.5rem;
    }
    
    /* Ensure all text content is visible */
    .bot-message * {
        color: inherit;
    }
    
    .bot-message span {
        color: #333 !important;
    }
    
    /* Override any inherited light colors */
    .stMarkdown div {
        color: #333 !important;
    }
    
    .stMarkdown p {
        color: #333 !important;
    }
    
    /* Additional spacing for numbered sections */
    .bot-message h3:contains("1."),
    .bot-message h3:contains("2."),
    .bot-message h3:contains("3."),
    .bot-message h3:contains("4."),
    .bot-message h3:contains("5.") {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e9ecef;
    }
    
    /* Ensure proper spacing for all content blocks */
    .bot-message > * + * {
        margin-top: 0.4rem;
    }
    
    /* Special styling for blood pressure categories and similar structured content */
    .bot-message strong {
        color: #667eea;
        font-weight: 600;
    }
    
    /* Improve table-like content spacing */
    .bot-message p strong + br + em,
    .bot-message p em + br + strong {
        margin-top: 0.2rem;
        display: inline-block;
    }
    
    /* Enhanced styling for numbered sections */
    .bot-message .numbered-section {
        margin-top: 0.8rem !important;
        padding-top: 0.5rem !important;
        border-top: 2px solid #667eea !important;
        color: #764ba2 !important;
        font-size: 1.4rem !important;
        font-weight: bold !important;
        position: relative;
    }
    
    .bot-message .numbered-section::before {
        content: "";
        position: absolute;
        top: -1px;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
        border-radius: 1px;
    }
    
    /* Add visual separators between major sections */
    .bot-message h2:not(:first-child)::before {
        content: "";
        display: block;
        height: 1px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 0.3rem 0;
    }
    
    /* Beautiful horizontal line separator for content breaks */
    .bot-message .content-separator {
        height: 1px;
        background: linear-gradient(90deg, transparent, #667eea, #764ba2, #667eea, transparent);
        margin: 1rem 0;
        border-radius: 1px;
        opacity: 0.7;
    }
    
    /* Enhanced heading separators with beautiful lines */
    .bot-message h2:not(:first-child) {
        margin-top: 2rem !important;
        padding-top: 1.5rem !important;
        border-top: 3px solid transparent !important;
        background: linear-gradient(90deg, #667eea, #764ba2, #667eea) !important;
        background-clip: text !important;
        -webkit-background-clip: text !important;
        position: relative !important;
    }
    
    .bot-message h2:not(:first-child)::before {
        content: "";
        position: absolute;
        top: -3px;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
        border-radius: 2px;
        box-shadow: 0 2px 6px rgba(102, 126, 234, 0.4);
    }
    
    .bot-message h3:not(:first-child) {
        margin-top: 1.5rem !important;
        padding-top: 1rem !important;
        border-top: 2px solid transparent !important;
        position: relative !important;
    }
    
    .bot-message h3:not(:first-child)::before {
        content: "";
        position: absolute;
        top: -2px;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #e9ecef, #667eea, #e9ecef);
        border-radius: 1px;
        box-shadow: 0 1px 3px rgba(102, 126, 234, 0.3);
    }
    
    .bot-message h4:not(:first-child) {
        margin-top: 1rem !important;
        padding-top: 0.8rem !important;
        border-top: 1px solid transparent !important;
        position: relative !important;
    }
    
    .bot-message h4:not(:first-child)::before {
        content: "";
        position: absolute;
        top: -1px;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, #f0f0f0, #764ba2, #f0f0f0);
        border-radius: 1px;
    }
    
    /* Special styling for numbered headings with enhanced separators */
    .bot-message .numbered-section {
        margin-top: 1.5rem !important;
        padding-top: 1rem !important;
        border-top: 2px solid transparent !important;
        color: #764ba2 !important;
        font-size: 1.4rem !important;
        font-weight: bold !important;
        position: relative !important;
    }
    
    .bot-message .numbered-section::before {
        content: "";
        position: absolute;
        top: -2px;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
        border-radius: 1px;
        box-shadow: 0 1px 4px rgba(102, 126, 234, 0.3);
    }
    
    /* Decorative line separators between major sections */
    .bot-message .section-divider {
        height: 3px;
        background: linear-gradient(90deg, transparent, #667eea, #764ba2, #667eea, transparent);
        margin: 1.5rem 0;
        border-radius: 2px;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        position: relative;
    }
    
    .bot-message .section-divider::after {
        content: "●";
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: #764ba2;
        font-size: 8px;
        background: white;
        padding: 2px;
        border-radius: 50%;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* Improve spacing for category-style content */
    .bot-message p strong:contains("Category:") {
        display: block;
        margin-bottom: 0.3rem;
        color: #667eea;
        font-size: 1.1rem;
    }
    
    .bot-message p strong:contains("Systolic"),
    .bot-message p strong:contains("Diastolic") {
        display: inline-block;
        margin-right: 0.8rem;
        color: #764ba2;
    }
    
    /* Reduce gaps between sections */
    .bot-message h3 + p,
    .bot-message h4 + p {
        margin-top: 0.2rem;
    }
    
    /* Compact list spacing */
    .bot-message ul + p,
    .bot-message ol + p {
        margin-top: 0.4rem;
    }
    
    .bot-message p + ul,
    .bot-message p + ol {
        margin-top: 0.2rem;
    }
    
    /* Blood Pressure Table Styling */
    .bot-message .blood-pressure-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
    }
    
    .bot-message .blood-pressure-table thead {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    
    .bot-message .blood-pressure-table th {
        padding: 12px 16px;
        text-align: left;
        font-weight: 600;
        font-size: 14px;
        border: none;
    }
    
    .bot-message .blood-pressure-table tbody tr {
        background: white;
        border-bottom: 1px solid #e9ecef;
        transition: background-color 0.2s;
    }
    
    .bot-message .blood-pressure-table tbody tr:hover {
        background: #f8f9fa;
    }
    
    .bot-message .blood-pressure-table tbody tr:last-child {
        border-bottom: none;
    }
    
    .bot-message .blood-pressure-table td {
        padding: 12px 16px;
        text-align: left;
        font-size: 14px;
        color: #333;
        border: none;
    }
    
    .bot-message .blood-pressure-table td:first-child {
        font-weight: 600;
        color: #667eea;
    }
    
    .bot-message .blood-pressure-table td:nth-child(2),
    .bot-message .blood-pressure-table td:nth-child(3) {
        font-family: 'Courier New', monospace;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

class MedBotStreamlit:
    def __init__(self):
        self.api_url = "http://localhost:8000/api/chat"
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            st.write("🔄 Initialized empty chat history")
        
        if 'current_chat_id' not in st.session_state:
            st.session_state.current_chat_id = f"chat_{int(time.time())}"
        
        if 'chat_count' not in st.session_state:
            st.session_state.chat_count = 0
        
        if 'total_tokens' not in st.session_state:
            st.session_state.total_tokens = 0
        
        if 'response_time' not in st.session_state:
            st.session_state.response_time = []
        
        if 'user_name' not in st.session_state:
            st.session_state.user_name = None
        
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {
                'detail_level': 'detailed',
                'response_format': 'markdown',
                'include_sources': True,
                'include_disclaimer': True,
                'preferred_language': 'English'
            }
        
        # Debug info
        st.sidebar.write(f"📊 Chat History Length: {len(st.session_state.chat_history)}")
        st.sidebar.write(f"🆔 Current Chat ID: {st.session_state.current_chat_id}")
        if st.session_state.user_name:
            st.sidebar.write(f"👤 User: {st.session_state.user_name}")
    
    def create_detailed_prompt(self, user_message, detail_level, response_format):
        """Create a detailed prompt based on user preferences"""
        
        detail_instructions = {
            'brief': "Provide a concise, to-the-point response with key facts only.",
            'moderate': "Provide a balanced response with essential information and some context.",
            'detailed': "Provide a comprehensive response with thorough explanations, examples, and context.",
            'expert': "Provide an expert-level response with in-depth analysis, research findings, and detailed explanations."
        }
        
        format_instructions = {
            'markdown': "Format your response using markdown for better readability. Use headers, bullet points, tables, and emphasis where appropriate.",
            'structured': "Organize your response in a clear, structured format with sections and subsections.",
            'narrative': "Provide your response in a flowing, narrative style that's easy to follow."
        }
        
        enhanced_prompt = f"""
**ENHANCED USER REQUEST:**
{user_message}

**RESPONSE REQUIREMENTS:**
- Detail Level: {detail_level} - {detail_instructions[detail_level]}
- Format: {format_instructions[response_format]}
- Include relevant medical terminology and explanations
- Provide actionable insights when applicable
- Use evidence-based information from medical sources
- Structure the response for optimal readability

**CONTEXT:**
The user is seeking healthcare information and requires a response that is {detail_level} and formatted in {response_format} style. 
Please ensure the response is comprehensive, accurate, and tailored to their specific needs.
"""
        return enhanced_prompt
    
    def create_context_enhanced_prompt(self, user_message, detail_level, response_format, rag_context, chat_history):
        """Create a prompt that uses RAG context and Azure model for comprehensive responses"""
        
        detail_instructions = {
            'brief': "Provide a concise, to-the-point response with key facts only.",
            'moderate': "Provide a balanced response with essential information and some context.",
            'detailed': "Provide a comprehensive response with thorough explanations, examples, and context.",
            'expert': "Provide an expert-level response with in-depth analysis, research findings, and detailed explanations."
        }
        
        format_instructions = {
            'markdown': "Format your response using markdown for better readability. Use headers, bullet points, tables, and emphasis where appropriate.",
            'structured': "Organize your response in a clear, structured format with sections and subsections.",
            'narrative': "Provide your response in a flowing, narrative style that's easy to follow."
        }
        
        # Check if this is a detail request
        is_detail_request = any(pattern in user_message.lower() for pattern in ['explain in detail', 'explain further', 'tell me more', 'please explain'])
        
        # Format chat history for context
        chat_history_context = ""
        if chat_history and len(chat_history) > 0:
            # Get the last few messages for context (avoid overwhelming the prompt)
            recent_messages = chat_history[-3:]  # Last 3 messages
            chat_history_context = "\n\n**RECENT CONVERSATION CONTEXT:**\n"
            
            # Find the last medical question to combine with follow-up
            last_medical_question = ""
            for msg in reversed(recent_messages):
                if msg.get('role') == 'user':
                    content = msg.get('content', '').lower()
                    # Check if this was a medical question
                    if any(term in content for term in ['microbiology', 'medical', 'health', 'disease', 'treatment', 'symptom', 'what is', 'tell me about', 'explain']):
                        last_medical_question = msg.get('content', '')
                        break
            
            # If this is a follow-up question, combine it with the last medical question
            follow_up_patterns = [
                'explain in detail', 'explain further', 'tell me more',
                'can you clarify', 'i don\'t understand', 'how does this work',
                'why is this important', 'give me examples', 'show me',
                'demonstrate', 'illustrate', 'describe', 'break down',
                'simplify', 'summarize', 'recap', 'please explain',
                'explain it', 'explain this', 'explain that'
            ]
            
            is_follow_up = any(pattern in user_message.lower() for pattern in follow_up_patterns)
            
            if is_follow_up and last_medical_question:
                chat_history_context += f"**FOLLOW-UP CONTEXT:** This is a follow-up question to: '{last_medical_question}'\n\n"
                if is_detail_request:
                    chat_history_context += "**DETAIL REQUEST:** The user is asking for an extremely detailed explanation. Provide the most comprehensive response possible.\n\n"
            
            # Add recent conversation context
            for i, msg in enumerate(recent_messages, 1):
                role = "User" if msg.get('role') == 'user' else "Assistant"
                content = msg.get('content', '')[:300] + "..." if len(msg.get('content', '')) > 300 else msg.get('content', '')
                chat_history_context += f"{i}. {role}: {content}\n"
        
        # Enhanced detail instructions for detail requests
        detail_enhancement = ""
        if is_detail_request:
            detail_enhancement = """
**EXTREME DETAIL REQUIREMENTS:**
- This is a "explain in detail" request - provide the MOST comprehensive response possible
- Use detailed PARAGRAPHS, not bullet points or summaries
- Include extensive examples, case studies, and real-world applications
- Break down every concept into multiple detailed explanations with substantial paragraphs
- Use detailed tables, lists, and structured information where appropriate
- Include historical context and evolution of knowledge
- Provide multiple perspectives and approaches
- Include technical details while maintaining accessibility
- Use extensive markdown formatting for optimal structure
- Provide actionable insights and practical recommendations
- Include cross-references to related topics and concepts
- Address edge cases and exceptions
- Provide step-by-step explanations for complex processes
- Include statistical data and research findings when relevant
- Use analogies and metaphors to enhance understanding
- Provide both beginner and advanced level information
- Include troubleshooting guides and common problems
- Provide comprehensive resource lists and references
- Write in a conversational, educational tone like a knowledgeable healthcare professional"""
        
        # Create a comprehensive prompt that uses RAG context
        context_enhanced_prompt = f"""
**🧠 COMPREHENSIVE MEDICAL ANALYSIS REQUEST:**

**USER QUESTION:** {user_message}

**AVAILABLE MEDICAL CONTEXT (RAG System):**
{rag_context}{chat_history_context}

**RESPONSE REQUIREMENTS:**
- Detail Level: {detail_level} - {detail_instructions[detail_level]}
- Format: {format_instructions[response_format]}
- Use the provided medical context as your primary knowledge base
- Expand on the context with additional medical insights and explanations
- Include relevant medical terminology and definitions
- Provide actionable insights and recommendations when applicable
- Use evidence-based information and cite the sources
- Structure the response for optimal readability and understanding
- Make the response comprehensive and educational{detail_enhancement}

**INSTRUCTIONS FOR AZURE MODEL:**
You are a medical AI specialist. Use the provided RAG context as your foundation, then expand it into a comprehensive, well-structured medical response. 
The response should be {detail_level} and formatted in {response_format} style.
Combine the context information with your medical knowledge to create a MASSIVE, well-explained response that covers:

**STANDARD SECTIONS:**
1. **Definition and Overview** - Clear explanation of the medical concept
2. **Causes and Risk Factors** - Detailed analysis of contributing factors
3. **Symptoms and Clinical Presentation** - Comprehensive symptom description
4. **Diagnosis and Testing** - Available diagnostic methods and procedures
5. **Treatment Options** - Current treatment approaches and recommendations
6. **Prevention and Management** - Preventive measures and ongoing care
7. **Prognosis and Outlook** - Expected outcomes and long-term considerations
8. **Additional Resources** - Where to find more information

**EXTRA DETAIL SECTIONS (for detail requests):**
9. **Research and Latest Developments** - Current findings and future directions
10. **Case Studies and Examples** - Real-world applications and scenarios
11. **Common Misconceptions** - Addressing myths and clarifying misunderstandings
12. **Global and Public Health Perspectives** - Worldwide impact and implications
13. **Technical Deep-Dive** - Advanced concepts and detailed mechanisms
14. **Comparative Analysis** - How this relates to other medical concepts
15. **Practical Applications** - Step-by-step guides and troubleshooting

**CRITICAL FORMATTING REQUIREMENTS:**
- Use detailed PARAGRAPHS for explanations, not bullet points or summaries
- Each section should have 3-5 detailed paragraphs explaining the concepts thoroughly
- Use bullet points ONLY for lists of items (e.g., types of bacteria, symptoms)
- Write in a conversational, educational tone like a knowledgeable healthcare professional
- Include detailed explanations, examples, and context for every concept
- Use tables where appropriate for structured data comparison
- Create clear visual hierarchy with headers and subheaders
- Ensure each section provides substantial, helpful information

**FORMATTING REQUIREMENTS:**
- Use extensive markdown formatting (headers, subheaders, detailed paragraphs)
- Include tables where appropriate for structured data
- Use bold and italic text for emphasis
- Create clear visual hierarchy and organization
- Use code blocks for technical information when relevant
- Ensure excellent readability and structure

**CONTEXT AWARENESS:**
- If this is a follow-up question, build upon the previous conversation context
- Maintain conversation continuity and reference earlier points
- If the user asks for "more detail" or "explain further", expand on the most relevant aspects
- Ensure the response directly addresses what the user is asking for

**DETAIL LEVEL ADJUSTMENT:**
- For "explain in detail" requests, provide the MOST comprehensive response possible
- Include extensive examples, case studies, and real-world applications
- Break down every concept into multiple detailed explanations with substantial paragraphs
- Provide both basic and advanced information
- Include troubleshooting guides and common problems
- Write detailed, educational explanations that a healthcare professional would provide

**IMPORTANT:** This is NOT a summarizer. This is a detailed healthcare chatbot that provides comprehensive, helpful explanations. Each section should contain detailed paragraphs that thoroughly explain the concepts, provide examples, and give practical insights. Avoid bullet-point summaries - instead, write detailed, educational explanations that a healthcare professional would provide to a patient.

Ensure the response is comprehensive, accurate, and provides immense value to the user while maintaining a warm, professional tone. For detail requests, make this the most thorough and detailed response possible with substantial paragraphs, not summaries.
"""
        return context_enhanced_prompt
    
    def get_rag_context(self, user_message):
        """Get RAG context from MedBot API"""
        try:
            payload = {
                "message": user_message,
                "user_id": f"user_{int(time.time())}",
                "conversation_id": st.session_state.current_chat_id,
                "get_context_only": True
            }
            
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"RAG Context Error: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error getting RAG context: {str(e)}")
            return None
    
    def get_azure_enhanced_response(self, context_enhanced_prompt):
        """Get enhanced response from Azure OpenAI with chat history context"""
        try:
            # Include chat history for context-aware responses
            chat_history = st.session_state.chat_history if 'chat_history' in st.session_state else []
            
            payload = {
                "message": context_enhanced_prompt,
                "user_id": f"user_{int(time.time())}",
                "conversation_id": st.session_state.current_chat_id,
                "use_azure_enhancement": True,
                "generate_comprehensive_response": True,
                "chat_history": chat_history  # Pass chat history for context
            }
            
            response = requests.post(self.api_url, json=payload, timeout=60)  # Longer timeout for comprehensive responses
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"Azure Enhancement Error: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error with Azure enhancement: {str(e)}")
            return None
    
    def format_rag_context(self, relevant_chunks):
        """Format RAG context chunks into readable text"""
        if not relevant_chunks:
            return "No relevant medical context found."
        
        formatted_context = []
        for i, chunk in enumerate(relevant_chunks, 1):
            source = chunk.get('metadata', {}).get('source', 'Unknown Source')
            content = chunk.get('content', 'No content')
            relevance = chunk.get('similarity_score', 'N/A')
            
            formatted_context.append(f"""
**Source {i}: {source}**
**Relevance Score: {relevance}**
**Content:**
{content}
---""")
        
        return "\n".join(formatted_context)
    
    def extract_user_name(self, message: str) -> str:
        """Extract user name from message if present."""
        import re
        
        # Common patterns for name introduction
        name_patterns = [
            r"i am (\w+)",
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"call me (\w+)",
            r"this is (\w+)",
            r"(\w+) here",
            r"(\w+) speaking"
        ]
        
        message_lower = message.lower()
        
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                name = match.group(1).capitalize()
                return name
        
        return None
    
    def update_user_name(self, message: str):
        """Update user name if found in message."""
        extracted_name = self.extract_user_name(message)
        if extracted_name and not st.session_state.user_name:
            st.session_state.user_name = extracted_name
            st.success(f"👋 Nice to meet you, {extracted_name}! I'll remember your name for this chat session.")
            return extracted_name
        return None
    
    def get_bot_response(self, enhanced_prompt, user_preferences):
        """Get response from MedBot API"""
        try:
            start_time = time.time()
            
            payload = {
                "message": enhanced_prompt,
                "user_id": f"user_{int(time.time())}",
                "conversation_id": st.session_state.current_chat_id,
                "preferences": user_preferences
            }
            
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Update metrics
            st.session_state.response_time.append(response_time)
            st.session_state.chat_count += 1
            
            return response.json(), response_time
            
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None, 0
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None, 0
    
    def format_markdown_response(self, response_text):
        """Format response text with enhanced markdown"""
        if not response_text:
            return "No content available"
        
        # AGGRESSIVE cleanup of all markdown artifacts
        formatted_text = response_text
        
        # Remove all leading/trailing ** and *
        formatted_text = formatted_text.strip()
        while formatted_text.startswith('**') or formatted_text.startswith('*'):
            if formatted_text.startswith('**'):
                formatted_text = formatted_text[2:].strip()
            else:
                formatted_text = formatted_text[1:].strip()
        
        while formatted_text.endswith('**') or formatted_text.endswith('*'):
            if formatted_text.endswith('**'):
                formatted_text = formatted_text[:-2].strip()
            else:
                formatted_text = formatted_text[:-1].strip()
        
        # Clean up headers with extra ** around them
        formatted_text = re.sub(r'^\*\*(.*?)\*\*$', r'\1', formatted_text, flags=re.MULTILINE)
        formatted_text = re.sub(r'^\*\*(.*?)\*\*', r'\1', formatted_text, flags=re.MULTILINE)
        
        # Convert numbered headers (1. 2. 3.) to proper headers with enhanced styling
        formatted_text = re.sub(r'^(\d+)\.\s+(.*?)$', r'<h3 class="numbered-section">\1. \2</h3>', formatted_text, flags=re.MULTILINE)
        
        # Convert markdown headers to HTML
        formatted_text = re.sub(r'^### (.*?)$', r'<h4>\1</h4>', formatted_text, flags=re.MULTILINE)
        formatted_text = re.sub(r'^## (.*?)$', r'<h3>\1</h3>', formatted_text, flags=re.MULTILINE)
        formatted_text = re.sub(r'^# (.*?)$', r'<h2>\1</h2>', formatted_text, flags=re.MULTILINE)
        
        # Convert lists to proper HTML
        lines = formatted_text.split('\n')
        in_list = False
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('• ') or line.startswith('- '):
                if not in_list:
                    formatted_lines.append('<ul>')
                    in_list = True
                # Convert bullet to list item (remove the original bullet symbol)
                list_item = line[2:] if line.startswith('• ') else line[2:]
                # Clean up any remaining bullet symbols in the content
                list_item = list_item.replace('•', '').replace('-', '').strip()
                formatted_lines.append(f'<li>{list_item}</li>')
            else:
                if in_list:
                    formatted_lines.append('</ul>')
                    in_list = False
                formatted_lines.append(line)
        
        # Close any open list
        if in_list:
            formatted_lines.append('</ul>')
        
        formatted_text = '\n'.join(formatted_lines)
        
        # Convert emphasis to HTML (simplified approach)
        formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_text)
        formatted_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted_text)
        
        # Add special handling for structured content like blood pressure categories
        # This will add proper spacing for category-style content
        formatted_text = re.sub(
            r'(\*\*Category:\*\*.*?)(\*\*Systolic.*?)(\*\*Diastolic.*?)',
            r'\1<br><br>\2<br>\3',
            formatted_text,
            flags=re.DOTALL
        )
        
        # Convert blood pressure table format to proper HTML table
        # Look for patterns like "Category: Normal, Systolic: <120, Diastolic: <80"
        # Handle multiple formats including the one from the image
        formatted_text = re.sub(
            r'\*\*Category:\*\*\s*(\w+(?:\s+Stage\s+\d+)?(?:\s+Crisis)?)\s*\*\*Systolic\s*\(mmHg\):\*\*\s*([^,]+)\s*\*\*Diastolic\s*\(mmHg\):\*\*\s*([^,]+)',
            r'<tr><td><strong>\1</strong></td><td>\2</td><td>\3</td></tr>',
            formatted_text,
            flags=re.IGNORECASE
        )
        
        # Also handle the format from the image: "Normal: Systolic <120, Diastolic <80"
        formatted_text = re.sub(
            r'(\w+(?:\s+Stage\s+\d+)?(?:\s+Crisis)?):\s*Systolic\s*([^,]+),\s*Diastolic\s*([^,]+)',
            r'<tr><td><strong>\1</strong></td><td>\2</td><td>\3</td></tr>',
            formatted_text,
            flags=re.IGNORECASE
        )
        
        # Handle bullet point format: "• Normal: Systolic <120, Diastolic <80"
        formatted_text = re.sub(
            r'•\s*(\w+(?:\s+Stage\s+\d+)?(?:\s+Crisis)?):\s*Systolic\s*([^,]+),\s*Diastolic\s*([^,]+)',
            r'<tr><td><strong>\1</strong></td><td>\2</td><td>\3</td></tr>',
            formatted_text,
            flags=re.IGNORECASE
        )
        
        # Add table wrapper if we find table rows
        if '<tr>' in formatted_text:
            formatted_text = re.sub(
                r'(<tr>.*?</tr>)',
                r'<table class="blood-pressure-table"><thead><tr><th><strong>Category</strong></th><th><strong>Systolic (mmHg)</strong></th><th><strong>Diastolic (mmHg)</strong></th></tr></thead><tbody>\1</tbody></table>',
                formatted_text,
                flags=re.DOTALL
            )
        
        # Add beautiful horizontal separators between major sections
        # Look for patterns like "Encouragement" or "Sources:" sections
        formatted_text = re.sub(
            r'(<p>.*?</p>)\s*(<h[34]>.*?</h3>)',
            r'\1<div class="content-separator"></div>\2',
            formatted_text,
            flags=re.DOTALL
        )
        
        # Add separators before numbered sections
        formatted_text = re.sub(
            r'(<p>.*?</p>)\s*(<h3 class="numbered-section">)',
            r'\1<div class="content-separator"></div>\2',
            formatted_text,
            flags=re.DOTALL
        )
        
        # Add beautiful separators ONLY between paragraphs and new headings
        # This creates clean separation without cluttering the content
        
        # Add separators between paragraphs and new headings (H2, H3, H4)
        formatted_text = re.sub(
            r'(</p>)\s*(<h[234]>)',
            r'\1<div class="content-separator"></div>\2',
            formatted_text,
            flags=re.DOTALL
        )
        
        # Add separators between list endings and new headings
        formatted_text = re.sub(
            r'(</ul>|</ol>)\s*(<h[234]>)',
            r'\1<div class="content-separator"></div>\2',
            formatted_text,
            flags=re.DOTALL
        )
        
        # Add separators between numbered sections and new content
        formatted_text = re.sub(
            r'(</h3 class="numbered-section">)\s*(<p>)',
            r'\1<div class="content-separator"></div>\2',
            formatted_text,
            flags=re.DOTALL
        )
        
        # Clean up multiple consecutive separators
        formatted_text = re.sub(
            r'(<div class="content-separator"></div>)\s*(<div class="content-separator"></div>)',
            r'\1',
            formatted_text,
            flags=re.DOTALL
        )
        
        return formatted_text
    
    def combine_responses(self, rag_context, azure_response, sources):
        """Combine RAG context with Azure enhanced response for comprehensive understanding"""
        combined = f"""
**📚 RAG CONTEXT (Medical Knowledge Base):**
{rag_context}

**🧠 AZURE ENHANCED RESPONSE:**
{azure_response}

**💡 COMPREHENSIVE INSIGHT:**
This response combines your medical knowledge base (RAG context) with Azure's intelligent analysis to provide you with the most comprehensive, well-structured, and educational healthcare information available.
"""
        return combined
    
    def handle_message_send(self, user_input):
        """Handle message sending when Enter is pressed"""
        if user_input and user_input.strip():
            # This will be handled in the main loop
            pass
    
    def display_chat_message(self, role, content, sources=None, is_enhanced=False):
        """Display a chat message with enhanced styling"""
        # Handle empty or invalid content
        if not content or not isinstance(content, str):
            content = "No content available"
        
        # Debug output removed - response is working correctly
        
        if role == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>👤 You:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            if is_enhanced and "📚 RAG CONTEXT (Medical Knowledge Base):" in content:
                # Split combined response
                parts = content.split("🧠 AZURE ENHANCED RESPONSE:")
                rag_context = parts[0].replace("📚 RAG CONTEXT (Medical Knowledge Base):", "").strip()
                azure_response = parts[1].strip() if len(parts) > 1 else ""
                
                # Remove the combined insight part if present
                if "💡 COMPREHENSIVE INSIGHT:" in azure_response:
                    azure_response = azure_response.split("💡 COMPREHENSIVE INSIGHT:")[0].strip()
                
                # Clean up markdown artifacts
                azure_response = azure_response.strip()
                if azure_response.endswith("**"):
                    azure_response = azure_response[:-2].strip()
                
                # Display RAG context
                if rag_context:
                    with st.expander("📚 Medical Knowledge Base (RAG Context)", expanded=False):
                        st.markdown(f"""
                        <div class="enhanced-prompt">
                            {self.format_markdown_response(rag_context)}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Display Azure enhanced response
                if azure_response:
                    # Format the response properly
                    formatted_response = self.format_markdown_response(azure_response)
                    
                    # Debug output removed - formatting issue identified and fixed
                    
                    st.markdown(f"""
                    <div class="bot-message">
                        {formatted_response}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="bot-message">
                    <strong>🤖 MedBot:</strong><br>
                    {self.format_markdown_response(content)}
                </div>
                """, unsafe_allow_html=True)
            
            # Display sources if available
            if sources and st.session_state.user_preferences['include_sources']:
                with st.expander("📚 Information Sources", expanded=False):
                    for source in sources:
                        if isinstance(source, dict):
                            source_name = source.get('source', 'Unknown Source')
                            relevance = source.get('relevance', 'N/A')
                        else:
                            source_name = str(source)
                            relevance = 'N/A'
                        
                        st.markdown(f"""
                        <div class="source-item">
                            <strong>{source_name}</strong><br>
                            <em>Relevance: {relevance}</em>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Display disclaimer
            if st.session_state.user_preferences['include_disclaimer']:
                st.markdown("""
                <div class="disclaimer">
                    ⚠️ <strong>Disclaimer:</strong> This information is for educational purposes only. 
                    Always consult healthcare professionals for medical advice.
                </div>
                """, unsafe_allow_html=True)
    
    def display_analytics(self):
        """Display chat analytics and metrics"""
        st.sidebar.markdown("## 📊 Chat Analytics")
        
        # Basic metrics
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Total Chats", st.session_state.chat_count)
        with col2:
            avg_response_time = sum(st.session_state.response_time) / len(st.session_state.response_time) if st.session_state.response_time else 0
            st.metric("Avg Response Time", f"{avg_response_time:.2f}s")
        
        # Response time chart
        if st.session_state.response_time:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=st.session_state.response_time,
                mode='lines+markers',
                name='Response Time',
                line=dict(color='#667eea', width=2),
                marker=dict(size=8, color='#764ba2')
            ))
            fig.update_layout(
                title="Response Time Trends",
                xaxis_title="Chat Number",
                yaxis_title="Response Time (seconds)",
                height=300,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.sidebar.plotly_chart(fig, use_container_width=True)
    
    def display_user_preferences(self):
        """Display and manage user preferences"""
        st.sidebar.markdown("## ⚙️ User Preferences")
        
        with st.sidebar.form("preferences_form"):
            detail_level = st.selectbox(
                "Detail Level",
                ["brief", "moderate", "detailed", "expert"],
                index=2
            )
            
            response_format = st.selectbox(
                "Response Format",
                ["markdown", "structured", "narrative"],
                index=0
            )
            
            include_sources = st.checkbox("Include Sources", value=True)
            include_disclaimer = st.checkbox("Include Disclaimer", value=True)
            preferred_language = st.selectbox("Preferred Language", ["English", "Spanish", "French", "German"])
            
            if st.form_submit_button("Update Preferences"):
                st.session_state.user_preferences.update({
                    'detail_level': detail_level,
                    'response_format': response_format,
                    'include_sources': include_sources,
                    'include_disclaimer': include_disclaimer,
                    'preferred_language': preferred_language
                })
                st.success("Preferences updated!")
    
    def display_chat_history(self):
        """Display chat history in sidebar"""
        st.sidebar.markdown("## 💬 Chat History")
        
        if not st.session_state.chat_history:
            st.sidebar.info("No chat history yet. Start a conversation!")
            return
        
        # Display chat history as individual messages
        for i, message_data in enumerate(st.session_state.chat_history[-10:]):  # Show last 10 messages
            # Create a title from the message content
            title = message_data.get('content', 'Message')[:30]
            if len(message_data.get('content', '')) > 30:
                title += "..."
            
            if st.sidebar.button(f"💬 {title}", key=f"chat_{i}"):
                # This would load the specific message - for now just show info
                st.sidebar.info(f"Message: {message_data.get('content', 'No content')[:100]}...")
    
    def export_chat_history(self):
        """Export chat history to various formats"""
        if not st.session_state.chat_history:
            st.warning("No chat history to export!")
            return
        
        export_format = st.selectbox("Export Format", ["JSON", "CSV", "TXT"])
        
        if export_format == "JSON":
            data = {
                "chat_id": st.session_state.current_chat_id,
                "timestamp": datetime.now().isoformat(),
                "messages": st.session_state.chat_history
            }
            st.download_button(
                label="Download JSON",
                data=json.dumps(data, indent=2),
                file_name=f"medbot_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        elif export_format == "CSV":
            # Convert messages to a format suitable for CSV
            export_data = []
            for msg in st.session_state.chat_history:
                export_data.append({
                    'role': msg.get('role', 'unknown'),
                    'content': msg.get('content', ''),
                    'timestamp': msg.get('timestamp', ''),
                    'sources': str(msg.get('sources', [])),
                    'is_enhanced': msg.get('is_enhanced', False)
                })
            
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"medbot_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        elif export_format == "TXT":
            text_content = f"MedBot Chat Export\n{'='*50}\n\n"
            for msg in st.session_state.chat_history:
                role = msg.get('role', 'unknown').upper()
                content = msg.get('content', 'No content')
                text_content += f"{role}: {content}\n\n"
            
            st.download_button(
                label="Download TXT",
                data=text_content,
                file_name=f"medbot_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    def run(self):
        """Main application runner"""
        try:
            # Header
            st.markdown("""
            <div class="main-header">
                <h1>🏥 MedBot - AI Healthcare Assistant</h1>
                <p>Your intelligent healthcare companion powered by advanced AI and medical knowledge</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Sidebar
            with st.sidebar:
                st.markdown('<div class="sidebar-header"><h3>🎯 Quick Actions</h3></div>', unsafe_allow_html=True)
                
                # New Chat Button
                if st.button("🆕 New Chat", use_container_width=True):
                    st.session_state.chat_history = []
                    st.session_state.current_chat_id = f"chat_{int(time.time())}"
                    st.rerun()
                
                # Clear History Button
                if st.button("🗑️ Clear History", use_container_width=True):
                    st.session_state.chat_history = []
                    st.session_state.chat_count = 0
                    st.rerun()
                
                st.markdown("---")
                
                # User Preferences
                self.display_user_preferences()
                
                st.markdown("---")
                
                # Chat History
                self.display_chat_history()
                
                st.markdown("---")
                
                # Analytics
                self.display_analytics()
                
                st.markdown("---")
                
                # Export Options
                st.markdown("## 📤 Export Options")
                self.export_chat_history()
            
            # Main Chat Area - Much wider chat area
            col1, col2 = st.columns([20, 1])
            
            with col1:
                st.markdown("## 💬 Chat Interface")
                
                # Display chat history
                if st.session_state.chat_history:
                    for message_data in st.session_state.chat_history:
                        try:
                            self.display_chat_message(
                                message_data.get('role', 'unknown'),
                                message_data.get('content', ''),
                                message_data.get('sources'),
                                message_data.get('is_enhanced', False)
                            )
                        except Exception as e:
                            st.error(f"Error displaying message: {str(e)}")
                            st.write("Message data:", message_data)
                else:
                    st.info("💬 Start a conversation by typing a message below!")
                    
                    # Welcome message and examples
                    st.markdown("""
                    <div class="feature-card">
                        <h4>👋 Welcome to MedBot!</h4>
                        <p>I'm your AI healthcare assistant. You can:</p>
                        <ul>
                            <li>🔬 Ask about medical topics (e.g., "What is microbiology?")</li>
                            <li>👤 Introduce yourself (e.g., "I am Usama")</li>
                            <li>💊 Get detailed medical information</li>
                            <li>📚 View source documents and relevance scores</li>
                        </ul>
                        <p><strong>Try these examples:</strong></p>
                        <ul>
                            <li>"I am Usama, can you tell me about diabetes?"</li>
                            <li>"What is radiology and how does it work?"</li>
                            <li>"Explain the symptoms of hypertension"</li>
                            <li>"Tell me about microbiology and its importance"</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Chat input with Enter key support using form
                with st.form(key="chat_form", clear_on_submit=True):
                    user_input = st.text_input(
                        "Ask me about healthcare, symptoms, treatments, or medical conditions...",
                        key="user_input",
                        placeholder="Type your medical question here and press Enter...",
                        label_visibility="collapsed"
                    )
                    
                    # Hidden submit button for Enter key support
                    submitted = st.form_submit_button("Send", use_container_width=True, type="primary")
                    
                    if submitted and user_input and user_input.strip():
                        try:
                            # Check for and update user name
                            self.update_user_name(user_input)
                            
                            # Add user message to history
                            st.session_state.chat_history.append({
                                'role': 'user',
                                'content': user_input,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            # Update chat count
                            st.session_state.chat_count += 1
                            
                            # Step 1: Get RAG context from medical knowledge base
                            start_time = time.time()
                            with st.spinner("🔍 Retrieving medical context..."):
                                rag_response = self.get_rag_context(user_input)
                            
                            if rag_response and rag_response.get('relevant_chunks'):
                                # Extract RAG context
                                rag_context = self.format_rag_context(rag_response.get('relevant_chunks'))
                                sources = rag_response.get('sources', [])
                                
                                # Step 2: Create context-enhanced prompt for Azure with chat history
                                context_enhanced_prompt = self.create_context_enhanced_prompt(
                                    user_input,
                                    st.session_state.user_preferences['detail_level'],
                                    st.session_state.user_preferences['response_format'],
                                    rag_context,
                                    st.session_state.chat_history  # Pass chat history for context
                                )
                                
                                # Step 3: Get comprehensive Azure-enhanced response with chat history
                                with st.spinner("🧠 MedBot thinking..."):
                                    azure_response = self.get_azure_enhanced_response(context_enhanced_prompt)
                                
                                if azure_response:
                                    # Calculate response time
                                    response_time = time.time() - start_time
                                    st.session_state.response_time.append(response_time)
                                    
                                    # Combine RAG context with Azure response
                                    combined_response = self.combine_responses(
                                        rag_context, 
                                        azure_response.get('response', ''), 
                                        sources
                                    )
                                    
                                    # Add bot response to history
                                    st.session_state.chat_history.append({
                                        'role': 'assistant',
                                        'content': combined_response,
                                        'sources': sources,
                                        'is_enhanced': True,
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    
                                    # Clear input and rerun
                                    st.rerun()
                                else:
                                    st.error("Failed to get Azure enhanced response. Please try again.")
                            else:
                                st.error("Failed to retrieve medical context. Please try again.")
                        except Exception as e:
                            st.error(f"Error processing message: {str(e)}")
                            st.write("Error details:", e)
            
            with col2:
                # Empty column for wider chat area
                pass
            
            # Footer
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; color: #666; padding: 1rem;">
                <p>🏥 MedBot - Your AI Healthcare Assistant | Powered by Advanced AI & Medical Knowledge</p>
                <p>⚠️ This is for educational purposes only. Always consult healthcare professionals for medical advice.</p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"An error occurred in the main application: {str(e)}")
            st.write("Error details:", e)
            st.write("Please try refreshing the page or contact support.")

def main():
    """Main application entry point"""
    # Initialize MedBot
    medbot = MedBotStreamlit()
    
    # Run the application
    medbot.run()

if __name__ == "__main__":
    main()
