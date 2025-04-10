from praw import Reddit
import json
import string
import re
import pandas as pd
from datetime import datetime
import csv

def initialize():
    # Initialize reddit session
    with open('../reddit-auth.txt', 'r') as file:
        content = file.read()
    
    reddit_auth = json.loads(content)
  
    reddit = Reddit(
        client_id = reddit_auth['client ID'],
        client_secret = reddit_auth['client secret'],
        user_agent = reddit_auth['user agent']
    )

    return reddit

def get_flair(topic):
    """
    Extract submission flair

    Inputs:
    - topic: praw.models.Submission

    Outputs:
    - flair: Tag of submission if exists. If no tag, returns None
    """
    return topic.link_flair_text

def extract_urls(text):
    # Regex pattern to find URLs inside parentheses
    pattern = r'\((https?://[^\s)]+)\)'
    url_list = re.findall(pattern, text)
    
    if len(url_list) == 0:
        return None
    
    for url in url_list:
        if "arxiv.org" in url:
            return [url]
        
    for url in url_list:
        if "github" in url:
            return [url]
    
    for url in url_list:
        if "hugging" in url:
            return [url]
        
    return [url_list[0]]

def extract_topic(topic):
    """
    Extract useful data from a submission

    Inputs:
    - topic: praw.models.Submission

    Outputs:
    - title: Title of submission
    - text: Plain text of submission 
    """

    title = topic.title
    text = topic.selftext
    links = extract_urls(text)

    return title, text, links

def scrape_subreddit(reddit, sub_name, sort='hot', limit = None, filter_flairs=["Research", "New Model"]):
    """
    Input:
    - reddit: praw.Reddit scraper
    - sub_name: Name of the subreddit to scrape
    - sort: Rank submissions by top or hot before extraction
    - limit: Number of submission to consider
    - filter_flairs: Filter submissions wrt a list of flairs
    """

    # Set to store unique topics
    topics = list()

    # Choosing if we look for the top entries or hot entries
    if sort == 'hot':
        submissions = reddit.subreddit(sub_name).hot(limit=limit)
    else:
        submissions = reddit.subreddit(sub_name).top(time_filter='week',limit=limit)
    
    # Looping on the submissions
    for submission in submissions:
        
        topic = {}
        flair = get_flair(submission)
        # We extract the topic if the flair is in the filters
        if flair in filter_flairs:
            title, text, links = extract_topic(submission)
            topic['title'] = title
            topic['text'] = text
            topic['links'] = links
            if topic['links']:
                topics.append(topic)
    
    return topics


def get_entries_from_reddit():

    # Initialize scraper
    reddit = initialize()

    # List of subreddits to look for
    subreddits = ['MachineLearning','LocalLLaMA']

    topics = []
    for subreddit in subreddits:
        topics.extend(scrape_subreddit(reddit,subreddit,limit=50))

    return topics

def update_csv_from_reddit(csv_file):
    topics = get_entries_from_reddit()
    today = datetime.today().strftime("%d/%m/%Y")

    # Lecture des colonnes du csv
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        headers = next(reader)

    blank_columns = [''] * (len(headers) - 2)

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        #writer.writerow(headers)
        for topic in topics:
            writer.writerow([today,topic['links'][0]] + blank_columns)

if __name__ == "__main__":
    update_csv_from_reddit('./output/reddit.csv')