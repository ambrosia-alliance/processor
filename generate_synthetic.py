import os
import sys
import json
import argparse
from typing import List, Dict
from openai import OpenAI

from app.config import settings
from app.database.schema import initialize_database
from app.database.db import DatabaseManager


CATEGORY_DESCRIPTIONS = {
    "efficacy_extent": "Information about how much improvement or benefit a therapy provides (e.g., '50% reduction in symptoms', 'complete remission', 'partial response')",
    "efficacy_rate": "Information about what percentage of patients respond to therapy (e.g., '75% of patients improved', '60% response rate')",
    "side_effect_severity": "Information about how severe side effects are (e.g., 'mild', 'moderate', 'severe', 'life-threatening')",
    "side_effect_risk": "Information about the likelihood or percentage of side effects occurring (e.g., '15% experienced nausea', 'rare adverse events')",
    "cost": "Information about monetary cost, price, or financial burden (e.g., '$2,500 per session', 'expensive', 'cost-effective')",
    "effect_size_evidence": "Statistical measures of treatment effect (e.g., 'Cohen's d = 0.8', 'large effect size', 'odds ratio of 2.5')",
    "trial_design": "Information about study methodology (e.g., 'double-blind', 'randomized controlled trial', 'placebo-controlled', 'crossover design')",
    "trial_length": "Duration of the study or treatment period (e.g., '6-month trial', '12-week study', '2-year follow-up')",
    "num_participants": "Number of subjects in the study (e.g., '150 participants', '500 patients enrolled')",
    "sex_participants": "Gender distribution of participants (e.g., '60% female', 'predominantly male cohort')",
    "age_range_participants": "Age information about participants (e.g., '35-70 years old', 'elderly patients', 'mean age 45')",
    "other_participant_info": "Other demographic or clinical characteristics (e.g., 'treatment-resistant patients', 'previously diagnosed with', 'comorbidities')",
    "other_study_info": "Other study details not covered by other categories (e.g., 'multicenter trial', 'FDA-approved', 'peer-reviewed publication')"
}


def create_system_prompt() -> str:
    categories_text = "\n".join([f"- {cat}: {desc}" for cat, desc in CATEGORY_DESCRIPTIONS.items()])

    return f"""You are a medical research text generator. Generate realistic SINGLE SENTENCES about medical therapies, clinical trials, and treatment outcomes.

CATEGORIES:
{categories_text}

IMPORTANT CONSTRAINTS:
- Each sample must be ONE complete sentence only (can be compound/complex, but still one sentence)
- Each sample should focus on 1-2 categories maximum
- Keep sentences clear and focused, not overly packed with information
- The text should sound like it comes from medical research papers, clinical trial reports, or therapy descriptions

Return your response as a JSON array of objects, where each object has:
- "text": the generated SINGLE sentence
- "labels": an object with category names as keys and boolean values (true if clearly present, false otherwise)

Generate diverse, realistic examples covering different therapies, conditions, and contexts."""


def create_user_prompt(target_categories: List[str], num_samples: int, is_multi: bool) -> str:
    if is_multi:
        return f"""Generate {num_samples} realistic medical/therapy SINGLE SENTENCES. Each sentence should contain information from AT MOST 2 of these categories: {', '.join(target_categories)}.

Requirements:
- ONE sentence per sample (compound/complex sentences are fine)
- EXACTLY 2 categories per sentence (no more, no less)
- Natural combinations (e.g., efficacy_rate + side_effect_risk, trial_design + num_participants)
- Clear, focused sentences

Return exactly {num_samples} samples in JSON format."""
    else:
        category = target_categories[0]
        return f"""Generate {num_samples} realistic medical/therapy SINGLE SENTENCES. Each sentence should focus on: {category} ({CATEGORY_DESCRIPTIONS[category]}).

Requirements:
- ONE sentence per sample (compound/complex sentences are fine)
- Focus on the target category (it's okay if ONE other category is slightly present, but minimize this)
- Clear, focused sentences

Return exactly {num_samples} samples in JSON format."""


def generate_batch(client: OpenAI, target_categories: List[str], num_samples: int, is_multi: bool) -> List[Dict]:
    system_prompt = create_system_prompt()
    user_prompt = create_user_prompt(target_categories, num_samples, is_multi)

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

        return samples

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {content[:200]}...")
        return []
    except Exception as e:
        print(f"Error generating batch: {e}")
        return []


