import os
import re
import time
import json
import requests
from typing import List, Dict, Optional, Tuple
from xml.etree import ElementTree as ET
from collections import Counter
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -----------------------------
# CONFIG
# -----------------------------
NCBI_API_KEY = os.getenv("NCBI_API_KEY")
NCBI_EMAIL = os.getenv("NCBI_EMAIL")
NCBI_TOOL = os.getenv("NCBI_TOOL", "medbot-rag")

# Validate required environment variables
if not NCBI_API_KEY:
    raise ValueError("NCBI_API_KEY environment variable is required. Please set it in your .env file.")
if not NCBI_EMAIL:
    raise ValueError("NCBI_EMAIL environment variable is required. Please set it in your .env file.")

# Use Europe PMC instead of NCBI for consistency with article_fetcher.py
EUROPE_PMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
HEADERS = {"User-Agent": f"{NCBI_TOOL} ({NCBI_EMAIL})"}
NCBI_SLEEP_SEC = 0.34  # NCBI polite rate limit

# Chroma / Embeddings
CHROMA_COLLECTION = "mesh_terms"
BIOBERT_MODEL = os.getenv("BIOBERT_MODEL", "pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb")

# -----------------------------
# Utilities
# -----------------------------
def _sleep():
    """Throttle requests for NCBI policy compliance"""
    time.sleep(NCBI_SLEEP_SEC)

def _clean(s: Optional[str]) -> str:
    return (s or "").strip()

def _dedup_preserve(seq):
    seen = set()
    out = []
    for x in seq:
        if not x:
            continue
        if x.lower() not in seen:
            out.append(x)
            seen.add(x.lower())
    return out

# -----------------------------
# Core Europe PMC Client (replacing NCBI for consistency)
# -----------------------------
class EuropePMCClient:
    def __init__(self, api_key=None, email=None, tool=None):
        self.api_key = api_key or NCBI_API_KEY
        self.email = email or NCBI_EMAIL
        self.tool = tool or NCBI_TOOL

    def _common_params(self):
        return {"api_key": self.api_key, "email": self.email, "tool": self.tool}

    def search_articles(self, query: str, retmax: int = 10) -> dict:
        """Search Europe PMC for articles matching query"""
        try:
            from urllib.parse import quote
            url = f"{EUROPE_PMC_BASE}/search?query={quote(query)}&format=json&pageSize={retmax}"
            r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        _sleep()
        return r.json()
        except requests.exceptions.RequestException as e:
            print(f"Error in Europe PMC search: {e}")
            return {"resultList": {"result": []}}

    def fetch_article_by_pmid(self, pmid: str) -> dict:
        """Fetch article details by PMID from Europe PMC"""
        try:
            url = f"{EUROPE_PMC_BASE}/search?query=EXT_ID:{pmid}&format=json"
            r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        _sleep()
            
            data = r.json()
            if data.get("resultList", {}).get("result"):
                return data["resultList"]["result"][0]
            return {}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching article by PMID: {e}")
            return {}

    def fetch_articles_by_pmids(self, pmids: List[str]) -> List[dict]:
        """Fetch multiple articles by PMIDs"""
        articles = []
        for pmid in pmids:
            article = self.fetch_article_by_pmid(pmid)
            if article:
                articles.append(article)
        return articles

# -----------------------------
# Parsing Helpers (PubMed)
# -----------------------------
def parse_pubmed_article(article_data: Dict) -> Dict:
    """Parse Europe PMC article data with better error handling."""
    try:
        out = {"pmid": None, "pmcid": None, "title": None, "abstract": None, "authors": [], "journal": None, "year": None}
        
        # Check if element is valid
        if article_data is None:
            print("Warning: Invalid article data")
            return out
        
        # Extract PMID
        out["pmid"] = article_data.get("pmid")
        
        # Extract PMCID (this is crucial for article_fetcher.py)
        out["pmcid"] = article_data.get("pmcid")
        
        # Extract title
        out["title"] = _clean(article_data.get("title"))
        
        # Extract abstract
        out["abstract"] = _clean(article_data.get("abstractText"))

        # Extract authors
        author_string = article_data.get("authorString")
        if author_string:
            # Split author string by semicolon and clean up
            authors = [author.strip() for author in author_string.split(";") if author.strip()]
            out["authors"] = authors

        # Extract journal
        out["journal"] = article_data.get("journalTitle")
        
        # Extract year
        out["year"] = article_data.get("pubYear")
        
    return out
        
    except Exception as e:
        print(f"Error parsing article: {e}")
        return {"pmid": None, "pmcid": None, "title": None, "abstract": None, "authors": [], "journal": None, "year": None}

