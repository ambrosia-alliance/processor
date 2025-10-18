"""
Synthetic data generation using Nebius API.

This module generates realistic therapy-related sentences using an LLM
to create training data for the classification pipeline.
"""

from openai import OpenAI
from typing import List, Dict
from app.config import settings
from app.storage.schemas import SyntheticPrompt


class SyntheticDataGenerator:
    """
    Generate synthetic training data using Nebius LLM API.

    Creates realistic sentences for each therapy category using category-specific
    prompts and examples. Useful for bootstrapping the training dataset.

    Attributes:
        client: OpenAI-compatible API client for Nebius
        model: Model name to use for generation
        prompts: Dictionary of category-specific generation prompts
    """
    def __init__(self):
        """Initialize the synthetic data generator with Nebius API client."""
        self.client = OpenAI(
            api_key=settings.nebius_api_key,
            base_url=settings.nebius_base_url
        )
        self.model = settings.nebius_model
        self.prompts = self._create_category_prompts()

    def _create_category_prompts(self) -> Dict[str, SyntheticPrompt]:
        """
        Create category-specific prompts for data generation.

        Returns:
            Dictionary mapping category names to SyntheticPrompt objects
        """
        return {
            "efficacy_extent": SyntheticPrompt(
                category="efficacy_extent",
                prompt_template="""Generate realistic sentences describing the extent of efficacy for therapeutic treatments like TPE, Red Light Therapy, or Stem Cell Treatments.
Examples should mention improvement levels, response rates, or degrees of success.
Generate 5 diverse sentences.""",
                examples=[
                    "TPE showed moderate improvement in 60% of patients with autoimmune conditions.",
                    "Red light therapy demonstrated significant reduction in inflammation markers."
                ]
            ),
            "efficacy_rate": SyntheticPrompt(
                category="efficacy_rate",
                prompt_template="""Generate realistic sentences describing efficacy rates or success percentages for therapeutic treatments.
Include specific percentages or rates of treatment success.
Generate 5 diverse sentences.""",
                examples=[
                    "The treatment achieved a 75% success rate in clinical trials.",
                    "Efficacy was observed in 82% of participants after 6 months."
                ]
            ),
            "side_effect_severity": SyntheticPrompt(
                category="side_effect_severity",
                prompt_template="""Generate realistic sentences describing the severity of side effects from therapeutic treatments.
Mention whether side effects are mild, moderate, severe, or specific symptom severity.
Generate 5 diverse sentences.""",
                examples=[
                    "Mild fatigue and dizziness were reported in some patients.",
                    "Severe adverse reactions were rare, occurring in less than 2% of cases."
                ]
            ),
            "side_effect_risk": SyntheticPrompt(
                category="side_effect_risk",
                prompt_template="""Generate realistic sentences describing the risk or frequency of side effects.
Include percentages or rates of side effect occurrence.
Generate 5 diverse sentences.""",
                examples=[
                    "Side effects occurred in approximately 15% of patients.",
                    "The risk of complications was estimated at 5-8% across all treatment groups."
                ]
            ),
            "cost": SyntheticPrompt(
                category="cost",
                prompt_template="""Generate realistic sentences describing costs of therapeutic treatments.
Include specific dollar amounts, price ranges, or cost-related information.
Generate 5 diverse sentences.""",
                examples=[
                    "Each session costs between $2,500 and $4,000.",
                    "The total treatment cost averaged $15,000 per patient."
                ]
            ),
            "effect_size_evidence": SyntheticPrompt(
                category="effect_size_evidence",
                prompt_template="""Generate realistic sentences describing statistical effect sizes or evidence strength.
Include Cohen's d, odds ratios, confidence intervals, or other statistical measures.
Generate 5 diverse sentences.""",
                examples=[
                    "The study reported a Cohen's d of 0.8, indicating a large effect.",
                    "Effect size analysis revealed a moderate treatment impact with d=0.5."
                ]
            ),
            "trial_design": SyntheticPrompt(
                category="trial_design",
                prompt_template="""Generate realistic sentences describing clinical trial designs.
Mention randomization, blinding, control groups, or study methodology.
Generate 5 diverse sentences.""",
                examples=[
                    "This double-blind randomized controlled trial compared treatment to placebo.",
                    "The study employed a crossover design with a 4-week washout period."
                ]
            ),
            "trial_length": SyntheticPrompt(
                category="trial_length",
                prompt_template="""Generate realistic sentences describing trial duration or follow-up periods.
Include specific time periods (weeks, months, years).
Generate 5 diverse sentences.""",
                examples=[
                    "The trial was conducted over a 12-month period with 6-month follow-up.",
                    "Participants were observed for 18 weeks during the treatment phase."
                ]
            ),
            "num_participants": SyntheticPrompt(
                category="num_participants",
                prompt_template="""Generate realistic sentences describing the number of study participants.
Include specific numbers or sample sizes.
Generate 5 diverse sentences.""",
                examples=[
                    "The study included 150 participants across three treatment centers.",
                    "A total of 320 patients were enrolled in the clinical trial."
                ]
            ),
            "sex_participants": SyntheticPrompt(
                category="sex_participants",
                prompt_template="""Generate realistic sentences describing the sex or gender distribution of participants.
Include percentages or ratios of male/female participants.
Generate 5 diverse sentences.""",
                examples=[
                    "The study population consisted of 60% female and 40% male participants.",
                    "Gender distribution was balanced with 52% women and 48% men."
                ]
            ),
            "age_range_participants": SyntheticPrompt(
                category="age_range_participants",
                prompt_template="""Generate realistic sentences describing the age range of study participants.
Include specific age ranges or mean ages.
Generate 5 diverse sentences.""",
                examples=[
                    "Participants ranged in age from 35 to 70 years old.",
                    "The mean age of enrolled patients was 52.3 years (SD=12.1)."
                ]
            ),
            "other_participant_info": SyntheticPrompt(
                category="other_participant_info",
                prompt_template="""Generate realistic sentences describing other participant characteristics.
Include information like comorbidities, baseline characteristics, inclusion criteria, etc.
Generate 5 diverse sentences.""",
                examples=[
                    "All participants had documented autoimmune conditions at baseline.",
                    "Inclusion criteria required patients to be treatment-naive."
                ]
            ),
            "other_study_info": SyntheticPrompt(
                category="other_study_info",
                prompt_template="""Generate realistic sentences describing other study information not covered by previous categories.
Include protocol details, ethical approval, funding sources, etc.
Generate 5 diverse sentences.""",
                examples=[
                    "The study protocol was approved by institutional review boards.",
                    "Research was funded by a national health research grant."
                ]
            )
        }

    def generate_for_category(self, category: str, num_samples: int = 5) -> List[str]:
        """
        Generate synthetic sentences for a specific category.

        Args:
            category: Category name to generate data for
            num_samples: Number of sentences to generate

        Returns:
            List of generated sentences

        Raises:
            ValueError: If category is unknown
        """
        if category not in self.prompts:
            raise ValueError(f"Unknown category: {category}")

        prompt = self.prompts[category]

        system_message = """You are a medical research text generator. Generate realistic sentences that would appear in medical research papers about therapeutic treatments.
Each sentence should be factual-sounding and contain specific information relevant to the requested category.
Return only the sentences, one per line, without numbering or bullet points."""

        user_message = f"{prompt.prompt_template}\n\nExamples:\n" + "\n".join(prompt.examples)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,
                max_tokens=500
            )

            generated_text = response.choices[0].message.content.strip()
            sentences = [s.strip() for s in generated_text.split('\n') if s.strip()]

            return sentences[:num_samples]

        except Exception as e:
            print(f"Error generating synthetic data: {e}")
            return []

    def generate_balanced_dataset(self, samples_per_category: int = 10) -> Dict[str, List[str]]:
        """
        Generate balanced synthetic dataset across all categories.

        Args:
            samples_per_category: Number of samples to generate per category

        Returns:
            Dictionary mapping categories to lists of generated sentences
        """
        dataset = {}

        for category in settings.categories:
            print(f"Generating {samples_per_category} samples for {category}...")
            sentences = self.generate_for_category(category, samples_per_category)
            dataset[category] = sentences

        return dataset

    def generate_batch(self, categories: List[str], samples_per_category: int = 5) -> Dict[str, List[str]]:
        """
        Generate synthetic data for selected categories only.

        Args:
            categories: List of category names to generate for
            samples_per_category: Number of samples per category

        Returns:
            Dictionary mapping categories to lists of generated sentences
        """
        dataset = {}

        for category in categories:
            if category in settings.categories:
                sentences = self.generate_for_category(category, samples_per_category)
                dataset[category] = sentences

        return dataset

