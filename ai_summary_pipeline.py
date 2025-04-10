import os
import pandas as pd
import csv
from processing.data_extractor import DataExtractor
from processing.data_classifier import DataClassifier
from summarization.summarizerAgent import generate_summary, classify_document
from summarization.evaluate_rouge import evaluate_summary_with_original
from scraping.huggingface_automatic_scraping import update_csv_from_huggingface
from scraping.reddit_scraping import update_csv_from_reddit

# Constants for configuration
SCRAP_REDDIT=True
SCRAP_HUGGINGFACE=True
INPUT_FILE = "./output/new_summaries.csv"
# INPUT_FILE = "./output/AI takeaways benchmark.csv" ##used for evaluation only
CALCULATE_ROUGE = False  # used for evaluation only
HUGGINGFACE_MAIN_PAGE_ID = "week/2025-W12" # month/2025-03 for March 2025 or week/2025-W12 for week 12 of 2025
headers = ['Reception date','Link','Review priority','Category (Illuin)','Category AI','Status','Reviewed','Topic / Keywords (Illuin)','Topic / Keywords AI','Take-away (Illuin)','Take-away AI','rouge1 precision','rouge2 precision','rougeL precision']
#automatic scraping
def scrape_data():
    # Create file Headers
    new_file = 0
    with open(INPUT_FILE, mode='r', newline='') as file:
        reader = csv.reader(file)
        if next(reader,None) == None:
            new_file = 1
    
    if new_file:
        with open(INPUT_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

    if SCRAP_HUGGINGFACE:
        update_csv_from_huggingface(INPUT_FILE, max_papers=20, main_page_id=HUGGINGFACE_MAIN_PAGE_ID)

    if SCRAP_REDDIT:
        update_csv_from_reddit(INPUT_FILE)

# Function to process a document
def process_document(row, extractor, classifier):
    url_or_id = row["Link"]
    print(f"Processing document: {url_or_id}")
    data = extractor.extract(url_or_id).to_dict()
    category_ai, _ = classify_document(data)
    print(f"Detected AI category: {category_ai}")
    take_away_ai, _ = generate_summary(data)
    print(f"Generated AI Take-away.")

    return category_ai, take_away_ai

# Function to process multiple documents in the dataframe
def process_documents(df, extractor, classifier):
    df_to_process = df[df["Take-away AI"].isna() | df["Take-away AI"].eq("")]
    if df_to_process.empty:
        print("No new documents to process.")
    else:
        print(f"Processing {len(df_to_process)} documents...")
    for index, row in df_to_process.iterrows():
        try:
            category_ai, take_away_ai = process_document(row, extractor, classifier)
            df.at[index, "Category AI"] = category_ai
            df.at[index, "Status"] = "Processed"
            df.at[index, "Take-away AI"] = take_away_ai
        except Exception as e:
            print(f"Error processing {row['Link']}: {e}")
            df.at[index, "Status"] = f"Error: {e}"

    return df

def calculate_rouge_scores(df):
    df_to_evaluate = df[
        (df["rouge1 precision"].isna() | df["rouge1 precision"].eq("")) & 
        (~df["Take-away AI"].isna()) & df["Take-away AI"].ne("")
    ]
    if df_to_evaluate.empty:
        print("No ROUGE scores to calculate.")
    else:
        print(f"{len(df_to_evaluate)} entries need ROUGE scores.")
        for index, row in df_to_evaluate.iterrows():
            if pd.isna(row["Take-away AI"]) or pd.isna(row["Take-away (Illuin)"]):
                continue
            rouge_scores = evaluate_summary_with_original(row["Take-away AI"], row["Take-away (Illuin)"])
            df.at[index, "rouge1 precision"] = round(float(rouge_scores["rouge1_precision"]), 4)
            df.at[index, "rouge2 precision"] = round(float(rouge_scores["rouge2_precision"]), 4)
            df.at[index, "rougeL precision"] = round(float(rouge_scores["rougeL_precision"]), 4)
        print("ROUGE scores calculated and added to the file.")
    
    return df

### Generating the AI Summaries
def generate_summaries(input_file=INPUT_FILE, calculate_rouge=CALCULATE_ROUGE):
    """Main function to process and summarize documents."""
    if os.path.exists(input_file):
        df = pd.read_csv(input_file)
    else:
        raise FileNotFoundError(f"File not found: {input_file}")

    extractor = DataExtractor()
    classifier = DataClassifier()

    df = process_documents(df, extractor, classifier)

    if calculate_rouge:
        df = calculate_rouge_scores(df)

    return df

def main():
    """Main execution flow for scraping, processing, and saving results."""
    scrape_data()
    df = generate_summaries(INPUT_FILE)
    df.to_csv(INPUT_FILE, index=False)
    print("✅ Update complete! File saved.")


if __name__ == "__main__":
    main()