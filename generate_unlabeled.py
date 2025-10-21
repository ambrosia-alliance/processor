import os
import sys
import json
import argparse
from typing import List
from openai import OpenAI

from app.config import settings
from app.database.schema import initialize_database
from app.database.db import DatabaseManager


CATEGORY_DESCRIPTIONS = {
    "efficacy_extent": "Information about how much improvement or benefit a therapy provides",
    "efficacy_rate": "Information about what percentage of patients respond to therapy",
    "side_effect_severity": "Information about how severe side effects are",
    "side_effect_risk": "Information about the likelihood or percentage of side effects occurring",
    "cost": "Information about monetary cost, price, or financial burden",
    "effect_size_evidence": "Statistical measures of treatment effect",
    "trial_design": "Information about study methodology",
    "trial_length": "Duration of the study or treatment period",
    "num_participants": "Number of subjects in the study",
    "sex_participants": "Gender distribution of participants",
    "age_range_participants": "Age information about participants",
    "other_participant_info": "Other demographic or clinical characteristics",
    "other_study_info": "Other study details not covered by other categories"
}


def create_system_prompt() -> str:
    categories_text = "\n".join([f"- {cat}: {desc}" for cat, desc in CATEGORY_DESCRIPTIONS.items()])

    return f"""You are a medical research text generator. Generate realistic, diverse SINGLE SENTENCES about medical therapies, clinical trials, and treatment outcomes.

The text should cover these types of information:
{categories_text}

IMPORTANT CONSTRAINTS:
- Each sample must be ONE complete sentence only (can be compound/complex, but still one sentence)
- Each sentence should focus on 1-2 information types maximum
- Keep sentences clear and focused, not overly packed with information
- Sound like they come from medical research papers, clinical trial reports, or therapy descriptions

Return ONLY a JSON array of strings (the sentence samples), nothing else."""


def create_user_prompt(num_samples: int, target_categories: List[str] = None) -> str:
    if target_categories:
        cats = ", ".join(target_categories)
        return f"""Generate {num_samples} realistic medical/therapy SINGLE SENTENCES about: {cats}.

Requirements:
- ONE sentence per sample (compound/complex sentences are fine)
- Focus on 1-2 information types per sentence maximum
- Clear, focused sentences
- Vary medical conditions, treatments, and contexts

Return exactly {num_samples} sentences as a JSON array of strings."""
    else:
        return f"""Generate {num_samples} realistic, diverse medical/therapy SINGLE SENTENCES covering various aspects of clinical research and treatment outcomes.

Requirements:
- ONE sentence per sample (compound/complex sentences are fine)
- Each sentence should focus on 1-2 information types maximum
- Clear, focused sentences
- Include variety: different medical conditions, treatment types, and study contexts

Return exactly {num_samples} sentences as a JSON array of strings."""


def generate_batch(client: OpenAI, num_samples: int, target_categories: List[str] = None) -> List[str]:
    system_prompt = create_system_prompt()
    user_prompt = create_user_prompt(num_samples, target_categories)

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324-fast",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )

        content = response.choices[0].message.content

        if not content:
            print(f"Warning: Empty response from API")
            return []

        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end]
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                content = content[start:end]

        content = content.strip()

        samples = json.loads(content)

        if not isinstance(samples, list):
            print(f"Warning: Expected list but got {type(samples)}")
            return []

        return [str(s) for s in samples if s]

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {content[:200]}...")
        return []
    except Exception as e:
        print(f"Error generating batch: {e}")
        return []


def insert_unlabeled_samples(db: DatabaseManager, texts: List[str], source: str = "synthetic_unlabeled"):
    inserted_count = 0

    for text in texts:
        text = text.strip()
        if not text or len(text) < 20:
            continue

        db.add_sample(text, source)
        inserted_count += 1

    return inserted_count


def generate_unlabeled_data(db_path: str, total_samples: int = 50, dry_run: bool = False):
    api_key = os.environ.get("NEBIUS_API_KEY")
    if not api_key:
        print("Error: NEBIUS_API_KEY environment variable not set")
        sys.exit(1)

    client = OpenAI(
        base_url="https://api.studio.nebius.com/v1/",
        api_key=api_key
    )

    initialize_database(db_path)

    print(f"Generation Plan:")
    print(f"  Total samples: {total_samples}")
    print(f"  Source: synthetic_unlabeled")
    print(f"  Dry run: {dry_run}")
    print()

    all_texts = []
    batch_size = 10
    num_batches = (total_samples + batch_size - 1) // batch_size

    print(f"Generating {total_samples} unlabeled samples in {num_batches} batches...")

    for i in range(num_batches):
        remaining = total_samples - (i * batch_size)
        current_batch_size = min(batch_size, remaining)

        print(f"  [{i+1}/{num_batches}] Generating {current_batch_size} samples...")

        batch = generate_batch(client, current_batch_size)
        all_texts.extend(batch)
        print(f"    Generated {len(batch)} samples")

    print()
    print(f"Generated {len(all_texts)} total samples")

    if dry_run:
        print("\n[DRY RUN] Preview of generated samples:")
        for i, text in enumerate(all_texts[:10], 1):
            print(f"\n{i}. {text}")

        if len(all_texts) > 10:
            print(f"\n... and {len(all_texts) - 10} more samples")

        print("\nTo insert into database, run without --dry-run flag")
    else:
        print("\nInserting into database...")
        with DatabaseManager(db_path) as db:
            inserted = insert_unlabeled_samples(db, all_texts)
            print(f"Inserted {inserted} unlabeled samples")

            total_unlabeled = len(db.get_unlabeled_samples())
            print(f"Total unlabeled samples in database: {total_unlabeled}")

        print(f"\nTo label these samples, run:")
        print(f"  python label.py --batch-size {min(20, inserted)}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic unlabeled therapy text for manual labeling")
    parser.add_argument('--db', default=settings.db_path, help='Database path')
    parser.add_argument('--samples', type=int, default=50, help='Total number of samples to generate')
    parser.add_argument('--dry-run', action='store_true', help='Preview generation without inserting to database')

    args = parser.parse_args()

    if args.samples < 1:
        print("Error: --samples must be at least 1")
        sys.exit(1)

    generate_unlabeled_data(
        db_path=args.db,
        total_samples=args.samples,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

