from typing import List
import torch


class Settings:
    model_name: str = "facebook/bart-large-mnli"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    confidence_threshold: float = 0.5
    min_sentence_length: int = 10

    categories: List[str] = [
        "efficacy_extent",
        "efficacy_rate",
        "side_effect_severity",
        "side_effect_risk",
        "cost",
        "effect_size_evidence",
        "trial_design",
        "trial_length",
        "num_participants",
        "sex_participants",
        "age_range_participants",
        "other_participant_info",
        "other_study_info"
    ]


settings = Settings()

