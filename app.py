import os
import json
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from sklearn.metrics.pairwise import cosine_similarity
from openai import AzureOpenAI
from langchain.schema import Document

app = Flask(__name__)

# --- Configuration & Azure Clients ---
# Ensure you have set these environment variables in your Azure deployment environment
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "your-azure-api-key")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "https://your-resource-name.openai.azure.com/")
AZURE_DEPLOYMENT_NAME = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o") # Your model deployment name in Azure Foundry
AZURE_EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-01",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# --- Reused Functions from Notebook[cite: 1] ---
def load_docs_from_jsonl(file_path):
    """Loads langchain Documents from a jsonl file (reused from notebook)[cite: 1]."""
    array = []
    if not os.path.exists(file_path):
        return array
    with open(file_path, 'r', encoding='utf-8') as jsonl_file:
        for line in jsonl_file:
            data = json.loads(line)
            obj = Document(**data)
            array.append(obj)
    return array

def clean_text(text):
    """Cleans input text by removing extra whitespaces[cite: 1]."""
    import re
    return re.sub(r'\s+', ' ', text).strip()

# --- Load Vector Database into Pandas DataFrame ---
DATA_FILE = 'scraped_data.jsonl'
raw_docs = load_docs_from_jsonl(DATA_FILE)

# Build DataFrame and precompute or load embeddings
df_data = []
for doc in raw_docs:
    df_data.append({
        "title": doc.metadata.get("title", "No Title"),
        "source": doc.metadata.get("source", ""),
        "content": clean_text(doc.page_content)
    })

df = pd.DataFrame(df_data)

# NOTE: In production, pre-compute and store embeddings in your JSONL file. 
# For this basic setup, you can generate dummy embeddings or compute them on startup if dataset is small.
# Here we simulate or generate embeddings if an embedding column is missing:
def get_embedding(text):
    response = client.embeddings.create(
        input=[text],
        model=AZURE_EMBEDDING_DEPLOYMENT
    )
    return response.data[0].embedding

# Precompute embeddings for the DataFrame if not already present
if not df.empty and 'embedding' not in df.columns:
    print("Computing embeddings for dataframe items...")
    # Limiting to content slice for speed in a basic app demo
    df['embedding'] = df['content'].apply(lambda x: get_embedding(x[:2000]))

def retrieve_top_k(query, k=3):
    """Retrieves top-k relevant articles using sklearn cosine similarity[cite: 1]."""
    if df.empty or 'embedding' not in df.columns:
        return []
    
    query_embedding = get_embedding(query)
    
    # Compute similarity against all rows using sklearn
    doc_embeddings = np.vstack(df['embedding'].values)
    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
    
    top_indices = similarities.argsort()[-k:][::-1]
    
    results = []
    for idx in top_indices:
        results.append({
            "title": df.iloc[idx]['title'],
            "source": df.iloc[idx]['source'],
            "content": df.iloc[idx]['content'][:1000], # Snippet preview
            "score": float(similarities[idx])
        })
    return results

# --- Flask Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_query = request.json.get("query", "")
    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    # 1. Retrieve relevant context from Pandas Vector DB
    retrieved_docs = retrieve_top_k(user_query, k=3)
    
    context_text = "\n\n".join([f"Source: {doc['source']}\nContent: {doc['content']}" for doc in retrieved_docs])

    # 2. Generate answer using Azure Foundry Model (Azure OpenAI)
    prompt = f"""You are a helpful assistant. Use the following context pieces to answer the user's question accurately. If you don't know the answer based on the context, state that you don't know.

Context:
{context_text}

Question: {user_query}
Answer:"""

    try:
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are an expert AI assistant answering questions based on provided documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"Error communicating with Azure Foundry model: {str(e)}"

    return jsonify({
        "answer": answer,
        "sources": [{"title": d["title"], "source": d["source"]} for d in retrieved_docs]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)