def insert_samples_to_db(db: DatabaseManager, samples: List[Dict], source: str = "synthetic_nebius_v1"):
    inserted_count = 0

    for sample in samples:
        text = sample.get("text", "").strip()
        labels = sample.get("labels", {})

        if not text or not labels:
            continue

        sample_id = db.add_sample(text, source)

        for category, is_positive in labels.items():
            if category in settings.categories:
                db.add_label(sample_id, category, bool(is_positive), confidence=1.0)

        db.mark_sample_labeled(sample_id)
        inserted_count += 1

    return inserted_count


def generate_synthetic_data(db_path: str, total_samples: int = 130, multi_ratio: float = 0.3, dry_run: bool = False):
    api_key = os.environ.get("NEBIUS_API_KEY")
    if not api_key:
        print("Error: NEBIUS_API_KEY environment variable not set")
        sys.exit(1)

    client = OpenAI(
        base_url="https://api.studio.nebius.com/v1/",
        api_key=api_key
    )

    initialize_database(db_path)

    num_multi = int(total_samples * multi_ratio)
    num_single = total_samples - num_multi

    samples_per_category = num_single // len(settings.categories)

    print(f"Generation Plan:")
    print(f"  Total samples: {total_samples}")
    print(f"  Single-category: {num_single} ({samples_per_category} per category)")
    print(f"  Multi-category: {num_multi}")
    print(f"  Dry run: {dry_run}")
    print()

    all_samples = []
    category_counts = {cat: 0 for cat in settings.categories}

    print("Generating single-category samples...")
    for i, category in enumerate(settings.categories):
        print(f"  [{i+1}/{len(settings.categories)}] Generating {samples_per_category} samples for '{category}'...")

        batch = generate_batch(client, [category], samples_per_category, is_multi=False)

        for sample in batch:
            labels = sample.get("labels", {})
            positive_categories = [cat for cat, val in labels.items() if val and cat in settings.categories]
            for cat in positive_categories:
                category_counts[cat] += 1

        all_samples.extend(batch)
        print(f"    Generated {len(batch)} samples")

    print()
    print("Generating multi-category samples...")

    batch_size = 5
    num_batches = (num_multi + batch_size - 1) // batch_size

    for i in range(num_batches):
        remaining = num_multi - (i * batch_size)
        current_batch_size = min(batch_size, remaining)

        print(f"  [{i+1}/{num_batches}] Generating {current_batch_size} multi-category samples...")

        batch = generate_batch(client, settings.categories, current_batch_size, is_multi=True)

        for sample in batch:
            labels = sample.get("labels", {})
            positive_categories = [cat for cat, val in labels.items() if val and cat in settings.categories]
            for cat in positive_categories:
                category_counts[cat] += 1

        all_samples.extend(batch)
        print(f"    Generated {len(batch)} samples")

    print()
    print(f"Generated {len(all_samples)} total samples")

    if dry_run:
        print("\n[DRY RUN] Preview of generated samples:")
        for i, sample in enumerate(all_samples[:5], 1):
            print(f"\n{i}. {sample['text'][:100]}...")
            labels = sample.get('labels', {})
            positive = [k for k, v in labels.items() if v]
            print(f"   Categories: {', '.join(positive)}")

        if len(all_samples) > 5:
            print(f"\n... and {len(all_samples) - 5} more samples")
    else:
        print("\nInserting into database...")
        with DatabaseManager(db_path) as db:
            inserted = insert_samples_to_db(db, all_samples)
            print(f"Inserted {inserted} samples")

    print("\nCategory distribution:")
    for category, count in category_counts.items():
        print(f"  {category}: {count}")

    multi_count = sum(1 for s in all_samples if sum(1 for v in s.get('labels', {}).values() if v) > 1)
    print(f"\nMulti-category samples: {multi_count} ({multi_count/len(all_samples)*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic labeled data using Nebius AI")
    parser.add_argument('--db', default=settings.db_path, help='Database path')
    parser.add_argument('--samples', type=int, default=130, help='Total number of samples to generate')
    parser.add_argument('--multi-ratio', type=float, default=0.3, help='Ratio of multi-category samples (0.0-1.0)')
    parser.add_argument('--dry-run', action='store_true', help='Preview generation without inserting to database')

    args = parser.parse_args()

    if args.multi_ratio < 0 or args.multi_ratio > 1:
        print("Error: --multi-ratio must be between 0.0 and 1.0")
        sys.exit(1)

    generate_synthetic_data(
        db_path=args.db,
        total_samples=args.samples,
        multi_ratio=args.multi_ratio,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

