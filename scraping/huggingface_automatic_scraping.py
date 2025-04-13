import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import re
from processing.data_extractor import DataExtractor

extractor=DataExtractor()

def get_entries_from_huggingface(max_papers=10, main_page_id="week/2025-W12"):
    """
    Fetches latest HuggingFace papers from the specified weekly page
    and returns a list of structured article data.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    main_page_url = f"https://huggingface.co/papers/{main_page_id}"

    response = requests.get(main_page_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch HuggingFace page (status code {response.status_code})")

    soup = BeautifulSoup(response.text, "html.parser")
    arxiv_pattern = re.compile(r"\d+\.\d+$")
    results = []
    seen_ids = set()

    for a in soup.select("a[href^='/papers/']"):
        relative_link = a["href"]
        arxiv_id = relative_link.split("/")[-1]

        if arxiv_pattern.search(arxiv_id) and arxiv_id not in seen_ids:
            seen_ids.add(arxiv_id)

            try:
                if extractor:
                    data = extractor.extract_arxiv(arxiv_id)
                else:
                    # Minimal fallback
                    data = {
                        "title": a.text.strip(),
                        "content": "",
                        "metadata": {"arxiv_id": arxiv_id}
                    }
                results.append(data)
            except Exception as e:
                print(f"❌ Failed to extract ArXiv {arxiv_id}: {e}")

            if len(results) >= max_papers:
                break

    return results

def update_csv_from_huggingface(csv_file, max_papers=10, main_page_id="week/2025-W12"):
    """
    Fetch new HuggingFace paper links and append new ArXiv links to the CSV.
    Preserves the original function name and logic, but uses get_entries_from_huggingface internally.
    """
    print(f"Fetching page: https://huggingface.co/papers/{main_page_id}...")

    try:
        entries = get_entries_from_huggingface(max_papers=max_papers, main_page_id=main_page_id)
    except Exception as e:
        print(f"⚠️ Error fetching HuggingFace papers: {e}")
        return

    print(f"✅ Successfully fetched {len(entries)} entries.")

    today = datetime.today().strftime("%d/%m/%Y")
    arxiv_urls = [entry["links"][0] for entry in entries]

    existing_urls = set()

    # Read existing CSV to track duplicates
    try:
        with open(csv_file, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                existing_urls.add(row[1])
    except FileNotFoundError:
        print("🆕 CSV file does not exist yet. It will be created.")
        existing_urls = set()

    # Read headers to know how many blank columns to fill
    try:
        with open(csv_file, mode='r', newline='') as file:
            reader = csv.reader(file)
            headers = next(reader)
            blank_columns = [''] * (len(headers) - 2)
    except FileNotFoundError:
        headers = ["date", "url"]
        blank_columns = []

    # Write new rows
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        for url in arxiv_urls:
            if url not in existing_urls:
                writer.writerow([today, url] + blank_columns)
                existing_urls.add(url)

    print("💾 Updated CSV with new paper links.")
    