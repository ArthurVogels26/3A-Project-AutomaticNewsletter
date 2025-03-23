import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import re

def update_csv_from_huggingface(csv_file,max_papers=10, main_page_id="week/2025-W12"):
    headers = {"User-Agent": "Mozilla/5.0"}
    main_page_url="https://huggingface.co/papers/"+main_page_id

    print(f"Fetching page: {main_page_url}...")

    response = requests.get(main_page_url, headers=headers)

    # Check for request success
    if response.status_code != 200:
        print(f"⚠️ Failed to fetch page (Status Code: {response.status_code})")
        return

    print("✅ Successfully fetched page.")

    soup = BeautifulSoup(response.text, "html.parser")

    # limit to max_papers
    paper_links = set()
    arxiv_pattern = re.compile(r"\d+\.\d+$")

    for a in soup.select("a[href^='/papers/']"):
        paper_url = "https://huggingface.co" + a["href"]
        
        # Extract the last part of the URL (arxiv ID) and check if it contains only digits
        arxiv_id = paper_url.split("/")[-1] 
        if arxiv_pattern.search(arxiv_id):
            paper_links.add(paper_url)

        if len(paper_links) >= max_papers:
            break

    print(f"🔎 Found {len(paper_links)} paper links.")

    # Extract ArXiv IDs directly from Hugging Face paper URLs
    arxiv_ids = [paper_url.split("/")[-1] for paper_url in paper_links] 

    today = datetime.today().strftime("%d/%m/%Y")

    existing_urls = set()

    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            existing_urls.add(row[1])

    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        headers = next(reader)
        blank_columns = [''] * (len(headers) - 2)

    # Open the CSV for appending updated data
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Write the ArXiv links to CSV only if they don't already exist
        for arxiv_id in arxiv_ids:
            paper_url = f"https://arxiv.org/abs/{arxiv_id}"

            if paper_url not in existing_urls:
                writer.writerow([today, paper_url] + blank_columns)
                existing_urls.add(paper_url)


    print("\n💾 Updated CSV with paper links.")
