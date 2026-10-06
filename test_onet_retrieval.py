from app.services.onet_retriever import search_onet


query = """
Python machine learning SQL data analysis
cloud computing statistical modeling
"""


results = search_onet(
    query=query,
    top_k=10
)


print("\n" + "=" * 80)
print("QUERY")
print("=" * 80)

print(query)


print("\n" + "=" * 80)
print("O*NET SEARCH RESULTS")
print("=" * 80)


for number, result in enumerate(
    results,
    start=1
):

    print(
        f"\n#{number}"
    )

    print(
        "Occupation:",
        result["occupation"]
    )

    print(
        "SOC:",
        result["onet_soc_code"]
    )

    print(
        "Document Type:",
        result["document_type"]
    )

    print(
        "Similarity:",
        round(result["score"], 4)
    )

    print(
        "Text:",
        result["text"][:300]
    )

    print("-" * 80)