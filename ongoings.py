import requests
from datetime import datetime, timedelta
import os
from typing import List, Dict
import time
import pyttsx3  # Replace pipecat
import pandas as pd  # Import pandas for CSV handling

class TwitterFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.socialdata.tools"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_user_id(self, username: str) -> str:
        # Remove any @ symbol and clean the username
        username = username.replace('@', '').strip()
        endpoint = f"{self.base_url}/twitter/user/{username}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            if response.status_code == 404:
                print(f"User @{username} not found. Please check the username and try again.")
                return None
            response.raise_for_status()
            user_data = response.json()
            print(f"User data: {user_data}")  # Debug print
            return user_data.get('id')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user ID for @{username}: {str(e)}")
            return None

    def get_user_tweets(self, username: str) -> List[Dict]:
        user_id = self.get_user_id(username)
        print(f"Got user ID: {user_id}")  # Debug print
        if not user_id:
            return []
        
        # Verify the correct endpoint for fetching tweets by user ID
        endpoint = f"{self.base_url}/twitter/user/{user_id}/tweets"  # Adjusted endpoint
        
        print(f"Requesting tweets for user ID: {user_id}")  # Debug print
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            print(f"Response status: {response.status_code}")  # Debug print
            response.raise_for_status()
            data = response.json()
            print(f"Full response data: {data}")  # Debug print
            
            # Assuming the response is a dictionary with a 'tweets' key
            tweets = data.get('tweets', [])
            print(f"Extracted tweets: {tweets}")  # Debug print
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

def read_tweets(tweets_by_user: Dict[str, List[Dict]]):
    engine = pyttsx3.init()  # Initialize the TTS engine
    for username, tweets in tweets_by_user.items():
        print(f"\nReading tweets for @{username}")
        for tweet in tweets:
            if isinstance(tweet, dict):  # Ensure tweet is a dictionary
                print(f"Tweet data: {tweet}")  # Debug print to inspect tweet structure
                text = tweet.get('text', '')  # Attempt to get the 'text' field
                if not text:
                    print("No text found in tweet, checking for other fields...")  # Debug print
                    # Check for other possible fields
                    text = tweet.get('full_text', '')  # Try 'full_text' if 'text' is not available
                print(f"Tweet: {text}")
                engine.say(text)  # Use pyttsx3 instead of pipecat
                engine.runAndWait()  # Wait for the speech to complete
                time.sleep(1)  # Add a small pause between tweets
            else:
                print("Unexpected tweet format:", tweet)

def save_tweets_to_csv(tweets_by_user: Dict[str, List[Dict]], filename: str = "tweets.csv"):
    # Flatten the tweets data into a list of dictionaries
    all_tweets = []
    for username, tweets in tweets_by_user.items():
        for tweet in tweets:
            if isinstance(tweet, dict):  # Ensure tweet is a dictionary
                # Debug print to inspect tweet structure
                print(f"Tweet data for CSV: {tweet}")
                
                # Attempt to get the 'text' field, or 'full_text' if available
                text = tweet.get('text', '') or tweet.get('full_text', '')
                
                tweet_data = {
                    "username": username,
                    "tweet_id": tweet.get('id'),
                    "text": text,
                    "created_at": tweet.get('created_at')
                }
                all_tweets.append(tweet_data)
            else:
                print(f"Unexpected tweet format for @{username}: {tweet}")  # Debug print

    # Create a DataFrame and save to CSV
    df = pd.DataFrame(all_tweets)
    df.to_csv(filename, index=False)
    print(f"Tweets saved to {filename}")
    
    # Display the first 5 rows of the CSV
    print("\nFirst 5 rows of the CSV:")
    print(df.head(5))

def main():
    # Use your socialdata.tools API key directly
    api_key = "2009|vzXUBmnBqLs3ca3oPX4U38WRfhU4bJ9tiyRZQNVobeca0361"
    
    fetcher = TwitterFetcher(api_key)
    handles = get_user_handles()
    
    tweets_by_user = {}
    for handle in handles:
        tweets = fetcher.get_user_tweets(handle)
        tweets_by_user[handle] = tweets
        print(f"Fetched {len(tweets)} tweets for @{handle}")
    
    save_tweets_to_csv(tweets_by_user)  # Save tweets to CSV
    read_tweets(tweets_by_user)
    

if __name__ == "__main__":
    main()
