import requests
import re
from bs4 import BeautifulSoup
from pathlib import Path
import os
import json
from urllib.parse import quote

# ==== CONFIG ====
SAVE_ROOT = Path("articles")
ensure_dir = lambda p: p.mkdir(parents=True, exist_ok=True)

# ==== Helpers ====
def to_folder_name(text):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip())[:100]

def soup_xml(xml_text):
    return BeautifulSoup(xml_text, "lxml-xml")

def get_text(tag):
    return tag.get_text(" ", strip=True) if tag else ""

def md_header(meta):
    return f"# {meta.get('title','Untitled')}\n\n**Authors:** {meta.get('authorString','N/A')}\n\n**Journal:** {meta.get('journalTitle','N/A')} ({meta.get('pubYear','')})\n\n"

def md_abstract(abstract):
    return f"## Abstract\n\n{abstract}\n"

# ==== API Calls ====
def search_europe_pmc(identifier: str):
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={quote(identifier)}&format=json"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get("resultList", {}).get("result"):
        return data["resultList"]["result"][0]
    return None

def get_fulltext_xml(pmcid: str):
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
    r = requests.get(url)
    return r.text if r.status_code == 200 else None

def fetch_semantic_scholar(doi: str):
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,abstract,url"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

def fetch_unpaywall(doi: str):
    url = f"https://api.unpaywall.org/v2/{doi}?email=your_email@example.com"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

# ==== Table to Markdown ====
def table_to_markdown(tbl_wrap):
    caption = get_text(tbl_wrap.find("caption"))
    table = tbl_wrap.find("table")
    if not table:
        return ""
    rows = table.find_all("tr")
    md_rows = []
    for i, row in enumerate(rows):
        cells = [get_text(c) for c in row.find_all(["td","th"])]
        if cells:
            md_rows.append("| " + " | ".join(cells) + " |")
            if i == 0:
                md_rows.append("|" + "|".join(["---"] * len(cells)) + "|")
    md_table = "\n".join(md_rows)
    return f"### Table: {caption}\n\n{md_table}\n\n" if md_rows else ""

# ==== Figures ====
def build_candidate_img_urls(pmcid, href):
    base = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/supplementaryFiles/"
    return [base + href]

def try_download(url, dest):
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(dest, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return True
    except:
        pass
    return False

def parse_and_download_figures(soup, pmcid, fig_dir: Path):
    ensure_dir(fig_dir)
    md_parts = []
    for fig in soup.find_all("fig"):
        caption = get_text(fig.find("caption"))
        img_rel_path = None
        graphic = fig.find("graphic")
        if graphic and graphic.has_attr("xlink:href"):
            href = graphic["xlink:href"]
            dest = fig_dir / f"{href}.jpg"
            ok = False
            for url in build_candidate_img_urls(pmcid, href):
                if try_download(url, dest):
                    ok = True
                    break
            if ok:
                rel_path = dest.relative_to(SAVE_ROOT)
                img_rel_path = f"![]({rel_path.as_posix()})"
        part = f"**Figure:** {caption}\n\n"
        if img_rel_path:
            part += img_rel_path + "\n\n"
        md_parts.append(part)
    return "\n".join(md_parts) + "\n"

# ==== Parse Full Text ====
def parse_full_text(xml_text: str, pmcid: str, article_dir: Path) -> str:
    soup = soup_xml(xml_text)
    md = []

    # Sections
    for sec in soup.find_all("sec", recursive=True):
        title = get_text(sec.find("title")) or "Section"
        paras = [get_text(p) for p in sec.find_all("p", recursive=False)]
        if title or paras:
            md.append(f"## {title}\n\n" + "\n\n".join(paras) + "\n")

    # Tables
    for tbl_wrap in soup.find_all("table-wrap"):
        md.append(table_to_markdown(tbl_wrap))

    # Figures
    fig_dir = article_dir / "figures"
    fig_md = parse_and_download_figures(soup, pmcid, fig_dir)
    if fig_md.strip():
        md.append("## Figures\n\n" + fig_md)

    return "\n".join(md)

# ==== Save Markdown & PDF ====
def save_markdown_only(article_dir: Path, markdown_content: str):
    """Save only the markdown file - PDF conversion handled separately"""
    md_file = article_dir / "article.md"
    
    # Save Markdown
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"✅ Markdown saved: {md_file}")
    print(f"💡 To convert to PDF, use: python md_to_pdf_converter.py {md_file}")

# ==== Main Fetcher ====
def fetch_article(identifier: str):
    # Step 1: Search Europe PMC
    meta = search_europe_pmc(identifier)
    if not meta:
        print("❌ No article found in Europe PMC.")
        return

    title = meta.get("title") or "Untitled"
    abstract = meta.get("abstractText") or "No abstract available."
    pmcid = meta.get("pmcid")
    doi = meta.get("doi")

    # Make folder for this article
    article_dir = SAVE_ROOT / to_folder_name(title)
    ensure_dir(article_dir)

    # Build Markdown
    md_parts = []
    md_parts.append(md_header(meta))
    md_parts.append(md_abstract(abstract))

    # Step 2: If PMCID exists → Fetch full text
    if pmcid:
        xml_text = get_fulltext_xml(pmcid)
        if xml_text:
            md_parts.append(parse_full_text(xml_text, pmcid, article_dir))
        else:
            md_parts.append("⚠ Full text not available.\n")
    else:
        md_parts.append("⚠ No PMCID, cannot fetch full text.\n")

    # Step 3: Fallback if DOI exists
    if doi:
        ss = fetch_semantic_scholar(doi)
        if ss and ss.get("abstract"):
            md_parts.append(f"### Semantic Scholar Abstract\n\n{ss['abstract']}\n")
        up = fetch_unpaywall(doi)
        if up and up.get("best_oa_location"):
            pdf_url = up["best_oa_location"].get("url_for_pdf")
            if pdf_url:
                md_parts.append(f"📥 [Download OA PDF here]({pdf_url})\n")

    # Combine Markdown
    md_final = "\n".join(md_parts)

    # Save Markdown only
    save_markdown_only(article_dir, md_final)

    print("🎉 Done!")

# ==== Run ====
if __name__ == "__main__":
    identifier = input("Enter DOI / PMID / PMCID: ").strip()
    fetch_article(identifier)
