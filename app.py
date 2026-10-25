import os
import json
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from sklearn.metrics.pairwise import cosine_similarity
from openai import AzureOpenAI

app = Flask(__name__)

# --- Configuration & Azure Clients ---
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "your-azure-api-key")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "https://your-resource-name.openai.azure.com/")
AZURE_DEPLOYMENT_NAME = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o")
AZURE_EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-01",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# --- File Paths ---
DATA_FILE = 'scraped_data.jsonl'
VECTOR_DB_FILE = 'vector_db.json'

# --- Helper Functions ---
def load_docs_from_jsonl(file_path):
    """Loads document records as standard dictionaries from a jsonl file."""
    array = []
    if not os.path.exists(file_path):
        return array
    with open(file_path, 'r', encoding='utf-8') as jsonl_file:
        for line in jsonl_file:
            data = json.loads(line)
            array.append(data)
    return array

def clean_text(text):
    """Cleans input text by removing extra whitespaces."""
    import re
    return re.sub(r'\s+', ' ', text).strip()

def get_embedding(text):
    """Generates an embedding vector using Azure OpenAI."""
    response = client.embeddings.create(
        input=[text],
        model=AZURE_EMBEDDING_DEPLOYMENT
    )
    return response.data[0].embedding

# --- Vector Database Initialization & Persistence Logic ---
def initialize_vector_db():
    """Loads precomputed vector database from disk if available. 
    Otherwise, computes embeddings from scraped_data.jsonl and saves them.
    """
    if os.path.exists(VECTOR_DB_FILE):
        print(f"Loading vector database from {VECTOR_DB_FILE}...")
        with open(VECTOR_DB_FILE, 'r', encoding='utf-8') as f:
            df_data = json.load(f)
        return pd.DataFrame(df_data)
    
    print(f"Vector database '{VECTOR_DB_FILE}' not found.")
    raw_docs = load_docs_from_jsonl(DATA_FILE)
    if not raw_docs:
        print("Warning: Source data file is empty or missing.")
        return pd.DataFrame(columns=["title", "source", "content", "embedding"])

    print("Computing embeddings from scratch (this may take a moment)...")
    df_data = []
    for doc in raw_docs:
        metadata = doc.get("metadata", {})
        title = metadata.get("title", "No Title")
        source = metadata.get("source", "")
        content = clean_text(doc.get("page_content", ""))
        
        print(f"Processing: {title}")
        # Generate embedding (limiting input chunk size for safety)
        embedding = get_embedding(content[:2000])
        
        df_data.append({
            "title": title,
            "source": source,
            "content": content,
            "embedding": embedding
        })
    
    # Save to disk as a JSON file vector database
    with open(VECTOR_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(df_data, f, ensure_ascii=False, indent=2)
    print(f"Vector database successfully created and saved to {VECTOR_DB_FILE}")

    return pd.DataFrame(df_data)

# Load database into memory on startup
df = initialize_vector_db()

def retrieve_top_k(query, k=3):
    """Retrieves top-k relevant articles using sklearn cosine similarity."""
    if df.empty or 'embedding' not in df.columns:
        return []
    
    query_embedding = get_embedding(query)
    doc_embeddings = np.vstack(df['embedding'].values)
    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
    
    top_indices = similarities.argsort()[-k:][::-1]
    
    results = []
    for idx in top_indices:
        results.append({
            "title": df.iloc[idx]['title'],
            "source": df.iloc[idx]['source'],
            "content": df.iloc[idx]['content'][:1000],
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
        return jsonify({"error": "No query provided"}, 400)

    # 1. Retrieve relevant context from Pandas Vector DB
    retrieved_docs = retrieve_top_k(user_query, k=3)
    context_text = "\n\n".join([f"Source: {doc['source']}\nContent: {doc['content']}" for doc in retrieved_docs])

    # 2. Generate answer using Azure Foundry Model
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
