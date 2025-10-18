import requests
import json


API_URL = "http://localhost:8000"

example_text = """
Therapeutic Plasma Exchange (TPE) has demonstrated a 75% efficacy rate in treating autoimmune conditions.
The treatment showed significant improvement in patient outcomes over a 6-month period.
Common side effects include mild fatigue and temporary dizziness, occurring in approximately 15% of cases.
The average cost per session is $2,500 to $4,000.
This double-blind randomized controlled trial included 150 participants.
The study population consisted of 60% female and 40% male participants.
Participants ranged in age from 35 to 70 years old.
The trial was conducted over a 12-month period with a 6-month follow-up.
Effect size analysis showed a Cohen's d of 0.8, indicating a large treatment effect.
"""

def main():
    print("Testing Therapy Classification API\n")

    health_response = requests.get(f"{API_URL}/health")
    print(f"Health Check: {health_response.json()}\n")

    categories_response = requests.get(f"{API_URL}/categories")
    print(f"Available Categories: {len(categories_response.json()['categories'])} categories\n")

    classify_response = requests.post(
        f"{API_URL}/classify",
        json={"text": example_text}
    )

    results = classify_response.json()

    print("Classification Results:")
    print("=" * 80)
    for category, data in results["categories"].items():
        if data["count"] > 0:
            print(f"\n{category.upper()}")
            print(f"  Count: {data['count']}")
            print(f"  Avg Confidence: {data['avg_confidence']:.2%}")
            print(f"  Sentences:")
            for sentence in data["sentences"]:
                print(f"    - {sentence['text'][:80]}... (conf: {sentence['confidence']:.2%})")


if __name__ == "__main__":
    main()

