import os
import time
import sqlite3
import urllib.parse
from scrapegraphai.graphs import SmartScraperGraph
from langchain_openai import ChatOpenAI

# Configuration for DeepSeek V4 Flash via OpenCode
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your_deepseek_api_key_here")

llm_model_instance = ChatOpenAI(
    api_key=os.getenv("OPENCODE_API_KEY", ""),  # key scrubbed before committing to git
    model="deepseek-v4-flash",
    base_url="https://opencode.ai/zen/go/v1"
)

graph_config = {
    "llm": {
        "model_instance": llm_model_instance,
        "model_tokens": 128000, # Lowered slightly to speed up processing while still allowing visual rendering
    },
    "verbose": True, 
    "headless": False,
}

# 1. Advanced Boolean Search Strategy
# Unencoded: ("Data Scientist" OR "AI Engineer" OR "Gen AI" OR "AI Agent" OR "LLM") AND ("Operations" OR "Automation" OR "CRM" OR "Advertising" OR "Reconciliation")
BOOLEAN_QUERY = '("Data Scientist" OR "AI Engineer" OR "Gen AI" OR "AI Agent" OR "LLM") AND ("Operations" OR "Automation" OR "CRM" OR "Advertising" OR "Reconciliation")'
ENCODED_QUERY = urllib.parse.quote(BOOLEAN_QUERY)
BASE_SEARCH_URL = f"https://www.linkedin.com/jobs/search/?keywords={ENCODED_QUERY}&sortBy=DD"

# 2. Time filters in seconds: 24 hours (Today), 48 hours (Yesterday), 72 hours (Day before yesterday)
TIME_FILTERS = [86400, 172800, 259200]

