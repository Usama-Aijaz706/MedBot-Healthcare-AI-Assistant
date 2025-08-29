import streamlit as st
import json
import time
from datetime import datetime
import re
from typing import Dict, List, Optional, Tuple
import random
import requests
import os
from dotenv import load_dotenv
import markdown  # Add markdown library for proper conversion

# Import article fetching system
from article_fetching_system import render_article_fetching_interface, get_article_fetching_button, reset_article_state

# Load environment variables
load_dotenv()

# Get endpoint URLs from environment
AZURE_ENDPOINT_URL = os.getenv('ENDPOINT_URL', 'http://localhost:8000')
BACKEND_URL = "http://localhost:8000"  # Frontend always calls local backend

# Page Configuration
st.set_page_config(
    page_title="MedBot AI - Advanced Healthcare Assistant",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Advanced CSS with modern glassmorphism design
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-attachment: fixed;
    }
    /* Header */
    .main-header {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 2.5rem; border-radius: 20px; margin-bottom: 2rem; color: white; text-align: center;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    }
    .main-header h1 { margin: 0; font-size: 3rem; font-weight: 700; color: white; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);}    
    .main-header p { margin: 1rem 0 0 0; font-size: 1.2rem; opacity: 0.9; font-weight: 300; }

    /* Chat container */
    .chat-container { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px; padding: 2rem; margin: 1rem 0; min-height: 600px; max-height: 800px; overflow-y: auto; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    }

    .user-message { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 25px 25px 8px 25px; margin: 1rem 0 1rem auto; max-width: 75%; box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3); position: relative; word-wrap: break-word; }
    .user-message::before { content: "👤"; position: absolute; top: -10px; right: 20px; font-size: 1.2rem; background: white; padding: 5px; border-radius: 50%; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }

    .bot-message { background: rgba(255, 255, 255, 0.95) !important; backdrop-filter: blur(10px); padding: 2rem; border-radius: 25px 25px 25px 8px; margin: 1rem auto 1rem 0; max-width: 95%; width: 95%; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1); border: 1px solid rgba(255, 255, 255, 0.3); position: relative; color: #2d3748; overflow: hidden; }
    .bot-message::before { content: "⚕️"; position: absolute; top: 4px; left: 4px; font-size: 1.2rem; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 8px; border-radius: 50%; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); z-index: 10; }

    /* Headings styled as cards */
    .bot-message h1, .bot-message h2, .bot-message h3, .bot-message h4 { position: relative; border-radius: 12px; border-left: 5px solid #667eea; padding: 1rem 1.25rem; box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15); backdrop-filter: blur(8px); margin: 1.5rem 0 0.8rem 0; }
    .bot-message h1 { font-size: 1.6rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(102, 126, 234, 0.08), rgba(102, 126, 234, 0.03)); color: #2b6cb0; }
    .bot-message h2 { font-size: 1.4rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.12), rgba(102, 126, 234, 0.06)); color: #2b6cb0; }
    .bot-message h3 { font-size: 1.2rem; background: linear-gradient(135deg, rgba(56, 178, 172, 0.15), rgba(56, 178, 172, 0.08)); color: #3182ce; border-left-color: #38b2ac; }
    .bot-message h4 { font-size: 1.05rem; background: linear-gradient(135deg, rgba(14, 165, 233, 0.15), rgba(14, 165, 233, 0.08)); color: #2c5aa0; border-left-color: #0ea5e9; }

    .bot-message p { color: #4a5568; line-height: 1.8; margin: 1rem 0; font-size: 1rem; text-align: justify; }

    /* Lists */
    .bot-message ul, .bot-message ol { margin: 1.2rem 0; padding-left: 0; list-style: none; }
    .bot-message li { margin: 0.8rem 0; padding: 0.8rem 1.2rem; background: rgba(102, 126, 234, 0.05); border-radius: 10px; border-left: 3px solid #667eea; line-height: 1.6; position: relative; font-size: 0.95rem; }

    /* Enhanced table styling for medical content with better spacing and typography */
    .bot-message table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 2.5rem 0;
        background: rgba(255, 255, 255, 0.98);
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.18);
        border: 2px solid rgba(102, 126, 234, 0.12);
        font-family: 'Inter', sans-serif;
    }
    
    .bot-message th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem 1.8rem;
        text-align: left;
        font-weight: 700;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        border-bottom: 3px solid rgba(255, 255, 255, 0.25);
        position: relative;
        font-family: 'Inter', sans-serif;
    }
    
    .bot-message th:first-child {
        border-top-left-radius: 18px;
    }
    
    .bot-message th:last-child {
        border-top-right-radius: 18px;
    }
    
    .bot-message td {
        padding: 1.4rem 1.8rem;
        border-bottom: 1px solid rgba(102, 126, 234, 0.1);
        color: #2d3748;
        line-height: 1.7;
        font-size: 1rem;
        vertical-align: top;
        font-family: 'Inter', sans-serif;
    }
    
    .bot-message tr:last-child td:first-child {
        border-bottom-left-radius: 18px;
    }
    
    .bot-message tr:last-child td:last-child {
        border-bottom-right-radius: 18px;
    }
    
    .bot-message tr:nth-child(even) {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.04), rgba(102, 126, 234, 0.02));
    }
    
    .bot-message tr:hover {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(102, 126, 234, 0.06));
        transform: translateY(-2px);
        transition: all 0.3s ease;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
    }
    
    .bot-message tr:hover td {
        color: #1a202c;
        font-weight: 500;
    }
    
    /* Special styling for medical comparison tables */
    .bot-message table.comparison-table th {
        background: linear-gradient(135deg, #38b2ac 0%, #319795 100%);
    }
    
    /* Special styling for symptoms tables */
    .bot-message table.symptoms-table th {
        background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
    }
    
    /* Special styling for treatment tables */
    .bot-message table.treatment-table th {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
    }
    
    /* Table caption styling */
    .bot-message table::before {
        content: "📊 Medical Information Table";
        display: block;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(102, 126, 234, 0.05));
        padding: 1rem 1.8rem;
        font-weight: 600;
        color: #2b6cb0;
        font-size: 1rem;
        border-bottom: 1px solid rgba(102, 126, 234, 0.1);
        text-align: center;
        letter-spacing: 0.5px;
    }
    
    /* Force table styling to override any default Streamlit styles */
    .bot-message table,
    .bot-message table * {
        border: none !important;
        background: inherit !important;
    }
    
    .bot-message table th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-bottom: 3px solid rgba(255, 255, 255, 0.25) !important;
    }
    
    .bot-message table td {
        border: none !important;
        border-bottom: 1px solid rgba(102, 126, 234, 0.1) !important;
        background: transparent !important;
    }
    
    /* Override any Streamlit default table styles */
    .stMarkdown table,
    .stMarkdown table * {
        all: unset !important;
    }
    
    .stMarkdown table {
        display: table !important;
        width: 100% !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
    }
    
    .stMarkdown table th,
    .stMarkdown table td {
        display: table-cell !important;
        padding: 1.4rem 1.8rem !important;
        text-align: left !important;
        vertical-align: top !important;
    }

    .sidebar-card { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 15px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 4px 15px rgba(31, 38, 135, 0.2); }

    .thinking-indicator { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 15px; padding: 2rem; margin: 2rem 0; text-align: center; color: #4a5568; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 0.8; } 50% { opacity: 1; } 100% { opacity: 0.8; } }

    .chat-container::-webkit-scrollbar { width: 8px; }
    .chat-container::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
    .chat-container::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.3); border-radius: 10px; }
    .chat-container::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.5); }

    @media (max-width: 768px) {
        .user-message, .bot-message { max-width: 95%; }
        .main-header h1 { font-size: 2rem; }
        .bot-message { padding: 1.5rem; }
    }

    .click-hint {
        text-align: center;
        margin-top: 15px;
        font-style: italic;
        opacity: 0.7;
    }
    
    /* Fixed bottom chat interface */
    .fixed-bottom-chat {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-top: 2px solid rgba(102, 126, 234, 0.2);
        padding: 1.5rem;
        z-index: 1000;
        box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .chat-input-container {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        gap: 1rem;
        align-items: center;
    }
    
    .chat-input-field {
        flex: 1;
        background: white;
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 25px;
        padding: 1rem 1.5rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .chat-input-field:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .chat-send-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 1rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        white-space: nowrap;
    }
    
    .chat-send-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
         /* Chat content area with bottom padding for fixed input */
     .chat-content-area {
         padding-bottom: 50px;
         min-height: calc(100vh - 10px);
     }
    
    /* Article fetching interface styles */
    .article-interface {
        padding: 2rem;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .mode-selector {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 2rem;
    }
    
    .search-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
    }
    
    .results-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
    }
    
    /* Form styling for the fixed bottom input */
    .stForm {
        margin-bottom: 0 !important;
    }
    
    .stForm > div {
        margin-bottom: 0 !important;
    }
    
    /* Ensure the form doesn't interfere with the fixed positioning */
    form[data-testid="stForm"] {
        margin-bottom: 0 !important;
    }
    
    /* Fixed bottom form styling */
    .fixed-bottom-form {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-top: 2px solid rgba(102, 126, 234, 0.2) !important;
        padding: 1.5rem !important;
        z-index: 1000 !important;
        box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Style the text input within the fixed form */
    .fixed-bottom-form .stTextInput > div > div > input {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9)) !important;
        border: 2px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 25px !important;
        padding: 1rem 1.5rem !important;
        font-size: 1rem !important;
        color: #333 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .fixed-bottom-form .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15), 0 8px 25px rgba(102, 126, 234, 0.2) !important;
        transform: translateY(-2px) !important;
        background: linear-gradient(135deg, rgba(255, 255, 255, 1), rgba(255, 255, 255, 0.95)) !important;
    }
    
    .fixed-bottom-form .stTextInput > div > div > input::placeholder {
        color: #667eea !important;
        opacity: 0.7 !important;
        font-style: italic !important;
    }
    
    /* Style the search button within the fixed form */
    .fixed-bottom-form .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 1rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        white-space: nowrap !important;
        width: 100% !important;
        height: auto !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .fixed-bottom-form .stButton > button::before {
        content: '🔍' !important;
        position: absolute !important;
        left: 1rem !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        font-size: 1rem !important;
        opacity: 0.9 !important;
        transition: all 0.3s ease !important;
    }
    
    .fixed-bottom-form .stButton > button::after {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
        transition: left 0.5s !important;
    }
    
    .fixed-bottom-form .stButton > button:hover::before {
        transform: translateY(-50%) rotate(-10deg) scale(1.1) !important;
    }
    
    .fixed-bottom-form .stButton > button:hover::after {
        left: 100% !important;
    }
    
    .fixed-bottom-form .stButton > button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4) !important;
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
    }
    
    .fixed-bottom-form .stButton > button:active {
        transform: translateY(-1px) scale(0.98) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Style the Articles button within the fixed form */
    .fixed-bottom-form .stButton > button:last-of-type {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 50%, #2f855a 100%) !important;
        border: 2px solid rgba(72, 187, 120, 0.3) !important;
        box-shadow: 0 8px 25px rgba(72, 187, 120, 0.3) !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .fixed-bottom-form .stButton > button:last-of-type::before {
        content: '📚' !important;
        position: absolute !important;
        left: 0.8rem !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        font-size: 1rem !important;
        opacity: 0.9 !important;
        transition: all 0.3s ease !important;
    }
    
    .fixed-bottom-form .stButton > button:last-of-type::after {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
        transition: left 0.5s !important;
    }
    
    .fixed-bottom-form .stButton > button:last-of-type:hover::before {
        transform: translateY(-50%) rotate(10deg) scale(1.1) !important;
    }
    
    .fixed-bottom-form .stButton > button:last-of-type:hover::after {
        left: 100% !important;
    }
    
    .fixed-bottom-form .stButton > button:last-of-type:hover {
        background: linear-gradient(135deg, #38a169 0%, #2f855a 50%, #48bb78 100%) !important;
        box-shadow: 0 15px 35px rgba(72, 187, 120, 0.4) !important;
        transform: translateY(-3px) scale(1.02) !important;
    }
    
    .fixed-bottom-form .stButton > button:last-of-type:active {
        transform: translateY(-1px) scale(0.98) !important;
        box-shadow: 0 8px 25px rgba(72, 187, 120, 0.3) !important;
    }
    
    /* Enhanced button styling for professional and creative look */
    .enhanced-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 1rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        white-space: nowrap !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .enhanced-button::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
        transition: left 0.5s !important;
    }
    
    .enhanced-button:hover::before {
        left: 100% !important;
    }
    
    .enhanced-button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4) !important;
        background: linear-gradient(135deg, #764ba2 0%, #f093fb 50%, #667eea 100%) !important;
    }
    
    .enhanced-button:active {
        transform: translateY(-1px) scale(0.98) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Articles button specific styling */
    .articles-button {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 50%, #2f855a 100%) !important;
        border: 2px solid rgba(72, 187, 120, 0.3) !important;
        box-shadow: 0 8px 25px rgba(72, 187, 120, 0.3) !important;
        font-size: 1.1rem !important;
        padding: 1.2rem 2.5rem !important;
        border-radius: 30px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .articles-button::after {
        content: '📚' !important;
        position: absolute !important;
        right: 1.5rem !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        font-size: 1.2rem !important;
        opacity: 0.9 !important;
        transition: all 0.3s ease !important;
    }
    
    .articles-button:hover {
        background: linear-gradient(135deg, #38a169 0%, #2f855a 50%, #48bb78 100%) !important;
        box-shadow: 0 15px 35px rgba(72, 187, 120, 0.4) !important;
        transform: translateY(-3px) scale(1.02) !important;
    }
    
    .articles-button:hover::after {
        transform: translateY(-50%) rotate(10deg) scale(1.1) !important;
    }
    
    /* Style the Articles button in the sidebar */
    [data-testid="stButton"] button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 50%, #2f855a 100%) !important;
        color: white !important;
        border: 2px solid rgba(72, 187, 120, 0.3) !important;
        border-radius: 30px !important;
        padding: 1.2rem 2.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 8px 25px rgba(72, 187, 120, 0.3) !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover {
        background: linear-gradient(135deg, #38a169 0%, #2f855a 50%, #48bb78 100%) !important;
        box-shadow: 0 15px 35px rgba(72, 187, 120, 0.4) !important;
        transform: translateY(-3px) scale(1.02) !important;
    }
    
    [data-testid="stButton"] button[data-testid="baseButton-secondary"]:active {
        transform: translateY(-1px) scale(0.98) !important;
        box-shadow: 0 8px 25px rgba(72, 187, 120, 0.3) !important;
    }
    
    /* Enhanced search button styling */
    .enhanced-search-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 1rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        white-space: nowrap !important;
        width: 100% !important;
        height: auto !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .enhanced-search-button::before {
        content: '🔍' !important;
        position: absolute !important;
        left: 1rem !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        font-size: 1rem !important;
        opacity: 0.9 !important;
        transition: all 0.3s ease !important;
    }
    
    .enhanced-search-button::after {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
        transition: left 0.5s !important;
    }
    
    .enhanced-search-button:hover::before {
        transform: translateY(-50%) rotate(-10deg) scale(1.1) !important;
    }
    
    .enhanced-search-button:hover::after {
        left: 100% !important;
    }
    
    .enhanced-search-button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4) !important;
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
    }
    
    .enhanced-search-button:active {
        transform: translateY(-1px) scale(0.98) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Enhanced text input styling */
    .enhanced-text-input {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9)) !important;
        border: 2px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 25px !important;
        padding: 1rem 1.5rem !important;
        font-size: 1rem !important;
        color: #333 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .enhanced-text-input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15), 0 8px 25px rgba(102, 126, 234, 0.2) !important;
        transform: translateY(-2px) !important;
        background: linear-gradient(135deg, rgba(255, 255, 255, 1), rgba(255, 255, 255, 0.95)) !important;
    }
    
    .enhanced-text-input::placeholder {
        color: #667eea !important;
        opacity: 0.7 !important;
        font-style: italic !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


class RAGIntegratedMedBotAI:
    """Advanced Medical AI Response System integrated with RAG backend"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.initialize_session()
    
    def initialize_session(self):
        """Initialize advanced session management"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'user_profile' not in st.session_state:
            st.session_state.user_profile = {
                'name': None,
                'preferred_detail_level': 'comprehensive',
                'interaction_count': 0,
                'topics_discussed': []
            }
        
        if 'response_metrics' not in st.session_state:
            st.session_state.response_metrics = {
                'total_responses': 0,
                'avg_response_time': 0,
                'response_times': []
            }
            
        if 'article_search_query' not in st.session_state:
            st.session_state.article_search_query = ""
            
        if 'show_articles' not in st.session_state:
            st.session_state.show_articles = False
    
    def extract_user_information(self, message: str) -> Optional[str]:
        """Advanced user name extraction with multiple patterns"""
        patterns = [
            r"\bi am (\w+)\b",
            r"\bmy name is (\w+)\b",
            r"\bi'm (\w+)\b",
            r"\bcall me (\w+)\b",
            r"\bthis is (\w+)\b",
            r"\b(\w+) here\b",
            r"\bhello, i'm (\w+)\b"
        ]
        message_lower = message.lower()
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                name = match.group(1).capitalize()
                if len(name) > 2 and name.isalpha():
                    return name
        return None
    
    def query_rag_backend(self, user_question: str) -> Optional[Dict]:
        """Query the RAG backend for medical information"""
        try:
            payload = {"user_question": user_question, "chat_history": st.session_state.messages}
            response = requests.post(f"{self.backend_url}/chat", json=payload, timeout=60)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Backend error: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
            return None

    def clean_response(self, response: str) -> str:
        """Clean response by removing unwanted HTML tags and fixing markdown pitfalls"""
        # Remove HTML tags
        response = re.sub(r'</?div[^>]*>', '', response or '')
        response = re.sub(r'<[^>]+>', '', response)
        # Fix headings like "## **Title**" -> "## Title"
        response = re.sub(r'(#{1,6})\s*\*\*(.*?)\*\*', r'\1 \2', response)
        # Normalize multiple blank lines
        response = re.sub(r'\n\s*\n\s*\n+', '\n\n', response)
        return response.strip()

    # -------------------- TABLE UTILITIES -------------------- #
    def ensure_table_formatting(self, response: str, original_query: str) -> str:
        """Detect malformed markdown tables and repair them. If the user asked for a table but none exists, try to synthesize one from bullet-like lines."""
        if not response:
            return response

        has_pipe = '|' in response
        has_dash = '---' in response
        asked_for_table = 'table' in (original_query or '').lower()

        # If a likely table exists, try to repair all tables found
        if has_pipe:
            response = self._repair_all_tables(response)
            return response

        # If no table present but user asked for one, try to build a simple one from list-like lines
        if asked_for_table:
            synthetic = self._synthesize_table_from_lists(response)
            if synthetic:
                return synthetic
        return response
    
    def _repair_all_tables(self, text: str) -> str:
        """Repair all tables in the text by normalizing concatenated rows and fixing structure"""
        import re
        
        # Step 1 — convert cases where rows were concatenated with adjacent pipes (e.g. "... | |---|..." or "... | | row | ...")
        # This inserts a newline where there are consecutive pipe boundaries used as row separators.
        text = re.sub(r'\|\s*\|\s*', '|\n|', text)

        # Step 2 — split into lines and process contiguous '|' blocks as table blocks
        lines = text.splitlines()
        output_lines = []
        block = []

        def flush_block():
            nonlocal output_lines, block
            if block:
                output_lines.extend(self._repair_table_block(block))
                block = []

        for ln in lines:
            if ln.strip().startswith('|'):
                block.append(ln)
            else:
                flush_block()
                output_lines.append(ln)
        flush_block()
        return '\n'.join(output_lines)

    def _repair_table_block(self, block_lines: list) -> list:
        """Repair a single table block by normalizing structure and removing phantom columns"""
        import re
        
        # Convert each pipe-line to a list of cell strings
        cleaned = []
        for raw in block_lines:
            ln = raw.strip()
            if not ln.startswith('|'):
                ln = '| ' + ln
            if not ln.endswith('|'):
                ln = ln + ' |'
            # split on pipes, ignore pure-empty tokens caused by leading/trailing pipes
            parts = [p.strip() for p in ln.strip('|').split('|')]
            cleaned.append(parts)

        if not cleaned:
            return block_lines

        # Find separator row (all dashes / alignment style); if not present, assume first row is header
        sep_row_idx = None
        for i, row in enumerate(cleaned):
            if all(re.fullmatch(r'[:\- ]+', cell) and '-' in cell for cell in row):
                sep_row_idx = i
                break

        if sep_row_idx is not None:
            header = cleaned[0]
            data_rows = cleaned[sep_row_idx + 1:]
        else:
            header = cleaned[0]
            data_rows = cleaned[1:]

        # Normalize column count to header width
        num_cols = len(header)
        normalized = []
        for r in data_rows:
            r = (r + [''] * num_cols)[:num_cols]
            normalized.append(r)

        # Drop trailing columns that are empty across all rows + header (removes phantom columns)
        while num_cols > 0 and all(((row[num_cols - 1].strip() == '') for row in ([header] + normalized))):
            for row in normalized:
                row.pop()
            header.pop()
            num_cols -= 1

        if num_cols == 0:
            # nothing meaningful — return original block as fallback
            return block_lines

        # Build canonical markdown table lines
        def row_to_md(row: list) -> str:
            safe = [str(c).replace('|', '\\|') for c in row]
            return '| ' + ' | '.join(safe) + ' |'

        md_lines = [row_to_md(header), '|' + '|'.join(['---'] * num_cols) + '|']
        for r in normalized:
            md_lines.append(row_to_md(r))

        return md_lines

    def _synthesize_table_from_lists(self, text: str) -> str:
        """Very simple heuristic: turn bullet-like lines into a one-column table if nothing else is tabular."""
        items = [m.group(1).strip() for m in re.finditer(r'^[\-\*]\s+(.*)$', text, flags=re.MULTILINE)]
        if not items:
            return ''
        header = ['Item']
        rows = [[it] for it in items]
        return self.build_markdown_table(header, rows)

    def build_markdown_table(self, headers: List[str], data: List[List[str]]) -> str:
        if not headers or not data:
            return ''
        table = '| ' + ' | '.join(headers) + ' |\n'
        table += '|' + '|'.join(['---'] * len(headers)) + '|\n'
        for row in data:
            row = (row + [''] * (len(headers) - len(row)))[:len(headers)]
            safe = [str(c).strip().replace('\n', ' ').replace('|', '\\|') for c in row]
            table += '| ' + ' | '.join(safe) + ' |\n'
        return table
    
    def test_table_repair(self):
        """Test function to verify table repair is working correctly"""
        # Test case: the broken thyroid table from your example
        broken_table = """| Type                     | Description                                                   | Symptoms                                                                                                   | Medications/Injections                                                            |
|--------------------------|---------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| Hypothyroidism           | Underactive thyroid; insufficient hormone production          | Fatigue, weight gain, cold intolerance, dry skin, depression                                               | Levothyroxine (Synthroid), Liothyronine (Cytomel)                                 |
| Hyperthyroidism          | Overactive thyroid; excessive hormone production              | Weight loss, rapid heartbeat, sweating, anxiety, tremors                                                   | Methimazole (Tapazole), Propylthiouracil (PTU), Beta-blockers (e.g., propranolol) |
| Goiter                   | Enlargement of the thyroid gland                              | Visible neck swelling, difficulty swallowing, breathing issues                                             | Iodine supplements (if deficient), thyroid hormone replacement, surgery (if severe) |
| Thyroid Nodules          | Growths or lumps in the thyroid gland                         | Often asymptomatic; may cause hyper- or hypothyroidism if large                                            | Fine-needle aspiration for diagnosis, radioactive iodine, surgery (if malignant)  |
| Thyroid Cancer           | Malignant growth in the thyroid gland                         | Neck lump, difficulty swallowing, hoarseness, swollen lymph nodes                                          | Surgery (thyroidectomy), radioactive iodine, chemotherapy, thyroid hormone therapy|
| Hashimoto's Thyroiditis  | Autoimmune condition leading to hypothyroidism                | Fatigue, weight gain, cold intolerance, goiter                                                              | Levothyroxine, monitoring for complications                                       |
| Graves' Disease          | Autoimmune condition causing hyperthyroidism                  | Bulging eyes, weight loss, rapid heartbeat, irritability                                                   | Methimazole, radioactive iodine therapy, beta-blockers                           |"""
        
        # Test the repair
        repaired = self._repair_all_tables(broken_table)
        return repaired
    


    # -------------------- PIPELINE -------------------- #
    def process_user_input(self, user_input: str) -> str:
        start_time = time.time()
        
        # Extract user name if provided
        name = self.extract_user_information(user_input)
        if name:
            st.session_state.user_profile['name'] = name
        
        st.session_state.user_profile['interaction_count'] += 1
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        rag_response = self.query_rag_backend(user_input)
        if rag_response and 'response' in rag_response:
            response = rag_response['response']
            response = self.clean_response(response)
            response = self.ensure_table_formatting(response, user_input)
            response += self.get_medical_disclaimer()
        else:
            response = self.generate_fallback_response(user_input)
        
        # Metrics
        response_time = time.time() - start_time
        st.session_state.response_metrics['total_responses'] += 1
        st.session_state.response_metrics['response_times'].append(response_time)
        st.session_state.response_metrics['avg_response_time'] = sum(st.session_state.response_metrics['response_times']) / len(st.session_state.response_metrics['response_times'])
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        return response
    
    def get_medical_disclaimer(self) -> str:
        return """

---

## ⚠️ Medical Disclaimer

**This information is for educational purposes only and should not replace professional medical advice. Always consult qualified healthcare providers for medical concerns.**

---
"""
    
    def generate_fallback_response(self, user_input: str) -> str:
        return f"""
        I apologize, but I'm currently unable to access my medical knowledge base. However, I can provide general information about common health topics.
        
        **Your question was:** {user_input}
        
        **Please try:**
        1. Refreshing the page
        2. Checking if the backend service is running
        3. Asking a different medical question
        
        For immediate medical concerns, please consult a healthcare professional.
        """


# -------------------- MAIN APP -------------------- #

def render_chat_interface(ai_system):
     """Render the main chat interface with fixed bottom input."""
     # Welcome card for fresh sessions
     if not st.session_state.messages:
         st.markdown(
             """
             <div class="bot-message">
                 <h2>Welcome to MedBot AI! 🏥</h2>
                 <p>I'm your advanced healthcare assistant powered by Retrieval-Augmented Generation (RAG). Ask about conditions, medications, treatments, anatomy, procedures, and wellness.</p>
             </div>
             """,
             unsafe_allow_html=True,
         )
 
     # Chat content area with bottom padding
     with st.container():
         st.markdown('<div class="chat-content-area">', unsafe_allow_html=True)
         
         # Chat transcript
         for message in st.session_state.messages:
             if message["role"] == "user":
                 st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
             else:
                 html_content = markdown.markdown(message["content"])  # render markdown to HTML first
                 st.markdown(f"<div class='bot-message'>{html_content}</div>", unsafe_allow_html=True)
         
         st.markdown('</div>', unsafe_allow_html=True)
     
     # Add bottom padding to make room for the fixed input
     st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
     
     # Fixed bottom chat input - now using actual Streamlit components
     with st.container():
         # Create a container that will be positioned at the bottom
         st.markdown("""
         <div class="fixed-bottom-form">
         """, unsafe_allow_html=True)
         
         # The actual functional form inside the fixed container
         with st.form("user_input_form", clear_on_submit=True):
             col1, col2, col3 = st.columns([3, 1, 1])
             with col1:
                 user_input = st.text_input(
                     "Ask me anything about healthcare and medicine:",
                     placeholder="e.g., Tell me about microbiology and its importance, explain in detail with tables",
                     key="user_input",
                     label_visibility="collapsed"  # Hide the label to make it look cleaner
                 )
             with col2:
                 submitted = st.form_submit_button("🔍 Search", use_container_width=True)
             with col3:
                 articles_clicked = st.form_submit_button("📚 Articles", use_container_width=True)
         
         st.markdown("</div>", unsafe_allow_html=True)
         
         # Process the form submission
         if submitted and user_input.strip():
             with st.spinner("🤔 Analyzing your medical question with the RAG system..."):
                 ai_system.process_user_input(user_input.strip())
                 st.rerun()
         
         # Process the Articles button click
         if articles_clicked:
             # Store the user's current input for article search
             if user_input.strip():
                 st.session_state.article_search_query = user_input.strip()
                 st.session_state.show_articles = True
                 st.rerun()
             else:
                 st.warning("⚠️ Please enter a healthcare-related query first, then click Articles.")


def main():
    ai_system = RAGIntegratedMedBotAI()

    st.markdown(
        """
    <div class="main-header">
        <h1>MedBot AI</h1>
        <p>Advanced Healthcare Assistant with RAG-Enhanced Medical Knowledge</p>
    </div>
        """,
        unsafe_allow_html=True,
    )
    
    with st.sidebar:
        st.markdown(
            """
        <div class="sidebar-card">
            <h3>🔍 Medical Topics</h3>
            <p>Ask about:</p>
            <ul>
                <li>Any medical condition or disease</li>
                <li>Medications and treatments</li>
                <li>Anatomy and physiology</li>
                <li>Medical procedures</li>
                <li>Health and wellness</li>
            </ul>
        </div>
            """,
            unsafe_allow_html=True,
        )
        
        if st.session_state.user_profile['name']:
            st.markdown(
                f"""
                <div class=\"sidebar-card\">
                <h3>👤 User Profile</h3>
                <p><strong>Name:</strong> {st.session_state.user_profile['name']}</p>
                <p><strong>Interactions:</strong> {st.session_state.user_profile['interaction_count']}</p>
            </div>
                """,
                unsafe_allow_html=True,
            )
        
        if st.session_state.response_metrics['total_responses'] > 0:
                    st.markdown(
            f"""
            <div class="sidebar-card">
                <h3>📊 System Metrics</h3>
                <p><strong>Total Responses:</strong> {st.session_state.response_metrics['total_responses']}</p>
                <p><strong>Avg Response Time:</strong> {st.session_state.response_metrics['avg_response_time']:.2f}s</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Backend status
        try:
            response = requests.get(f"{ai_system.backend_url}/health", timeout=15)
            if response.status_code == 200:
                st.markdown(
                    """
                    <div class="sidebar-card" style="border-left: 4px solid #48bb78;">
                        <h3>🟢 Backend Status</h3>
                        <p><strong>RAG System:</strong> Connected</p>
                        <p><strong>Knowledge Base:</strong> Active</p>
                        <p><strong>Azure Endpoint:</strong> Configured</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="sidebar-card" style="border-left: 4px solid #f56565;">
                        <h3>🔴 Backend Status</h3>
                        <p><strong>RAG System:</strong> Error</p>
                        <p><strong>Status Code:</strong> {response.status_code}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        except Exception:
            st.markdown(
                """
                <div class="sidebar-card" style="border-left: 4px solid #f56565;">
                    <h3>🔴 Backend Status</h3>
                    <p><strong>RAG System:</strong> Disconnected</p>
                    <p><strong>Please start the backend:</strong></p>
                    <code>python main.py</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div class="sidebar-card" style="border-left: 4px solid #3182ce;">
                <h3>🔧 System Info</h3>
                <p><strong>Backend URL:</strong> {BACKEND_URL}</p>
                <p><strong>Azure Endpoint:</strong> Configured</p>
                <p><strong>Environment:</strong> Loaded</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Table repair test button
        if st.button("🧪 Test Table Repair"):
            test_result = ai_system.test_table_repair()
            st.markdown("**Table Repair Test Result:**")
            st.code(test_result, language="markdown")
         
        # Article fetching button - REMOVED FROM SIDEBAR

    # Main interface - switch between chat and article fetching
    if st.session_state.get('show_articles', False):
        # Article fetching interface
        render_article_fetching_interface()
        
        # Back to chat button
        if st.button("💬 Back to Chat", use_container_width=True, type="primary"):
            st.session_state.show_articles = False
            reset_article_state()
            st.rerun()
    else:
        # Regular chat interface
        render_chat_interface(ai_system)
    
    # Global disclaimer footer
    st.markdown(
        """
        <div class="sidebar-card" style="border-left: 4px solid #fc8181; background: linear-gradient(135deg, #fed7d7, #feb2b2); color:#7b341e">
            <strong>⚠️ Medical Disclaimer:</strong> This AI assistant provides educational information only and should not replace professional medical advice. Always consult qualified healthcare providers for medical concerns.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
