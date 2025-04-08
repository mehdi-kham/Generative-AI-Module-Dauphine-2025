import pandas as pd
import numpy as np
from openai import OpenAI
import configparser
import json

class RAGEngine:
    def __init__(self):
        # Load OpenAI API key
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.client = OpenAI(api_key=config.get('OPENAI_API', 'OPENAI_KEY'))
        
        # Load data and embeddings
        self.load_data()
    
    def load_data(self):
        """Load tweet data and their embeddings"""
        # Load original data
        self.data = pd.read_csv("data/twitter_data_clean_sample.csv")
        
        try:
            # Try to load pre-computed embeddings
            self.embeddings_df = pd.read_excel("data/embeddings.xlsx")
            self.embeddings = np.array(json.loads(self.embeddings_df['embedding'].tolist()))
        except (FileNotFoundError, KeyError):
            print("No pre-computed embeddings found. Computing new embeddings...")
            self.compute_and_save_embeddings()
    
    def compute_and_save_embeddings(self):
        """Compute embeddings for all customer tweets and save them"""
        print("Computing embeddings for all tweets...")
        embeddings = []
        
        for tweet in self.data['customer_tweet']:
            embedding = self.get_embedding(tweet)
            embeddings.append(embedding)
        
        # Save embeddings
        self.embeddings = np.array(embeddings)
        embeddings_json = [json.dumps(emb.tolist()) for emb in embeddings]
        
        self.embeddings_df = pd.DataFrame({
            'customer_tweet': self.data['customer_tweet'],
            'embedding': embeddings_json
        })
        
        self.embeddings_df.to_excel("data/embeddings.xlsx", index=False)
        print("Embeddings computed and saved successfully!")
    
    def get_embedding(self, text, model="text-embedding-3-small"):
        """Get OpenAI embedding for a text"""
        text = text.replace("\\n", " ")
        return self.client.embeddings.create(input=[text], model=model).data[0].embedding
    
    def find_similar_tweets(self, query, top_k=3):
        """Find most similar tweets to the query"""
        # Get query embedding
        query_embedding = self.get_embedding(query)
        
        # Calculate cosine similarities
        similarities = self.cosine_similarity(query_embedding, self.embeddings)
        
        # Get top k similar tweets
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'customer_tweet': self.data.iloc[idx]['customer_tweet'],
                'company_tweet': self.data.iloc[idx]['company_tweet'],
                'company': self.data.iloc[idx]['company'],
                'similarity': similarities[idx]
            })
        
        return results
    
    @staticmethod
    def cosine_similarity(a, b):
        """Calculate cosine similarity between a vector and a matrix of vectors"""
        if len(b.shape) == 1:
            b = b.reshape(1, -1)
        return np.dot(a, b.T) / (np.linalg.norm(a) * np.linalg.norm(b, axis=1))
    
    def generate_response(self, customer_message, company, similar_tweets):
        """Generate response using GPT with similar tweets as context"""
        # Create prompt with similar tweets as examples
        examples = ""
        for tweet in similar_tweets:
            examples += f"Customer: {tweet['customer_tweet']}\n"
            examples += f"Agent: {tweet['company_tweet']}\n\n"
        
        prompt = f"""You are a customer service agent for {company}. 
Use these similar conversation examples to guide your response style and tone:

{examples}
Now, please respond to this customer message in a similar style:
Customer: {customer_message}

Response:"""
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        return response.choices[0].message.content 