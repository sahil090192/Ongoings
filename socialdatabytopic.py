import requests
import pandas as pd
from typing import List, Dict
from openai import OpenAI
import os
from datetime import datetime, timedelta

class SocialDataTwitterSearcher:
    def __init__(self):
        self.api_key = os.getenv('SOCIALDATA_API_KEY')
        if not self.api_key:
            raise ValueError("Please set the SOCIALDATA_API_KEY environment variable")
        self.base_url = "https://api.socialdata.tools"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def search_tweets_by_query(self, query: str, days: int = 7) -> List[Dict]:
        # Calculate the date range for the query
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        # Include the date range in the query
        query_with_date = f"{query} since:{start_date_str}"
        
        endpoint = f"{self.base_url}/twitter/search"
        params = {
            "query": query_with_date,
            "type": "latest"
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            tweets = data.get('tweets', [])
            return tweets
        except requests.exceptions.RequestException as e:
            print(f"Error searching tweets with query '{query}': {str(e)}")
            return []

def get_search_terms_and_days() -> List[Dict[str, int]]:
    search_terms = []
    print("Enter search queries and the number of past days (e.g., 'deepseek 7'):")
    print("Press Enter twice to finish:")
    
    while True:
        input_line = input().strip()
        if not input_line:
            break
        parts = input_line.split()
        if len(parts) == 2 and parts[1].isdigit():
            search_terms.append({"query": parts[0], "days": int(parts[1])})
        else:
            print("Invalid input. Please enter in the format 'query days'.")
    
    return search_terms

def save_search_results_to_csv(tweets_by_term: Dict[str, List[Dict]], filename: str = "search_results.csv"):
    all_tweets = []
    for term, tweets in tweets_by_term.items():
        for tweet in tweets:
            if isinstance(tweet, dict):
                tweet_data = {
                    "search_term": term,
                    "tweet_id": tweet.get('id'),
                    "text": tweet.get('text', '') or tweet.get('full_text', ''),
                    "created_at": tweet.get('created_at'),
                    "likes": tweet.get('favorite_count', 0)
                }
                all_tweets.append(tweet_data)

    df = pd.DataFrame(all_tweets)
    df.to_csv(filename, index=False)
    print(f"\nTweets saved to {filename}")
    print("\nFirst 5 rows of the DataFrame:")
    print(df.head())
    return df

def analyze_search_results_with_gpt4(df: pd.DataFrame) -> str:
    """
    Analyze tweet patterns using GPT-4 for each search term in the DataFrame
    """
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")
    
    client = OpenAI(api_key=openai_api_key)
    
    # Group tweets by search term
    analyses = []
    for term, term_tweets in df.groupby('search_term'):
        # Combine all tweets for this term
        all_tweets = term_tweets['text'].tolist()
        tweet_text = "\n".join([f"Tweet {i+1}: {tweet}" for i, tweet in enumerate(all_tweets)])
        
        try:
            print(f"\nAnalyzing tweets for search term '{term}'...")
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional summarizer and presenter specializing in creating engaging, concise, and informative digests from social media data. Your task is to analyze a set of tweets related to a given topic or keyword and reproduce them along with a insightful take on said tweets."
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Analyze the following tweets from the search term '{term}' and reproduce them along with insightful (and funny) takes on them:

                        move tweet by tweet and reproduce it in a polished fashion, add your own insightful take to go along and where necessary bring forth humor to bear as well.
                        """
                    }
                ]
            )
            
            analysis = completion.choices[0].message.content
            analyses.append(f"\nAnalysis for search term '{term}':\n{analysis}\n{'='*50}")
            
        except Exception as e:
            print(f"Error analyzing tweets for search term '{term}': {str(e)}")
            analyses.append(f"\nError analyzing tweets for search term '{term}'")
    
    return "\n".join(analyses)

def main():
    searcher = SocialDataTwitterSearcher()
    search_terms = get_search_terms_and_days()
    
    tweets_by_term = {}
    for term_info in search_terms:
        query = term_info["query"]
        days = term_info["days"]
        tweets = searcher.search_tweets_by_query(query, days)
        tweets_by_term[query] = tweets
        print(f"Fetched {len(tweets)} tweets for search term '{query}' over the past {days} days")

    df = save_search_results_to_csv(tweets_by_term)
    
    # Run GPT-4 analysis
    try:
        analysis = analyze_search_results_with_gpt4(df)
        print("\nGPT-4 Analysis of Tweet Patterns:")
        print(analysis)
        
        # Save analysis to file
        with open("search_analysis.txt", "w", encoding="utf-8") as f:
            f.write(analysis)
        print("\nAnalysis saved to search_analysis.txt")
        
    except Exception as e:
        print(f"\nError during GPT-4 analysis: {str(e)}")
    
    return df

if __name__ == "__main__":
    main()