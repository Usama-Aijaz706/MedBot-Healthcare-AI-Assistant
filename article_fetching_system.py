import os
import streamlit as st
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
import json
from datetime import datetime
from pathlib import Path

# Load environment variables
load_dotenv()

# -----------------------------
# CONFIGURATION
# -----------------------------
GROQ_API_KEY = os.getenv("PMID")  # Using the same key as pmid.py
EUROPE_PMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
HEADERS = {"User-Agent": "MedBot-ArticleFetcher (medbot@example.com)"}

# -----------------------------
# Groq API Enhancement
# -----------------------------
def enhance_query_with_groq(user_query: str) -> str:
    """
    Use Groq API to enhance and clarify user queries for better article search.
    """
    try:
        if not GROQ_API_KEY:
            st.warning("⚠️ Groq API key not found. Using original query.")
            return user_query
        
        from openai import OpenAI
        
        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        
        # Create enhancement prompt
        enhancement_prompt = f"""You are a medical research specialist. A user has asked for articles about: "{user_query}"

Your task is to:
1. Analyze what they're actually looking for
2. Enhance their query with proper medical terminology
3. Make it searchable for Europe PMC (NOT PubMed MeSH syntax)
4. Keep it concise but comprehensive
5. Use simple keywords, NOT MeSH syntax like [MeSH] or [Subheading]

Return ONLY the enhanced search query, no explanations or extra text.

Examples:
- "cancer" → "cancer research treatment"
- "heart problems" → "cardiovascular disease diagnosis treatment"
- "diabetes management" → "diabetes mellitus management guidelines"
- "myocardial infarction diagnosis" → "myocardial infarction diagnosis treatment outcomes"

IMPORTANT: Do NOT use MeSH syntax. Use simple medical keywords only.

Enhanced query:"""

        # Call Groq API
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a medical research specialist. Provide only enhanced search queries."},
                {"role": "user", "content": enhancement_prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        enhanced_query = response.choices[0].message.content.strip()
        
        if enhanced_query and len(enhanced_query) > 5:
            st.success(f"🔍 Enhanced query: **{enhanced_query}**")
            return enhanced_query
        else:
            st.warning("⚠️ Query enhancement failed. Using original query.")
            return user_query
            
    except Exception as e:
        st.error(f"❌ Query enhancement failed: {str(e)}")
        return user_query

# -----------------------------
# Europe PMC Article Search
# -----------------------------
def search_articles(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search Europe PMC for articles matching the query.
    Returns articles with both PMID and PMCID.
    """
    try:
        from urllib.parse import quote
        
        # Clean the query - remove any MeSH syntax if present
        clean_query = query.replace("[MeSH]", "").replace("[Subheading]", "").replace("[All Fields]", "")
        clean_query = " ".join(clean_query.split())  # Remove extra spaces
        
        st.info(f"🔍 Searching with query: **{clean_query}**")
        
        # Search for articles
        search_url = f"{EUROPE_PMC_BASE}/search?query={quote(clean_query)}&format=json&pageSize={max_results * 3}"  # Get more to filter
        st.info(f"📡 Search URL: {search_url}")
        
        response = requests.get(search_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("resultList", {}).get("result", [])
        
        st.info(f"📊 Found {len(results)} total results from Europe PMC")
        
        # Filter articles with both PMID and PMCID
        valid_articles = []
        for article in results:
            pmid = article.get("pmid")
            pmcid = article.get("pmcid")
            
            if pmid and pmcid:  # Only include articles with both identifiers
                article_info = {
                    "pmid": pmid,
                    "pmcid": pmcid,
                    "title": article.get("title", "No title available"),
                    "authors": article.get("authorString", "Unknown authors"),
                    "journal": article.get("journalTitle", "Journal not available"),
                    "year": article.get("pubYear", "Year not available"),
                    "abstract": article.get("abstractText", "No abstract available"),
                    "doi": article.get("doi", ""),
                    "pmc_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/",
                    "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                }
                valid_articles.append(article_info)
                
                if len(valid_articles) >= max_results:
                    break
        
        st.info(f"✅ Found {len(valid_articles)} articles with both PMID and PMCID")
        return valid_articles
        
    except Exception as e:
        st.error(f"❌ Article search failed: {str(e)}")
        st.error(f"🔍 Query used: {query}")
        st.error(f"📡 URL attempted: {EUROPE_PMC_BASE}/search?query={quote(query)}&format=json&pageSize={max_results * 3}")
        
        # Try fallback search with simplified query
        try:
            st.warning("🔄 Trying fallback search with simplified query...")
            fallback_query = " ".join([word for word in clean_query.split() if len(word) > 3])[:100]  # Remove short words and limit length
            st.info(f"🔄 Fallback query: **{fallback_query}**")
            
            fallback_url = f"{EUROPE_PMC_BASE}/search?query={quote(fallback_query)}&format=json&pageSize={max_results * 2}"
            fallback_response = requests.get(fallback_url, headers=HEADERS, timeout=30)
            fallback_response.raise_for_status()
            
            fallback_data = fallback_response.json()
            fallback_results = fallback_data.get("resultList", {}).get("result", [])
            
            st.info(f"📊 Fallback search found {len(fallback_results)} total results")
            
            # Filter fallback results
            fallback_articles = []
            for article in fallback_results:
                pmid = article.get("pmid")
                pmcid = article.get("pmcid")
                
                if pmid and pmcid:
                    article_info = {
                        "pmid": pmid,
                        "pmcid": pmcid,
                        "title": article.get("title", "No title available"),
                        "authors": article.get("authorString", "Unknown authors"),
                        "journal": article.get("journalTitle", "Journal not available"),
                        "year": article.get("pubYear", "Year not available"),
                        "abstract": article.get("abstractText", "No abstract available"),
                        "doi": article.get("doi", ""),
                        "pmc_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/",
                        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    }
                    fallback_articles.append(article_info)
                    
                    if len(fallback_articles) >= max_results:
                        break
            
            if fallback_articles:
                st.success(f"✅ Fallback search successful! Found {len(fallback_articles)} articles")
                return fallback_articles
            else:
                st.error("❌ Fallback search also failed")
                return []
                
        except Exception as fallback_error:
            st.error(f"❌ Fallback search failed: {str(fallback_error)}")
            return []

# -----------------------------
# Article Card Display
# -----------------------------
def display_article_cards(articles: List[Dict]) -> Optional[str]:
    """
    Display articles in beautiful, clickable cards.
    Returns the PMCID of the clicked article.
    """
    if not articles:
        st.warning("❌ No articles found matching your query.")
        return None
    
    st.success(f"✅ Found {len(articles)} articles with both PMID and PMCID")
    
    # Create columns for responsive layout
    cols = st.columns(2)
    
    clicked_pmcid = None
    
    for idx, article in enumerate(articles):
        col_idx = idx % 2
        col = cols[col_idx]
        
        with col:
            # Create a beautiful card
            with st.container():
                st.markdown("""
                <style>
                .article-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 15px;
                    padding: 20px;
                    margin: 10px 0;
                    color: white;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;
                    cursor: pointer;
                }
                .article-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
                }
                .article-title {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    line-height: 1.4;
                }
                .article-meta {
                    font-size: 14px;
                    opacity: 0.9;
                    margin: 8px 0;
                }
                .article-abstract {
                    font-size: 13px;
                    opacity: 0.8;
                    line-height: 1.5;
                    margin-top: 15px;
                }
                .click-hint {
                    text-align: center;
                    margin-top: 15px;
                    font-style: italic;
                    opacity: 0.7;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Create clickable card that directly fetches and opens the article
                if st.button(f"📄 Article {idx + 1}", key=f"article_{idx}", 
                           help="Click to fetch full article and open in browser"):
                    with st.spinner("🔄 Fetching article and opening in browser..."):
                        try:
                            # Fetch the full article content directly
                            from article_fetcher import fetch_article
                            article_dir = fetch_article(article["pmcid"])
                            
                            if article_dir:
                                st.success("✅ Article fetched successfully! Opening in browser...")
                                
                                # Convert to HTML and open in browser immediately
                                from simple_html_to_pdf import SimpleHTMLToPDFConverter
                                from pathlib import Path
                                converter = SimpleHTMLToPDFConverter()
                                
                                # Find the markdown file
                                article_path = Path(article_dir)
                                md_files = list(article_path.glob("*.md"))
                                
                                if md_files:
                                    md_file = md_files[0]
                                    html_file = converter.convert_markdown_to_pdf(md_file, f"article_{article['pmcid']}")
                                    
                                    if html_file:
                                        st.success("✅ Article opened in browser!")
                                        st.info("📖 You can now read the full article and use the DOWNLOAD PDF button to save it")
                                        
                                        # Set session state for the viewer
                                        st.session_state.selected_article = article
                                        st.session_state.article_mode = 'view'
                                        st.session_state.article_fetched = True
                                        st.session_state.article_dir = article_dir
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to open in browser")
                                else:
                                    st.error("❌ No markdown file found in article directory")
                            else:
                                st.error("❌ Failed to fetch article content")
                                
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            st.error("💡 Make sure you have the required libraries installed: pip install markdown weasyprint playwright")
                
                # Display article information
                st.markdown(f"""
                <div class="article-card">
                    <div class="article-title">{article['title']}</div>
                    <div class="article-meta"><strong>PMID:</strong> {article['pmid']}</div>
                    <div class="article-meta"><strong>PMCID:</strong> {article['pmcid']}</div>
                    <div class="article-meta"><strong>Authors:</strong> {article['authors']}</div>
                    <div class="article-meta"><strong>Journal:</strong> {article['journal']}</div>
                    <div class="article-meta"><strong>Year:</strong> {article['year']}</div>
                    <div class="article-abstract">{article['abstract'][:200]}...</div>
                    <div class="click-hint">Click the button above to fetch and open full article in browser</div>
                </div>
                """, unsafe_allow_html=True)
    
    return clicked_pmcid

# -----------------------------
# Article Fetching and PDF Conversion
# -----------------------------
def fetch_and_convert_article(pmcid: str) -> Optional[str]:
    """
    Fetch article using article_fetcher.py and convert to PDF using simple_html_to_pdf.py
    Returns the path to the generated PDF file.
    """
    try:
        # Import article fetcher
        from article_fetcher import fetch_article
        
        st.info(f"🔄 Fetching article content for PMCID: {pmcid}")
        
        # Fetch article content
        article_dir = fetch_article(pmcid)
        
        if not article_dir or not Path(article_dir).exists():
            st.error("❌ Failed to fetch article content")
            return None
        
        st.success("✅ Article content fetched successfully!")
        
        # Find the markdown file in the article directory
        md_files = list(Path(article_dir).glob("*.md"))
        if not md_files:
            st.error("❌ No markdown file found in article directory")
            return None
        
        md_file = md_files[0]
        st.info(f"📄 Found markdown file: {md_file.name}")
        
        # Import PDF converter
        from simple_html_to_pdf import SimpleHTMLToPDFConverter
        
        st.info("🔄 Converting to PDF...")
        
        # Convert to PDF using the converter class
        converter = SimpleHTMLToPDFConverter()
        pdf_path = converter.convert_markdown_to_pdf(md_file, f"article_{pmcid}")
        
        if pdf_path:
            st.success(f"✅ PDF generated successfully!")
            return pdf_path
        else:
            st.error("❌ PDF conversion failed")
            return None
            
    except Exception as e:
        st.error(f"❌ Error in article fetching/conversion: {str(e)}")
        return None

# -----------------------------
# Main Article Fetching Interface
# -----------------------------
def render_article_fetching_interface():
    """
    Main interface for article fetching functionality.
    """
    st.markdown("## 📚 Article Research & Fetching System")
    st.markdown("---")
    
    # Initialize session state
    if 'article_mode' not in st.session_state:
        st.session_state.article_mode = 'search'
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_article' not in st.session_state:
        st.session_state.selected_article = None
    
    # Check if we have a query from the chat interface
    chat_query = st.session_state.get('article_search_query', '')
    
    if chat_query and st.session_state.article_mode == 'search':
        # Auto-search with the chat query
        st.markdown(f"### 🔍 Searching for articles related to: **{chat_query}**")
        
        with st.spinner("🔍 Enhancing query and searching articles..."):
            # Enhance query with Groq
            enhanced_query = enhance_query_with_groq(chat_query.strip())
            st.info(f"**Enhanced query:** {enhanced_query}")
            
            # Search articles
            articles = search_articles(enhanced_query, max_results=10)
            
            if articles:
                st.session_state.search_results = articles
                st.session_state.article_mode = 'results'
                st.rerun()
            else:
                st.warning("❌ No articles found. Try a different query.")
    
    # Mode selection
    mode = st.radio(
        "Choose mode:",
        ["🔍 Search Articles", "📄 View Selected Article", "📱 Download PDF", "🧪 Test System"],
        key="article_mode_radio"
    )
    
    if mode == "🔍 Search Articles":
        render_search_interface()
    elif mode == "📄 View Selected Article":
        render_article_viewer()
    elif mode == "📱 Download PDF":
        render_pdf_downloader()
    elif mode == "🧪 Test System":
        test_article_system_integration()

def render_search_interface():
    """Render the article search interface."""
    st.markdown("### 🔍 Search for Medical Articles")
    
    # Check if we have a query from the chat interface
    chat_query = st.session_state.get('article_search_query', '')
    
    if chat_query:
        st.info(f"💬 **Query from chat:** {chat_query}")
        st.markdown("---")
    
    # Query input
    user_query = st.text_area(
        "Enter your research query:",
        value=chat_query,  # Pre-fill with chat query if available
        placeholder="e.g., lung cancer treatment, diabetes management, heart disease prevention...",
        height=100,
        key="article_query_input"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🚀 Search Articles", type="primary", use_container_width=True):
            if user_query.strip():
                with st.spinner("🔍 Enhancing query and searching articles..."):
                    # Enhance query with Groq
                    enhanced_query = enhance_query_with_groq(user_query.strip())
                    
                    # Search articles
                    articles = search_articles(enhanced_query, max_results=10)
                    
                    if articles:
                        st.session_state.search_results = articles
                        st.session_state.article_mode = 'results'
                        st.rerun()
                    else:
                        st.warning("❌ No articles found. Try a different query.")
            else:
                st.warning("⚠️ Please enter a search query.")
    
    with col2:
        if st.button("🔍 Direct Search", type="secondary", use_container_width=True):
            if user_query.strip():
                with st.spinner("🔍 Searching with original query..."):
                    # Search directly without enhancement
                    articles = search_articles(user_query.strip(), max_results=10)
                    
                    if articles:
                        st.session_state.search_results = articles
                        st.session_state.article_mode = 'results'
                        st.rerun()
                    else:
                        st.warning("❌ Direct search also failed. Try a different query.")
            else:
                st.warning("⚠️ Please enter a search query.")
    
    # Display search results if available
    if st.session_state.search_results:
        st.markdown("### 📋 Search Results")
        clicked_pmcid = display_article_cards(st.session_state.search_results)
        
        if clicked_pmcid:
            st.session_state.selected_pmcid = clicked_pmcid
            st.session_state.article_mode = 'view'
            st.rerun()

def render_article_viewer():
    """Render the article viewer interface."""
    st.markdown("### 📄 Article Viewer")
    
    if not st.session_state.selected_article:
        st.warning("⚠️ No article selected. Please search for articles first.")
        if st.button("🔍 Back to Search"):
            st.session_state.article_mode = 'search'
            st.rerun()
        return
    
    article = st.session_state.selected_article
    
    # Display article details
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 25px; border-radius: 15px; margin: 20px 0;">
        <h2>{article['title']}</h2>
        <p><strong>PMID:</strong> {article['pmid']} | <strong>PMCID:</strong> {article['pmcid']}</p>
        <p><strong>Authors:</strong> {article['authors']}</p>
        <p><strong>Journal:</strong> {article['journal']} ({article['year']})</p>
        <p><strong>DOI:</strong> {article['doi'] if article['doi'] else 'Not available'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Abstract
    st.markdown("### 📝 Abstract")
    st.markdown(article['abstract'])
    
    # Quick action - Open article directly in browser
    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    
    # Check if article is already fetched
    article_fetched = st.session_state.get('article_fetched', False)
    
    if not article_fetched:
        if st.button("🌐 Fetch & Open Article in Browser", type="primary", use_container_width=True, 
                    help="Fetch the full article and open it in your browser"):
            with st.spinner("🔄 Fetching article and opening in browser..."):
                try:
                    # Fetch the full article content
                    from article_fetcher import fetch_article
                    article_dir = fetch_article(article['pmcid'])
                    
                    if article_dir:
                        st.success("✅ Article fetched successfully! Opening in browser...")
                        st.session_state.article_fetched = True
                        st.session_state.article_dir = article_dir
                        
                        # Convert to HTML and open in browser
                        from simple_html_to_pdf import SimpleHTMLToPDFConverter
                        from pathlib import Path
                        converter = SimpleHTMLToPDFConverter()
                        html_file = converter.convert_markdown_to_pdf(Path(article_dir) / "article.md", f"article_{article['pmcid']}")
                        
                        if html_file:
                            st.success("✅ Article opened in browser!")
                            st.info("📖 You can now read the full article and use the DOWNLOAD PDF button to save it")
                        else:
                            st.error("❌ Failed to open in browser")
                    else:
                        st.error("❌ Failed to fetch article content")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.error("💡 Make sure you have the required libraries installed: pip install markdown weasyprint playwright")
    else:
        st.success("✅ Article already fetched!")
        if st.button("🌐 Open Article Again", type="secondary", use_container_width=True):
            try:
                article_dir = st.session_state.get('article_dir')
                if article_dir:
                    from simple_html_to_pdf import SimpleHTMLToPDFConverter
                    from pathlib import Path
                    converter = SimpleHTMLToPDFConverter()
                    html_file = converter.convert_markdown_to_pdf(Path(article_dir) / "article.md", f"article_{article['pmcid']}")
                    if html_file:
                        st.success("✅ Article opened in browser!")
            except Exception as e:
                st.error(f"❌ Error opening article: {str(e)}")
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔗 View on PubMed", use_container_width=True):
            st.markdown(f"[Open in PubMed]({article['pubmed_url']})")
    
    with col2:
        if st.button("📖 View on PMC", use_container_width=True):
            st.markdown(f"[Open in PMC]({article['pmc_url']})")
    
    with col3:
        if st.button("📄 Fetch Full Article", type="primary", use_container_width=True):
            with st.spinner("🔄 Fetching full article content..."):
                try:
                    # Fetch the full article content
                    from article_fetcher import fetch_article
                    article_dir = fetch_article(article['pmcid'])
                    
                    if article_dir:
                        st.success("✅ Full article fetched successfully!")
                        st.info(f"📁 Article saved to: {article_dir}")
                        
                        # Find the markdown file
                        import os
                        from pathlib import Path
                        article_path = Path(article_dir)
                        md_files = list(article_path.glob("*.md"))
                        
                        if md_files:
                            md_file = md_files[0]
                            st.success(f"📄 Markdown file found: {md_file.name}")
                            
                            # Read and display the content
                            with open(md_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            st.markdown("### 📖 Full Article Content")
                            st.markdown(content)
                            
                            # Add button to open in browser
                            if st.button("🌐 Open in Browser", type="secondary", use_container_width=True):
                                from simple_html_to_pdf import SimpleHTMLToPDFConverter
                                converter = SimpleHTMLToPDFConverter()
                                html_file = converter.convert_markdown_to_pdf(md_file, f"article_{article['pmcid']}")
                                if html_file:
                                    st.success("✅ Article opened in browser!")
                                else:
                                    st.error("❌ Failed to open in browser")
                        else:
                            st.error("❌ No markdown file found in article directory")
                    else:
                        st.error("❌ Failed to fetch article content")
                        
                except Exception as e:
                    st.error(f"❌ Error fetching article: {str(e)}")
    
    with col4:
        if st.button("📱 Download PDF", use_container_width=True):
            st.session_state.article_mode = 'download'
            st.rerun()
    
    # Back button
    if st.button("🔍 Back to Search", use_container_width=True):
        st.session_state.article_mode = 'search'
        st.rerun()

def render_pdf_downloader():
    """Render the PDF download interface."""
    st.markdown("### 📱 PDF Download")
    
    if not st.session_state.selected_article:
        st.warning("⚠️ No article selected for PDF conversion.")
        if st.button("🔍 Back to Search"):
            st.session_state.article_mode = 'search'
            st.rerun()
        return
    
    article = st.session_state.selected_article
    
    st.info(f"📄 Converting article to PDF: **{article['title']}**")
    
    if st.button("🚀 Generate PDF", type="primary", use_container_width=True):
        with st.spinner("🔄 Fetching article and converting to PDF..."):
            pdf_path = fetch_and_convert_article(article['pmcid'])
            
            if pdf_path:
                st.success("✅ PDF generated successfully!")
                
                # Provide download link
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_file.read(),
                        file_name=f"article_{article['pmcid']}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                st.info(f"📁 PDF saved at: `{pdf_path}`")
            else:
                st.error("❌ PDF generation failed. Please try again.")
    
    # Back button
    if st.button("🔍 Back to Search", use_container_width=True):
        st.session_state.article_mode = 'search'
        st.rerun()

# -----------------------------
# Utility Functions
# -----------------------------
def reset_article_state():
    """Reset article fetching state."""
    if 'article_mode' in st.session_state:
        del st.session_state.article_mode
    if 'search_results' in st.session_state:
        del st.session_state.search_results
    if 'selected_article' in st.session_state:
        del st.session_state.selected_article
    if 'selected_pmcid' in st.session_state:
        del st.session_state.selected_pmcid
    if 'article_search_query' in st.session_state:
        del st.session_state.article_search_query
    if 'article_fetched' in st.session_state:
        del st.session_state.article_fetched
    if 'article_dir' in st.session_state:
        del st.session_state.article_dir

def get_article_fetching_button():
    """Get the beautiful Articles button for the main interface."""
    return st.button("📚 Articles", use_container_width=True, type="secondary")

def test_article_system_integration():
    """Test the integration of the article system components."""
    st.markdown("### 🧪 Testing Article System Integration")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Test Europe PMC Search"):
            with st.spinner("Testing Europe PMC search..."):
                try:
                    # Test basic search functionality
                    test_query = "lung cancer treatment"
                    articles = search_articles(test_query, max_results=5)
                    if articles:
                        st.success(f"✅ Europe PMC search working! Found {len(articles)} articles")
                        st.session_state.test_results = articles[:3]  # Show first 3
                    else:
                        st.warning("⚠️ Europe PMC search returned no results")
                except Exception as e:
                    st.error(f"❌ Europe PMC search failed: {str(e)}")
    
    with col2:
        if st.button("🤖 Test Groq API"):
            with st.spinner("Testing Groq API..."):
                try:
                    test_query = "cancer treatment"
                    enhanced = enhance_query_with_groq(test_query)
                    if enhanced and enhanced != test_query:
                        st.success(f"✅ Groq API working! Enhanced query: {enhanced}")
                    else:
                        st.warning("⚠️ Groq API enhancement minimal")
                except Exception as e:
                    st.error(f"❌ Groq API failed: {str(e)}")
    
    with col3:
        if st.button("📄 Test PDF Converter"):
            with st.spinner("Testing PDF converter..."):
                try:
                    from simple_html_to_pdf import SimpleHTMLToPDFConverter
                    converter = SimpleHTMLToPDFConverter()
                    st.success("✅ PDF converter imported successfully")
                except Exception as e:
                    st.error(f"❌ PDF converter failed: {str(e)}")
    
    with col4:
        if st.button("🧪 Test User Query"):
            with st.spinner("Testing with user's query..."):
                try:
                    user_query = st.session_state.get('article_search_query', 'myocardial infarction diagnosis treatment outcomes')
                    st.info(f"Testing query: {user_query}")
                    
                    # Test the full workflow
                    enhanced = enhance_query_with_groq(user_query)
                    articles = search_articles(enhanced, max_results=5)
                    
                    if articles:
                        st.success(f"✅ Full workflow working! Found {len(articles)} articles")
                        st.session_state.test_results = articles[:3]
                    else:
                        st.warning("⚠️ Full workflow failed - no articles found")
                except Exception as e:
                    st.error(f"❌ Full workflow test failed: {str(e)}")
    
    # Show test results if available
    if hasattr(st.session_state, 'test_results') and st.session_state.test_results:
        st.markdown("### 📋 Test Results")
        for article in st.session_state.test_results:
            st.info(f"**{article['title'][:60]}...** | PMID: {article['pmid']} | PMCID: {article['pmcid']}")
