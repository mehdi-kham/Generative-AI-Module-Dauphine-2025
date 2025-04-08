import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import openai
from openai import OpenAI
import configparser
import os

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')
OPENAI_KEY = config.get('OPENAI_API', 'OPENAI_KEY')

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_KEY)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load and sample 20% of the data
data = pd.read_csv("data/twitter_data_clean_sample.csv")
data_sample = data.sample(frac=0.2, random_state=42)  # Take 20% of the data

# Function to get embeddings
def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

# Function to compute cosine similarity
def cosine_similarity(A, B):
    dot_product = np.dot(A, B)
    magnitude_A = np.linalg.norm(A)
    magnitude_B = np.linalg.norm(B)
    return dot_product / (magnitude_A * magnitude_B)

# Precompute embeddings for the sample
print("Computing embeddings for sample tweets...")
data_sample['embedding'] = data_sample['customer_tweet'].apply(get_embedding)
print("Embeddings computed successfully!")

@app.route('/')
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Twitter Response Generator</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .container {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            textarea {
                width: 100%;
                height: 100px;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            button {
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #0056b3;
            }
            .result {
                border: 1px solid #ccc;
                padding: 20px;
                border-radius: 4px;
                margin-top: 20px;
            }
            .similarity {
                color: #666;
                font-style: italic;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Twitter Response Generator</h1>
            <div>
                <label for="tweet">Enter your tweet:</label>
                <textarea id="tweet" placeholder="Type your tweet here..."></textarea>
            </div>
            <div>
                <label for="company">Company:</label>
                <input type="text" id="company" value="Amazon" placeholder="Company name">
            </div>
            <button onclick="generateResponse()">Generate Response</button>
            <div id="result" class="result" style="display: none;">
                <h3>Generated Response:</h3>
                <p id="response"></p>
                <h4>Similar Tweet:</h4>
                <p id="similar_tweet"></p>
                <h4>Similar Response:</h4>
                <p id="similar_response"></p>
                <p class="similarity">Similarity Score: <span id="similarity_score"></span></p>
            </div>
        </div>

        <script>
            async function generateResponse() {
                const tweet = document.getElementById('tweet').value;
                const company = document.getElementById('company').value;
                
                try {
                    const response = await fetch('/generate_response', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ tweet, company }),
                    });
                    
                    const data = await response.json();
                    
                    document.getElementById('response').textContent = data.response;
                    document.getElementById('similar_tweet').textContent = data.similar_tweet;
                    document.getElementById('similar_response').textContent = data.similar_response;
                    document.getElementById('similarity_score').textContent = data.similarity_score;
                    document.getElementById('result').style.display = 'block';
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred while generating the response.');
                }
            }
        </script>
    </body>
    </html>
    """
    return html

@app.route('/generate_response', methods=['POST'])
def generate_response():
    try:
        data = request.json
        tweet = data.get('tweet')
        company = data.get('company', 'Amazon')  # Default to Amazon if not specified

        # Get embedding for the input tweet
        tweet_embedding = get_embedding(tweet)

        # Find most similar tweet
        similarities = data_sample['embedding'].apply(lambda x: cosine_similarity(tweet_embedding, x))
        most_similar_idx = similarities.idxmax()
        similar_tweet = data_sample.loc[most_similar_idx, 'customer_tweet']
        similar_response = data_sample.loc[most_similar_idx, 'company_tweet']
        similarity_score = similarities.max()

        # Generate response using the similar example
        instruction = f"""You are a chatbot answering customer's tweet. You are working for a company called {company}. 
You are provided with an example of a similar interaction between a customer and an agent. Reply to the customer's tweet in the same tone, structure and style than the provided example.

#####
Example :
Customer : "{similar_tweet}"
Agent : "{similar_response}"

#####
Tweet:
"{tweet}"
"""

        messages = [{"role": "user", "content": instruction}]
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        generated_text = response.choices[0].message.content

        return jsonify({
            'response': generated_text,
            'similar_tweet': similar_tweet,
            'similar_response': similar_response,
            'similarity_score': float(similarity_score)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 