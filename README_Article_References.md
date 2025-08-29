# 📚 Enhanced Article Reference System for MedBot

This document describes the enhanced functionality added to `pmid.py` for extracting, saving, and referencing the top articles from PubMed searches.

## 🆕 New Features

### 1. **Article Information Extraction**
- **Function**: `extract_top_articles_info(articles, max_articles=10)`
- **Purpose**: Extracts key metadata from the **top 10 articles** including PMID, title, authors, publication date, journal, and abstract
- **Returns**: List of dictionaries with structured article information for the top 10 articles

### 2. **Console Article Summary**
- **Function**: `print_top_articles_summary(articles, max_articles=10)`
- **Purpose**: Prints a formatted summary of the **top 10 articles** to the console
- **Features**: Shows PMID, title, authors, publication date, journal, and PubMed link for the top 10 articles

### 3. **Article Reference File Generation**
- **Function**: `save_articles_reference(articles, query, output_dir="article_references")`
- **Purpose**: Creates a comprehensive markdown file with all details for the **top 10 articles**
- **Features**: 
  - Summary table with key information for top 10 articles
  - Detailed article information with abstracts for top 10 articles
  - PubMed links for each of the top 10 articles
  - Statistics and metadata
  - Timestamped filenames

### 4. **Enhanced Save Function**
- **Function**: `save_markdown_with_references(content, articles, query, path=None)`
- **Purpose**: Saves both the main report AND article references
- **Returns**: Dictionary with paths to both files

## 📁 File Structure

```
MedBot/
├── pmid.py                           # Main enhanced file
├── test_article_functions.py         # Test script
├── article_references/               # Generated reference files
│   ├── articles_reference_heart_transplant_20231201_143022.md
│   └── ...
└── medical_summary_*.md             # Main research reports
```

## 🚀 Usage Examples

### Basic Usage

```python
from pmid import build_markdown_report, save_markdown_with_references

# Build report (now returns both markdown and articles data)
report_data = build_markdown_report(query="heart transplantation", max_search=10)

# Save both main report and article references
saved_files = save_markdown_with_references(
    content=report_data["markdown"],
    articles=report_data["articles"],
    query="heart transplantation"
)

print(f"Main report: {saved_files['main_report']}")
print(f"Articles reference: {saved_files['articles_reference']}")
```

### Extract Article Information Only

```python
from pmid import extract_top_articles_info

# Extract top 5 articles info
top_articles = extract_top_articles_info(articles_data, max_articles=5)

for article in top_articles:
    print(f"PMID: {article['pmid']}")
    print(f"Title: {article['title']}")
    print(f"Authors: {article['authors']}")
    print(f"Published: {article['publication_date']}")
    print("---")
```

### Print Console Summary

```python
from pmid import print_top_articles_summary

# Print formatted summary to console
print_top_articles_summary(articles_data, max_articles=10)
```

### Save Reference File Only

```python
from pmid import save_articles_reference

# Save articles reference file
ref_file = save_articles_reference(
    articles=articles_data,
    query="heart transplantation research",
    output_dir="my_references"
)
```

## 📊 Generated Reference File Format

The generated reference file includes:

1. **Header Information**
   - Search query
   - Generation timestamp
   - Article counts

2. **Summary Table**
   - Rank, PMID, Title, Authors, Publication Date, Journal

3. **Detailed Article Information**
   - Full title and abstract
   - Complete author list
   - Journal details
   - PubMed link

4. **Statistics**
   - Total articles processed
   - Articles with valid PMIDs
   - Articles with abstracts
   - Articles with author information

## 🔧 Configuration

### Output Directory
- Default: `article_references/`
- Can be customized in `save_articles_reference()`

### Article Limit
- Default: Top 10 articles
- Can be customized in `extract_top_articles_info()`

### File Naming
- Format: `articles_reference_{query}_{timestamp}.md`
- Query is sanitized for filename safety
- Timestamp format: `YYYYMMDD_HHMMSS`

## 🧪 Testing

Run the test script to verify functionality:

```bash
python test_article_functions.py
```

This will:
1. Test article extraction
2. Test console summary printing
3. Test reference file generation
4. Create sample reference files

## 📝 Example Output

### Console Summary
```
📋 TOP 3 ARTICLES SUMMARY
================================================================================

🔸 Article #1
   PMID: 12345678
   Title: Advanced Heart Transplantation Techniques in Modern Cardiology
   Authors: Dr. John Smith, Dr. Sarah Johnson, Dr. Michael Brown
   Published: 2023
   Journal: Journal of Cardiovascular Medicine
   PubMed: https://pubmed.ncbi.nlm.nih.gov/12345678/
------------------------------------------------------------
```

### Reference File Content
```markdown
# 📚 Articles Reference: heart transplantation research
**Generated on:** 2023-12-01 14:30:22
**Total articles found:** 5
**Top articles extracted:** 5

## 🔍 Search Query
`heart transplantation research`

## 📋 Top Articles Summary
| Rank | PMID | Title | Authors | Publication Date | Journal |
|------|------|-------|---------|------------------|---------|
| 1 | 12345678 | Advanced Heart Transplantation Techniques in Modern Cardiology... | Dr. John Smith, Dr. Sarah Johnson, Dr. Michael Brown... | 2023 | Journal of Cardiovascular Medicine |
...
```

## 🔄 Integration with Existing Code

The enhanced functions are fully backward compatible:
- `build_markdown_report()` now returns a dictionary instead of just markdown
- Existing `save_markdown()` function still works
- New functions can be used independently or together

## 🎯 Benefits

1. **Easy Reference**: Quick access to article details without opening PubMed
2. **Organized Data**: Structured information in readable markdown format
3. **Comprehensive Coverage**: Includes all metadata, abstracts, and links
4. **Flexible Usage**: Can be used independently or integrated into workflows
5. **Professional Output**: Clean, formatted files suitable for sharing or documentation

## 🚨 Requirements

- Python 3.7+
- Required packages: `requests`, `xml.etree.ElementTree`, `collections`, `dotenv`
- Optional: `chromadb` for semantic search features
- Optional: `openai` for Groq API integration