def pmids_to_pmcids(client: EuropePMCClient, pmids: List[str]) -> Dict[str, str]:
    pmcid_map = {}
    if not pmids: return pmcid_map
    # The original elink logic was for NCBI, which is no longer used.
    # For Europe PMC, we'll just map PMIDs to PMCIDs if they are PMC IDs.
    for pmid in pmids:
        if pmid.startswith("PMC"):
            pmcid_map[pmid] = pmid
        elif pmid.startswith("PMID"):
            # For PubMed, we can't directly get PMC ID from PMID.
            # This function is now primarily for PMC mapping.
            pmcid_map[pmid] = pmid
    return pmcid_map

# -----------------------------
# MeSH: dynamic fetch + parse
# -----------------------------
def mesh_search_descriptors(client: EuropePMCClient, query: str, retmax: int = 10) -> List[str]:
    """Search MeSH db for descriptor UIDs matching a query (free text)."""
    # This function is no longer directly applicable to Europe PMC as they don't have a direct MeSH API.
    # It's kept for compatibility with existing code, but will return empty.
    print("Warning: mesh_search_descriptors is not directly applicable to Europe PMC.")
    return []

def mesh_fetch_descriptors(client: EuropePMCClient, uids: List[str]) -> List[Dict]:
    """
    Fetch descriptor records from MeSH and extract:
      - descriptor_name
      - descriptor_ui
      - entry_terms (synonyms)
    """
    # This function is no longer directly applicable to Europe PMC as they don't have a direct MeSH API.
    # It's kept for compatibility with existing code, but will return empty.
    print("Warning: mesh_fetch_descriptors is not directly applicable to Europe PMC.")
    return []

# ChromaDB: cache MeSH + semantic search

_chroma_client = None
_chroma_collection = None

def _get_chroma_collection():
    global _chroma_client, _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection
    import chromadb
    from chromadb.utils import embedding_functions
    _chroma_client = chromadb.Client()
    emb = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=BIOBERT_MODEL)
    _chroma_collection = _chroma_client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=emb,
        metadata={"source": "ncbi_mesh_dynamic"}
    )
    return _chroma_collection

def cache_mesh_records_in_chroma(records: List[Dict]):
    """
    Upsert MeSH descriptors + synonyms into Chroma.
    Each record gets one doc string: "DescriptorName. Synonyms: ...".
    """
    if not records: return
    coll = _get_chroma_collection()
    ids, docs, metas = [], [], []
    for r in records:
        ui = r["descriptor_ui"]
        name = r["descriptor_name"]
        syns = r.get("entry_terms", [])
        doc = f"{name}. Synonyms: {', '.join(_dedup_preserve(syns))}"
        ids.append(ui or name)
        docs.append(doc)
        metas.append({"ui": ui, "name": name, "synonyms": json.dumps(syns, ensure_ascii=False)})
    # Chunk to avoid too-large upserts
    CHUNK = 100
    for i in range(0, len(ids), CHUNK):
        coll.upsert(ids=ids[i:i+CHUNK], documents=docs[i:i+CHUNK], metadatas=metas[i:i+CHUNK])

def chroma_semantic_mesh_lookup(text: str, k: int = 5) -> List[Dict]:
    coll = _get_chroma_collection()
    res = coll.query(query_texts=[text], n_results=k)
    out = []
    for i, doc in enumerate(res.get("documents", [[]])[0]):
        meta = res.get("metadatas", [[]])[0][i] or {}
        out.append({
            "descriptor_ui": meta.get("ui"),
            "descriptor_name": meta.get("name"),
            "entry_terms": json.loads(meta.get("synonyms", "[]")),
            "document": doc
        })
    return out

