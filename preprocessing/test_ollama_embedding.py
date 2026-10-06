import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "nomic-embed-text"


def get_embedding(text):
    payload = {
        "model": MODEL,
        "input": text
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["embeddings"][0]


text = """
Data Scientist with Python, SQL,
machine learning and data analysis skills.
"""

embedding = get_embedding(text)

print("=" * 60)
print("OLLAMA EMBEDDING TEST")
print("=" * 60)

print("Model:", MODEL)
print("Embedding dimension:", len(embedding))
print("First 10 values:", embedding[:10])

print("\nEmbedding generated successfully!")