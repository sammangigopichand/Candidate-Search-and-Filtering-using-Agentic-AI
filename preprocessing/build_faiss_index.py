import os
import json
import urllib.request

import numpy as np
import faiss


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "processed")

INPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "semantic_documents.json"
)

FAISS_FILE = os.path.join(
    PROCESSED_DIR,
    "onet_index.faiss"
)

METADATA_FILE = os.path.join(
    PROCESSED_DIR,
    "onet_metadata.json"
)

OLLAMA_URL = "http://localhost:11434/api/embed"

MODEL = "nomic-embed-text"

BATCH_SIZE = 20


# ============================================================
# OLLAMA EMBEDDING
# ============================================================

def get_embeddings(texts):

    payload = {
        "model": MODEL,
        "input": texts
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=300
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["embeddings"]


# ============================================================
# LOAD DOCUMENTS
# ============================================================

print("=" * 70)
print("LOADING SEMANTIC DOCUMENTS")
print("=" * 70)

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    documents = json.load(file)

print("Documents loaded:", len(documents))


# ============================================================
# GENERATE EMBEDDINGS
# ============================================================

all_embeddings = []
metadata = []

total = len(documents)

print("\nGenerating embeddings using:", MODEL)


for start in range(0, total, BATCH_SIZE):

    end = min(
        start + BATCH_SIZE,
        total
    )

    batch = documents[start:end]

    texts = [
        document["text"]
        for document in batch
    ]

    try:

        embeddings = get_embeddings(texts)

    except Exception as error:

        print(
            f"\nError while processing "
            f"documents {start} to {end}:"
        )

        print(error)

        raise

    if len(embeddings) != len(batch):

        raise ValueError(
            "Number of embeddings does not "
            "match number of documents."
        )

    all_embeddings.extend(
        embeddings
    )

    for document in batch:

        metadata.append({
            "text": document["text"],
            "metadata": document["metadata"]
        })

    print(
        f"Embedded {end}/{total}"
    )


# ============================================================
# CONVERT TO NUMPY
# ============================================================

embedding_matrix = np.array(
    all_embeddings,
    dtype="float32"
)

print("\nEmbedding matrix shape:")
print(embedding_matrix.shape)


# ============================================================
# NORMALIZE
# ============================================================

faiss.normalize_L2(
    embedding_matrix
)


# ============================================================
# CREATE FAISS INDEX
# ============================================================

dimension = embedding_matrix.shape[1]

print("Embedding dimension:", dimension)

index = faiss.IndexFlatIP(
    dimension
)

index.add(
    embedding_matrix
)


# ============================================================
# SAVE FAISS INDEX
# ============================================================

faiss.write_index(
    index,
    FAISS_FILE
)


# ============================================================
# SAVE METADATA
# ============================================================

with open(
    METADATA_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metadata,
        file,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 70)

print("FAISS INDEX CREATED SUCCESSFULLY")

print("=" * 70)

print("Documents:", len(documents))
print("Vectors:", index.ntotal)
print("Dimension:", dimension)

print("\nFAISS index:")
print(FAISS_FILE)

print("\nMetadata:")
print(METADATA_FILE)