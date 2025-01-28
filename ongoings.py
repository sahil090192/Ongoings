import requests
import pandas as pd
from typing import List, Dict
from openai import OpenAI
import os

class TwitterFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.socialdata.tools"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_user_id(self, username: str) -> str:
        username = username.replace('@', '').strip()
        endpoint = f"{self.base_url}/twitter/user/{username}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            if response.status_code == 404:
                print(f"User @{username} not found. Please check the username and try again.")
                return None
            response.raise_for_status()
            user_data = response.json()
            return user_data.get('id')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user ID for @{username}: {str(e)}")
            return None

    def get_user_tweets(self, username: str) -> List[Dict]:
        user_id = self.get_user_id(username)
        if not user_id:
            return []
        
        endpoint = f"{self.base_url}/twitter/user/{user_id}/tweets"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            tweets = data.get('tweets', [])
            return tweets
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tweets for @{username}: {str(e)}")
            print("Please verify the username and your API key are correct.")
            return []

def get_user_handles() -> List[str]:
    handles = []
    print("Enter Twitter handles (one per line, press Enter twice to finish):")
    
    while True:
        handle = input().strip()
        if not handle:
            break
        handles.append(handle.lstrip('@'))
    
    return handles

def save_tweets_to_csv(tweets_by_user: Dict[str, List[Dict]], filename: str = "tweets.csv"):
    all_tweets = []
    for username, tweets in tweets_by_user.items():
        for tweet in tweets:
            if isinstance(tweet, dict):
                tweet_data = {
                    "username": username,
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

def analyze_tweets_with_gpt4(df: pd.DataFrame) -> str:
    """
    Analyze tweet patterns using GPT-4 for each user in the DataFrame
    """
    client = OpenAI(
        api_key='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'  # Replace with your actual OpenAI API key
    )
    
    # Group tweets by username
    analyses = []
    for username, user_tweets in df.groupby('username'):
        # Combine all tweets for this user
        all_tweets = user_tweets['text'].tolist()
        tweet_text = "\n".join([f"Tweet {i+1}: {tweet}" for i, tweet in enumerate(all_tweets)])
        
        try:
            print(f"\nAnalyzing tweets for @{username}...")
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an advanced AI trained to analyze text and uncover patterns, themes, and behavioral insights. You will be analyzing tweets from a single Twitter user. Your task is to go beyond surface-level observations and generate incisive, surprising, and insightful analyses that reveal the user's interests, personality traits, values, and potential future behavior."
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Analyze the following tweets from user @{username} and provide insights about:
                        Objectives:

                        Themes & Topics: Identify recurring topics, themes, and subjects of interest in the user's tweets. Highlight surprising or unexpected patterns.
                        Tone & Personality: Analyze the tone, style, and emotional undertone of their tweets (e.g., optimistic, sarcastic, informative, reflective). Infer personality traits and social tendencies based on the tone.
                        Behavioral Patterns: Look for behavioral patterns, such as posting frequency, times of activity, types of content shared (e.g., original posts, replies, retweets), and the use of specific language or hashtags.
                        Values & Priorities: Deduce the user's priorities, values, or what they care about most based on the topics and opinions they express.
                        Engagement Style: Assess how they interact with others (if applicable), including their conversational style, preferred topics of discussion, and whether they are more of a broadcaster or an engager.
                        Surprising Observations: Highlight uncommon or hidden connections within their tweets (e.g., subtle shifts in opinion, changes in topics over time, unique language quirks).
                        Predictive Analysis: Predict future themes, topics, or behaviors the user might explore based on historical data. For example, forecast their potential interests or how their focus might evolve.
                        Output: Organize your insights into the following structure:

                        Key Themes and Patterns: A summary of what the user tweets about most and what stands out.
                        Personality Profile: Inferred personality traits and behaviors with examples from tweets.
                        Aha! Insights: Unusual or unexpected observations about the user's tweeting habits or interests.
                        Predictions: Data-backed predictions about how the users behavior or interests might change in the future.
                        Provide clear, specific, and thought-provoking insights in your response, ensuring it is detailed enough to provoke meaningful "aha!" moments. Use examples from the input tweets to support your analysis. 

                        Tweets:
                        {tweet_text}

                        Please provide a concise but comprehensive analysis.
                        """
                    }
                ]
            )
            
            analysis = completion.choices[0].message.content
            analyses.append(f"\nAnalysis for @{username}:\n{analysis}\n{'='*50}")
            
        except Exception as e:
            print(f"Error analyzing tweets for @{username}: {str(e)}")
            analyses.append(f"\nError analyzing tweets for @{username}")
    
    return "\n".join(analyses)

def main():
    fetcher = TwitterFetcher("2013|ts7ojeD23o1QTVXgi0UbVSEq01y2VNEmYXg5wW6v23cfde4f")
    handles = get_user_handles()
    
    tweets_by_user = {}
    for handle in handles:
        tweets = fetcher.get_user_tweets(handle)
        tweets_by_user[handle] = tweets
        print(f"Fetched {len(tweets)} tweets for @{handle}")

    df = save_tweets_to_csv(tweets_by_user)
    
    # Run GPT-4 analysis
    try:
        analysis = analyze_tweets_with_gpt4(df)
        print("\nGPT-4 Analysis of Tweet Patterns:")
        print(analysis)
        
        # Save analysis to file
        with open("tweet_analysis.txt", "w", encoding="utf-8") as f:
            f.write(analysis)
        print("\nAnalysis saved to tweet_analysis.txt")
        
    except Exception as e:
        print(f"\nError during GPT-4 analysis: {str(e)}")
    
    return df

if __name__ == "__main__":
    main()