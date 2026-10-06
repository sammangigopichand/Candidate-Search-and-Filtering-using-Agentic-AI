import os
import json
import urllib.request

import faiss
import numpy as np


# ============================================================
# PATHS
# ============================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(APP_DIR)

PROCESSED_DIR = os.path.join(
    PROJECT_ROOT,
    "processed"
)

FAISS_FILE = os.path.join(
    PROCESSED_DIR,
    "onet_index.faiss"
)

METADATA_FILE = os.path.join(
    PROCESSED_DIR,
    "onet_metadata.json"
)


# ============================================================
# OLLAMA CONFIG
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/embed"

EMBEDDING_MODEL = "nomic-embed-text"


# ============================================================
# LOAD FAISS INDEX
# ============================================================

print("Loading O*NET FAISS index...")

index = faiss.read_index(
    FAISS_FILE
)


# ============================================================
# LOAD METADATA
# ============================================================

with open(
    METADATA_FILE,
    "r",
    encoding="utf-8"
) as file:

    metadata = json.load(file)


if index.ntotal != len(metadata):
    raise ValueError(
        f"FAISS contains {index.ntotal} vectors "
        f"but metadata contains {len(metadata)} records."
    )


print(
    f"O*NET knowledge base loaded: "
    f"{index.ntotal} vectors"
)


# ============================================================
# GENERATE QUERY EMBEDDING
# ============================================================

def get_query_embedding(text):

    payload = {
        "model": EMBEDDING_MODEL,
        "input": text
    }

    data = json.dumps(
        payload
    ).encode("utf-8")

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
        timeout=120
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    embedding = np.array(
        [result["embeddings"][0]],
        dtype="float32"
    )

    # IMPORTANT:
    # We normalized vectors before storing them in FAISS,
    # so normalize query vectors too.
    faiss.normalize_L2(
        embedding
    )

    return embedding


# ============================================================
# SEARCH O*NET
# ============================================================

def search_onet(
    query,
    top_k=5,
    document_type=None
):

    query_embedding = get_query_embedding(
        query
    )

    # Search more documents when filtering because FAISS
    # itself is not filtering by metadata here.
    search_k = top_k

    if document_type:
        search_k = min(
            max(top_k * 10, 50),
            index.ntotal
        )

    scores, indices = index.search(
        query_embedding,
        search_k
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx == -1:
            continue

        item = metadata[idx]

        item_metadata = item.get(
            "metadata",
            {}
        )

        if (
            document_type
            and item_metadata.get("document_type")
            != document_type
        ):
            continue

        results.append({
            "score": float(score),
            "onet_soc_code": item_metadata.get(
                "onet_soc_code"
            ),
            "occupation": item_metadata.get(
                "occupation"
            ),
            "document_type": item_metadata.get(
                "document_type"
            ),
            "text": item.get(
                "text",
                ""
            )
        })

        if len(results) >= top_k:
            break

    # return resultstest_onet_retrieval.py
    return results