# -----------------------------
# Optional LLM expansion (provider-agnostic)
# -----------------------------
def llm_expand_query(user_query: str, context_hint: str = "") -> List[str]:
    """
    Use Groq API to enhance medical search queries for PubMed/MeSH.
    Returns a list of concise, medically-appropriate expansions.
    """
    try:
        # Get Groq API key from environment
        groq_api_key = os.getenv("PMID")
        if not groq_api_key:
            print("Warning: PMID (Groq API key) not found, using fallback expansion")
            return _fallback_heuristic_expansion(user_query)
        
        # Use Groq API for query enhancement
        from openai import OpenAI
        
        client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        # Create enhancement prompt
        enhancement_prompt = f"""You are a medical search query specialist. Your task is to enhance a user's medical question for PubMed/MeSH search.

User Query: "{user_query}"
Context: {context_hint}

Instructions:
1. Generate 5-8 medical search terms that would help find relevant articles
2. Include medical synonyms, abbreviations, and related terminology
3. Use proper medical terminology that PubMed/MeSH would recognize
4. Keep each term concise (2-6 words max)
5. Focus on the core medical concept

Return ONLY the search terms, one per line, no numbering or extra text.

Example for "heart attack":
myocardial infarction
acute coronary syndrome
cardiac arrest
coronary thrombosis
ischemic heart disease"""

        # Call Groq API
        response = client.chat.completions.create(
            model="llama3-70b-8192",  # Using Llama3 model
            messages=[
                {"role": "system", "content": "You are a medical search query specialist. Provide only medical search terms, one per line."},
                {"role": "user", "content": enhancement_prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        # Extract and clean response
        enhanced_terms = response.choices[0].message.content.strip().split('\n')
        enhanced_terms = [term.strip() for term in enhanced_terms if term.strip()]
        
        # Add original query and ensure we have good terms
        if enhanced_terms:
            enhanced_terms = [user_query] + enhanced_terms
            return _dedup_preserve(enhanced_terms)[:8]
        else:
            print("Warning: LLM returned empty response, using fallback")
            return _fallback_heuristic_expansion(user_query)
            
    except Exception as e:
        print(f"Warning: LLM enhancement failed: {e}, using fallback")
        return _fallback_heuristic_expansion(user_query)

def _fallback_heuristic_expansion(user_query: str) -> List[str]:
    """Fallback heuristic expansions when LLM is not available."""
    uq = user_query.strip().lower()
    seeds = [user_query]
    
    # Simple normalizations helpful for cardiology examples
    if "bypass" in uq or "by pass" in uq:
        seeds += [
            "coronary artery bypass grafting",
            "CABG",
            "coronary bypass surgery",
            "myocardial revascularization",
        ]
    elif "heart attack" in uq or "heartattack" in uq:
        seeds += [
            "myocardial infarction",
            "acute coronary syndrome",
            "cardiac arrest",
            "coronary thrombosis",
        ]
    elif "diabetes" in uq:
        seeds += [
            "diabetes mellitus",
            "type 2 diabetes",
            "insulin resistance",
            "hyperglycemia",
        ]
    elif "cancer" in uq:
        seeds += [
            "neoplasms",
            "oncology",
            "malignant tumors",
            "carcinogenesis",
        ]
    elif "lung" in uq:
        seeds += [
            "pulmonary neoplasms",
            "lung carcinoma",
            "bronchogenic carcinoma",
            "non-small cell lung cancer",
            "small cell lung cancer",
        ]
    
    return _dedup_preserve(seeds)[:5]

# -----------------------------
# Query building
# -----------------------------
def build_pubmed_boolean_query(
    user_query: str,
    mesh_hits: List[Dict],
    llm_terms: List[str],
    max_mesh: int = 6,
    max_synonyms_per_mesh: int = 5
) -> str:
    """
    Combine:
      - original user text (as [tiab])
      - top MeSH descriptors ([mh]) + a few synonyms ([tiab])
      - LLM expansions ([tiab])
    """
    tiab_clauses = []
    if user_query:
        tiab_clauses.append(f'("{user_query}"[tiab])')

    # LLM expansions
    for t in llm_terms:
        if t and t.lower() != user_query.lower():
            tiab_clauses.append(f'("{t}"[tiab])')

    # MeSH
    mh_clauses = []
    syn_clauses = []
    for r in mesh_hits[:max_mesh]:
        name = r.get("descriptor_name")
        if name:
            mh_clauses.append(f'"{name}"[mh]')
        for s in r.get("entry_terms", [])[:max_synonyms_per_mesh]:
            syn_clauses.append(f'"{s}"[tiab]')

    # Join
    mh_block = f"({' OR '.join(mh_clauses)})" if mh_clauses else ""
    tiab_block = f"({' OR '.join(tiab_clauses + syn_clauses)})" if (tiab_clauses or syn_clauses) else ""

    if mh_block and tiab_block:
        return f"({mh_block}) OR {tiab_block}"
    return mh_block or tiab_block or user_query

# -----------------------------
# Simple summarizer
# -----------------------------
def simple_corpus_summary(text: str, max_sentences: int = 7) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return " ".join(sentences)
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    freq = Counter(w for w in words if len(w) > 2)
    scores = []
    for i, s in enumerate(sentences):
        sw = re.findall(r"[a-zA-Z0-9]+", s.lower())
        scores.append((sum(freq.get(w, 0) for w in sw), i, s))
    top = sorted(scores, key=lambda x: (-x[0], x[1]))[:max_sentences]
    return " ".join(s for _, _, s in sorted(top, key=lambda x: x[1]))

# -----------------------------
# Main Report Builder (now with enhanced query)
# -----------------------------
def build_markdown_report(
    query: Optional[str] = None,
    seed_pmids: Optional[List[str]] = None,
    max_search: int = 10,
    include_related: bool = True,
    max_related_per_seed: int = 5,
    mesh_retmax: int = 10
) -> Dict[str, any]:
    """
    Build a comprehensive markdown report and return both the markdown content and articles data.
    Returns a dictionary with 'markdown' and 'articles' keys.
    """
    try:
        client = EuropePMCClient()

    # 1) Dynamic MeSH fetch + Chroma cache
        try:
    mesh_uids = mesh_search_descriptors(client, query or "")
    mesh_records = mesh_fetch_descriptors(client, mesh_uids)
    cache_mesh_records_in_chroma(mesh_records)
        except Exception as e:
            print(f"Warning: MeSH processing failed: {e}")
            mesh_records = []

    # 2) LLM/context expansions + semantic MeSH lookup
        try:
    llm_terms = llm_expand_query(query or "", context_hint="biomedical literature search; PubMed/MeSH")
            print(f"🧠 LLM Enhanced Terms: {llm_terms}")
    mesh_hits = chroma_semantic_mesh_lookup(query or "", k=min(8, max(3, len(mesh_records) or 5)))
        except Exception as e:
            print(f"Warning: LLM expansion failed: {e}")
            llm_terms = []
            mesh_hits = []

    # 3) Build enhanced PubMed query
    enhanced_query = build_pubmed_boolean_query(
        user_query=query or "", mesh_hits=mesh_hits, llm_terms=llm_terms
    )

    # 4) PubMed search with enhanced query
    pmids = seed_pmids or []
    if enhanced_query:
            try:
                # Use Europe PMC search with proper query syntax
                # For Europe PMC, we need to use different query format than NCBI
                # Try different search strategies
                search_queries = [
                    enhanced_query,  # Original enhanced query
                    query,  # Fallback to original query
                    f'"{query}"',  # Quoted original query
                ]
                
                pmids = []
                for search_query in search_queries:
                    if pmids:  # If we found some, break
                        break
                        
                    try:
                        js = client.search_articles(search_query, retmax=max_search)
                        results = js.get("resultList", {}).get("result", [])
                        
                        if results:
                            # Extract PMIDs from results
                            for item in results:
                                pmid = item.get("pmid")
                                if pmid and pmid not in pmids:
                                    pmids.append(pmid)
                                    if len(pmids) >= max_search:
                                        break
                        
                        print(f"🔍 Search query '{search_query}' returned {len(results)} results, found {len(pmids)} PMIDs")
                        
                    except Exception as e:
                        print(f"Warning: Search query '{search_query}' failed: {e}")
                        continue
                        
            except Exception as e:
                print(f"Warning: PubMed search failed: {e}")
                pmids = []
        
    if not pmids:
            print(f"⚠️  No PMIDs found for any search query. Using fallback approach.")
            # Try a simple search as last resort
            try:
                simple_query = query.replace(" ", " AND ")
                js = client.search_articles(simple_query, retmax=max_search)
                results = js.get("resultList", {}).get("result", [])
                
                if results:
                    for item in results:
                        pmid = item.get("pmid")
                        if pmid and pmid not in pmids:
                            pmids.append(pmid)
                            if len(pmids) >= max_search:
                                break
                    print(f"🔍 Fallback search found {len(pmids)} PMIDs")
            except Exception as e:
                print(f"Warning: Fallback search also failed: {e}")
        
        if not pmids:
            error_msg = f"# ❌ No articles found for query: `{query}`\n\nEnhanced query: `{enhanced_query}`\nTry adjusting the terms."
            return {
                "markdown": error_msg,
                "articles": [],
                "query": query,
                "enhanced_query": enhanced_query,
                "seed_count": 0,
                "related_count": 0,
                "total_count": 0
            }

    # 5) Fetch seed articles
        try:
            
            pubmed_xml = client.fetch_articles_by_pmids(pmids)
            seed_articles = [parse_pubmed_article(a) for a in pubmed_xml]
        except Exception as e:
            print(f"Warning: Failed to fetch articles: {e}")
            seed_articles = []

    # 6) Relateds
    related_articles = []
    if include_related and pmids:
            try:
                
                related_xml = client.fetch_articles_by_pmids(pmids)
                related_articles = [parse_pubmed_article(a) for a in related_xml]
            except Exception as e:
                print(f"Warning: Failed to fetch related articles: {e}")

    # 7) Map to PMC
        try:
    pmcid_map = pmids_to_pmcids(client, pmids)
        except Exception as e:
            print(f"Warning: PMC mapping failed: {e}")
            pmcid_map = {}

    # 8) Summary
    corpus_texts = [a["title"] + "\n" + (a["abstract"] or "") for a in seed_articles + related_articles if a.get("title")]
    summary = simple_corpus_summary("\n".join(corpus_texts), max_sentences=7) if corpus_texts else "No summary available."

    # 9) Markdown
    md = [
        "# 🧠 PubMed/PMC Research Report",
        f"- **Original query:** `{query}`",
        f"- **Enhanced PubMed query:** `{enhanced_query}`",
        f"- **Seed articles:** {len(seed_articles)} | **Related articles:** {len(related_articles)}",
        "",
        "## 📌 Executive Summary",
        summary,
        "",
        "## 🔎 Query Expansion Details",
        f"- **LLM terms:** {', '.join(llm_terms) if llm_terms else '—'}",
        f"- **Top MeSH hits:** {', '.join(_dedup_preserve([m.get('descriptor_name') for m in mesh_hits if m.get('descriptor_name')])) or '—'}",
        "",
        "## 📄 Articles"
    ]
        
    for idx, a in enumerate(seed_articles + related_articles, 1):
        authors = ", ".join(a["authors"]) if a["authors"] else "Unknown"
        md.append(
            f"### {idx}. {a['title']}\n"
            f"**Authors:** {authors}\n\n"
            f"**Abstract:** {a['abstract'] or 'No abstract available.'}\n\n"
            f"*Citation:* {a['title']} ({a['journal']}, {a['year']}). PMID: {a['pmid']}"
        )
        if a["pmid"] in pmcid_map:
            md.append(f"✅ **Full Text Available:** [PMC Link](https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid_map[a['pmid']]}/)")
        md.append("\n---")

    if len(related_articles) == 0:
        md += [
            "\n## ❗ No related articles found.\n",
            "### 🔍 Suggested Queries:",
            "- `coronary artery bypass grafting outcomes randomized`",
            "- `CABG vs PCI long-term survival`",
            "- `off-pump CABG complications`",
        ]

        markdown_content = "\n".join(md)
        
        # Combine all articles for reference
        all_articles = seed_articles + related_articles
        
        return {
            "markdown": markdown_content,
            "articles": all_articles,
            "query": query,
            "enhanced_query": enhanced_query,
            "seed_count": len(seed_articles),
            "related_count": len(related_articles),
            "total_count": len(all_articles)
        }

    except Exception as e:
        error_msg = f"# ❌ Error generating report\n\nAn error occurred: {str(e)}\n\nPlease check your configuration and try again."
        return {
            "markdown": error_msg,
            "articles": [],
            "query": query,
            "enhanced_query": "",
            "seed_count": 0,
            "related_count": 0,
            "total_count": 0
        }

def save_markdown(content, path=None):
    """Save markdown content with incremental numbering."""
    if path is None:
        # Find the next available number
        counter = 1
        while True:
            filename = f"medical_summary_{counter}.md"
            if not os.path.exists(filename):
                path = filename
                break
            counter += 1
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    abs_path = os.path.abspath(path)
    print(f"\n✅ Markdown report saved at: {abs_path}")
    return abs_path

def test_groq_connection():
    """Test Groq API connection and show enhanced query example."""
    try:
        groq_api_key = os.getenv("PMID")
        if not groq_api_key:
            print("❌ PMID (Groq API key) not found in environment variables")
            return False
        
        print("🔑 Groq API key found!")
        
        # Test with a simple query
        test_query = "diabetes treatment"
        print(f"\n🧪 Testing query enhancement for: '{test_query}'")
        
        enhanced_terms = llm_expand_query(test_query, "biomedical literature search")
        print(f"✅ Enhanced terms: {enhanced_terms}")
        
        return True
        
    except Exception as e:
        print(f"❌ Groq API test failed: {e}")
        return False

def extract_top_articles_info(articles: List[Dict], max_articles: int = 10) -> List[Dict]:
    """
    Extract key information from the top articles for reference.
    Only includes articles that have BOTH PMID and PMCID for data accuracy.
    Returns a list of dictionaries with PMID, PMCID, title, authors, and publication date.
    """
    extracted_info = []
    
    for i, article in enumerate(articles, 1):
        # Only include articles that have BOTH PMID and PMCID
        if not article.get("pmid") or not article.get("pmcid"):
            continue
            
        article_info = {
            "rank": len(extracted_info) + 1,  # Recalculate rank for valid articles only
            "pmid": article.get("pmid"),
            "pmcid": article.get("pmcid"),
            "title": article.get("title") or "No title available",
            "authors": ", ".join(article.get("authors", [])) if article.get("authors") else "Unknown authors",
            "publication_date": article.get("year") or "Date not available",
            "journal": article.get("journal") or "Journal not available",
            "abstract": article.get("abstract") or "No abstract available"
        }
        extracted_info.append(article_info)
        
        # Stop when we reach max_articles
        if len(extracted_info) >= max_articles:
            break
    
    return extracted_info

def save_articles_reference(articles: List[Dict], query: str, output_dir: str = "article_references") -> str:
    """
    Save a detailed reference file with the top articles information.
    Creates a markdown file with all article details for easy reference.
    """
    import os
    from datetime import datetime
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_query = safe_query.replace(' ', '_')[:50]  # Limit length
    filename = f"articles_reference_{safe_query}_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Extract top 10 articles info
    top_articles = extract_top_articles_info(articles, max_articles=10)
    
    # Create markdown content
    md_content = [
        f"# 📚 Articles Reference: {query}",
        f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total articles found:** {len(articles)}",
        f"**Top articles extracted:** {len(top_articles)}",
        "",
        "## 🔍 Search Query",
        f"`{query}`",
        "",
        "## 📋 Top Articles Summary"
    ]
    
    # Add summary table
    if top_articles:
        md_content.extend([
            "| Rank | PMID | PMCID | Title | Authors | Publication Date | Journal |",
            "|------|------|-------|-------|---------|------------------|---------|"
        ])
        
        for article in top_articles:
            title_short = article["title"][:60] + "..." if len(article["title"]) > 60 else article["title"]
            authors_short = article["authors"][:40] + "..." if len(article["authors"]) > 40 else article["authors"]
            md_content.append(
                f"| {article['rank']} | {article['pmid']} | {article['pmcid']} | {title_short} | {authors_short} | {article['publication_date']} | {article['journal']} |"
            )
    
    md_content.extend([
        "",
        "## 📄 Detailed Article Information"
    ])
    
    # Add detailed information for each article
    for article in top_articles:
        md_content.extend([
            f"### {article['rank']}. PMID: {article['pmid']} | PMCID: {article['pmcid']}",
            f"**Title:** {article['title']}",
            f"**Authors:** {article['authors']}",
            f"**Publication Date:** {article['publication_date']}",
            f"**Journal:** {article['journal']}",
            "",
            "**Abstract:**",
            f"{article['abstract']}",
            "",
            f"**PubMed Link:** [https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/](https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/)",
            f"**PMC Full Text:** [https://www.ncbi.nlm.nih.gov/pmc/articles/{article['pmcid']}/](https://www.ncbi.nlm.nih.gov/pmc/articles/{article['pmcid']}/)",
            "",
            "---",
            ""
        ])
    
    # Add footer
    md_content.extend([
        "## 📊 Statistics",
        f"- **Total articles processed:** {len(articles)}",
        f"- **Articles with valid PMIDs:** {len([a for a in articles if a.get('pmid')])}",
        f"- **Articles with valid PMCIDs:** {len([a for a in articles if a.get('pmcid')])}",
        f"- **Articles with BOTH PMID and PMCID:** {len([a for a in articles if a.get('pmid') and a.get('pmcid')])}",
        f"- **Articles with abstracts:** {len([a for a in articles if a.get('abstract')])}",
        f"- **Articles with author information:** {len([a for a in articles if a.get('authors')])}",
        "",
        "---",
        f"*This reference file was automatically generated by MedBot PubMed Research Assistant*"
    ])
    
    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))
    
    return filepath

def print_top_articles_summary(articles: List[Dict], max_articles: int = 10):
    """
    Print a formatted summary of the top articles to the console.
    Shows PMID, title, authors, and publication date in a readable format.
    """
    print(f"\n📋 TOP {min(max_articles, len(articles))} ARTICLES SUMMARY")
    print("=" * 80)
    
    top_articles = extract_top_articles_info(articles, max_articles)
    
    if not top_articles:
        print("❌ No articles with valid PMIDs found.")
        return
    
    for article in top_articles:
        print(f"\n🔸 Article #{article['rank']}")
        print(f"   PMID: {article['pmid']}")
        print(f"   PMCID: {article['pmcid']}")
        print(f"   Title: {article['title']}")
        print(f"   Authors: {article['authors']}")
        print(f"   Published: {article['publication_date']}")
        print(f"   Journal: {article['journal']}")
        print(f"   PubMed: https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/")
        print(f"   PMC Full Text: https://www.ncbi.nlm.nih.gov/pmc/articles/{article['pmcid']}/")
        print("-" * 60)

# Enhanced save function that also saves article references
def save_markdown_with_references(content: str, articles: List[Dict], query: str, path: str = None) -> Dict[str, str]:
    """
    Save markdown content with incremental numbering AND save article references.
    Returns a dictionary with paths to both files.
    """
    # Save the main markdown report
    main_file = save_markdown(content, path)
    
    # Save article references
    ref_file = save_articles_reference(articles, query)
    
    # Print summary to console
    print_top_articles_summary(articles)
    
    print(f"\n✅ Files saved successfully:")
    print(f"   📄 Main Report: {os.path.basename(main_file)}")
    print(f"   📚 Articles Reference: {os.path.basename(ref_file)}")
    
    return {
        "main_report": main_file,
        "articles_reference": ref_file
    }

# Example usage
if __name__ == "__main__":
    print("🚀 MedBot PubMed Research Assistant")
    print("=" * 50)
    
    # Test Groq API connection first
    if test_groq_connection():
        print("\n🎯 Groq API is working! Proceeding with enhanced search...")
        
        query = "lung cancer"  # user input
        print(f"\n🔍 Processing query: '{query}'")
        print("📚 Using Groq API for enhanced query expansion...")
        
        report_data = build_markdown_report(query=query, max_search=10)
        report_content = report_data["markdown"]
        articles_data = report_data["articles"]
        
        print(f"\n📊 Found {report_data['total_count']} articles ({report_data['seed_count']} seed + {report_data['related_count']} related)")
        
        # Save both main report and article references using real data
        if articles_data:
            saved_files = save_markdown_with_references(report_content, articles_data, query)
            
            print(f"\n🎯 Report and references generated successfully!")
            print(f"📁 Main Report: {os.path.basename(saved_files['main_report'])}")
            print(f"📚 Articles Reference: {os.path.basename(saved_files['articles_reference'])}")
            print(f"📍 Main Report Location: {saved_files['main_report']}")
            print(f"📍 Articles Reference Location: {saved_files['articles_reference']}")
        else:
            # Fallback to just saving the main report if no articles found
            output_file = save_markdown(report_content)
            print(f"\n⚠️  No articles found, only main report saved: {os.path.basename(output_file)}")
        
    else:
        print("\n⚠️  Using fallback query enhancement (no Groq API)")
        query = "lung cancer"
        report_data = build_markdown_report(query=query, max_search=10)
        report_content = report_data["markdown"]
        articles_data = report_data["articles"]
        
        print(f"\n📊 Found {report_data['total_count']} articles ({report_data['seed_count']} seed + {report_data['related_count']} related)")
        
        # Save both main report and article references using real data
        if articles_data:
            saved_files = save_markdown_with_references(report_content, articles_data, query)
            print(f"\n📁 Files saved: {os.path.basename(saved_files['main_report'])} and {os.path.basename(saved_files['articles_reference'])}")
        else:
            # Fallback to just saving the main report if no articles found
            output_file = save_markdown(report_content)
            print(f"\n⚠️  No articles found, only main report saved: {os.path.basename(output_file)}")
