from praw import Reddit
import json
import string
import re

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
    return re.findall(pattern, text)


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

def scrape_subreddit(sub_name, sort='top', limit = None, filter_flairs=["Research"]):
    """
    Input:
    - sub_name: Name of the subreddit to scrape
    - sort: Rank submissions by top or hot before extraction
    - limit: Number of submission to consider
    - filter_flairs: Filter submissions wrt a list of flairs
    """

    # Initialize reddit session
    with open('../reddit-auth.txt', 'r') as file:
        content = file.read()
    
    reddit_auth = json.loads(content)
  
    reddit = Reddit(
        client_id = reddit_auth['client ID'],
        client_secret = reddit_auth['client secret'],
        user_agent = reddit_auth['user agent']
    )

    # Set to store unique topics
    topics = list()

    # Loop on the topics and extract useful data
    for submission in reddit.subreddit(sub_name).hot(limit=limit):

        topic = {}

        flair = get_flair(submission)

        # We extract the topic if the flair is in the filters
        if flair in filter_flairs:
            title, text, links = extract_topic(submission)
            topic['title'] = title
            topic['text'] = text
            topic['links'] = links
            topics.append(topic)

scrape_subreddit('MachineLearning',limit=5)