def init_db():
    conn = sqlite3.connect("matched_jobs.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            salary_range TEXT,
            experience_required TEXT,
            posted_date TEXT,
            url TEXT UNIQUE,
            reason TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_history (
            url TEXT PRIMARY KEY,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_already_processed(url: str) -> bool:
    conn = sqlite3.connect("matched_jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM processed_history WHERE url = ?", (url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def log_processed_url(url: str):
    conn = sqlite3.connect("matched_jobs.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO processed_history (url) VALUES (?)", (url,))
        conn.commit()
    except Exception as e:
        print(f"Error logging history: {e}")
    finally:
        conn.close()

def save_job_to_db(job_data: dict):
    conn = sqlite3.connect("matched_jobs.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO jobs (title, company, salary_range, experience_required, posted_date, url, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job_data.get("title"),
            job_data.get("company"),
            job_data.get("salary_range"),
            job_data.get("experience_required"),
            job_data.get("posted_date"),
            job_data.get("url"),
            job_data.get("reason")
        ))
        conn.commit()
    except Exception as e:
        print(f"Database insertion error: {e}")
    finally:
        conn.close()

def extract_job_links(search_url: str) -> list:
    prompt = """
    Extract all individual job posting links visible on this search results page.
    Return a list of JSON objects, where each object has a 'link' key containing the absolute URL to the job posting.
    """
    scraper = SmartScraperGraph(prompt=prompt, source=search_url, config=graph_config)
    try:
        result = scraper.run()
        return [item.get("link") for item in result if "link" in item]
    except Exception as e:
        print(f"Error extracting links: {e}")
        return []

def get_job_links_with_fallback() -> list:
    """Checks Today, Yesterday, and the Day Before Yesterday for jobs."""
    for time_window in TIME_FILTERS:
        target_url = f"{BASE_SEARCH_URL}&f_TPR=r{time_window}"
        
        if time_window == 86400:
            print(f"Searching for jobs posted TODAY (Last 24 Hours)...")
        elif time_window == 172800:
            print(f"Searching for jobs posted YESTERDAY (Last 48 Hours)...")
        else:
            print(f"Searching for jobs posted DAY BEFORE YESTERDAY (Last 72 Hours)...")
            
        links = extract_job_links(target_url)
        
        if links and len(links) > 0:
            print(f"Success! Found {len(links)} links in this time window.")
            return links
            
        print("No links found in this time window. Expanding time parameters...")
        time.sleep(3) 
        
    print("No jobs found even after expanding the search to the past 72 hours.")
    return []

def evaluate_job_description(job_url: str) -> dict:
    # 3. The Conceptual "Applied AI" Framework Prompt
    evaluation_prompt = """
    You are an expert Technical Technical Recruiter. Your task is to evaluate this job posting against a highly specific candidate profile: an 'Applied AI Automation Engineer'. 
    This candidate specializes in connecting LLMs, AI agents, and Machine Learning models to actual backend operational workflows. They do not just do theoretical data research; they build systems that execute business logic.

    Evaluate if the job aligns with ANY of the following four core application domains:
    1. CRM & Customer Service Automation: Building systems (like multi-agent orchestrations) to handle support queues, route tickets, manage real-time tracking, or interact with CRMs.
    2. AdTech, PPC, & Social Media: Processing marketing/retail data, optimizing ad-spend, calculating ROAS, identifying SKU anomalies, or generating automated multimodal marketing creatives.
    3. FinTech & Accounting Data: Automating backend financial reconciliation, extracting data from invoices (PDF parsing), or cross-validating sales data against internal Purchase Orders (POs) and APIs.
    4. General Business Operations Automation: Creating internal AI workflows or agentic tools that directly improve the speed, accuracy, or capability of a company's internal teams.

    Rigorously evaluate the job description against these rules:
    1. Sponsorship Constraint: If the posting explicitly states 'will not sponsor', 'no visa sponsorship provided', or 'requires current US citizenship/Green Card without exception', you MUST mark 'is_match' as false.
    2. Relaxed Experience Constraint: The role targets early-career to mid-level professionals (0 to 2 years of experience). If it strictly demands 4+ years, 5+ years, or is labeled 'Senior', 'Staff', 'Principal', or 'Lead', you MUST mark 'is_match' as false.
    3. Domain Alignment Constraint: The role MUST involve applying AI, ML, or Data Science to at least one of the four business domains listed above. If it is a generic data engineering role (just building data lakes), a pure academic AI research role, or a standard business analyst role making Tableau dashboards without building AI/automated systems, you MUST mark 'is_match' as false.

    Output Format:
    Return exactly one JSON object with these keys:
    - "title": Job title
    - "company": Company name
    - "salary_range": Stated base range (or 'Not Listed')
    - "experience_required": Exact experience text from the posting
    - "posted_date": Posted timing (e.g., '3 days ago', '1 day ago')
    - "is_match": true or false
    - "reason": Detailed explanation specifying exactly which operational domain the job aligns with, or precisely why the constraints forced a rejection.
    """
    
    scraper = SmartScraperGraph(prompt=evaluation_prompt, source=job_url, config=graph_config)
    try:
        result = scraper.run()
        if isinstance(result, dict):
            result["url"] = job_url
        return result
    except Exception as e:
        return {"error": str(e), "url": job_url, "is_match": False}

def display_and_rank_saved_jobs():
    conn = sqlite3.connect("matched_jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, company, salary_range, experience_required, posted_date, url, reason FROM jobs")
    rows = cursor.fetchall()
    conn.close()
    
    def parse_recency(row):
        text = row[4].lower()
        if "hour" in text or "minute" in text or "just now" in text:
            return 0
        if "day" in text:
            try:
                return int([int(s) for s in text.split() if s.isdigit()][0])
            except IndexError:
                return 1
        return 99

    sorted_rows = sorted(rows, key=parse_recency)
    
    print("\n--- Final Filtered and Ranked Job Listings (Top Matches) ---\n")
    for idx, row in enumerate(sorted_rows[:10], 1):
        print(f"Rank: {idx}")
        print(f"Title: {row[0]} | Company: {row[1]}")
        print(f"Salary: {row[2]} | Experience: {row[3]}")
        print(f"Posted: {row[4]}")
        print(f"URL: {row[5]}")
        print(f"Reasoning: {row[6]}")
        print("-" * 50)

if __name__ == "__main__":
    init_db()
    
    raw_links = get_job_links_with_fallback()
    
    if not raw_links:
        print("Pipeline finished: No URLs to evaluate.")
    else:
        MAX_SEARCH_LIMIT = 50
        target_links = raw_links[:MAX_SEARCH_LIMIT]
        print(f"Budget limited optimization to processing top {len(target_links)} links.")
        
        match_count = 0
        max_matches_needed = 10
        
        for url in target_links:
            if match_count >= max_matches_needed:
                print("Successfully accumulated 10 new high-precision matches. Stopping pipeline.")
                break
                
            if not url.startswith("http"):
                continue
                
            if is_already_processed(url):
                print(f"Skipping already evaluated URL: {url}")
                continue
                
            print(f"Analyzing new listing: {url}")
            evaluation = evaluate_job_description(url)
            
            log_processed_url(url)
            
            if evaluation.get("is_match") is True:
                print(f"Match approved: {evaluation.get('title')} at {evaluation.get('company')}")
                save_job_to_db(evaluation)
                match_count += 1
            else:
                print(f"Rejected: {evaluation.get('reason')}")
                
            time.sleep(4)
            
        display_and_rank_saved_jobs()