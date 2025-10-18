from typing import List, Dict
import torch
import os


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

    nebius_api_key: str = os.getenv("NEBIUS_API_KEY", "")
    nebius_base_url: str = "https://api.studio.nebius.com/v1/"
    nebius_model: str = "deepseek-ai/DeepSeek-V3-0324-fast"

    ensemble_models: List[str] = [
        "facebook/bart-large-mnli",
        "microsoft/deberta-v3-base",
        "roberta-large-mnli",
        "typeform/distilbert-base-uncased-mnli",
        "cross-encoder/nli-deberta-v3-base"
    ]

    supermajority_threshold: float = 0.8
    entropy_threshold: float = 1.5
    label_threshold: float = 0.5

    category_accuracy_threshold: float = 0.90
    min_samples_for_handoff: int = 50

    human_review_enabled: Dict[str, bool] = {
        "efficacy_extent": True,
        "efficacy_rate": True,
        "side_effect_severity": True,
        "side_effect_risk": True,
        "cost": True,
        "effect_size_evidence": True,
        "trial_design": True,
        "trial_length": True,
        "num_participants": True,
        "sex_participants": True,
        "age_range_participants": True,
        "other_participant_info": True,
        "other_study_info": True
    }

    database_path: str = "data/labeling.db"
    export_path: str = "data/exports/"


settings = Settings()

