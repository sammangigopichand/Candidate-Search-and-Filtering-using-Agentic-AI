import json
import urllib.request
import time


URL = "http://localhost:11434/api/generate"

payload = {
    "model": "llama3.1:8b",
    "prompt": "Return only the word WORKING.",
    "stream": False
}

data = json.dumps(payload).encode("utf-8")

request = urllib.request.Request(
    URL,
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

print("Sending request to Ollama...")

start = time.time()

try:

    with urllib.request.urlopen(
        request,
        timeout=900
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    end = time.time()

    print("\nResponse:")
    print(result["response"])

    print("\nTime taken:")
    print(round(end - start, 2), "seconds")

    print("\nOllama API working successfully!")

except Exception as error:

    print("\nOllama API failed:")
    print(type(error).__name__)
    print(error)