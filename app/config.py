from typing import List, Optional
import torch


class Settings:
    model_name: str = "facebook/bart-large-mnli"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    confidence_threshold: float = 0.5
    max_categories_per_sentence: int = 2
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

    db_path: str = "therapy_labels.db"

    finetuned_model_path: Optional[str] = "models/finetuned/model_20251021_113816"

    focal_loss_alpha: float = 0.75
    focal_loss_gamma: float = 2.0
    focal_loss_class_weights: List[float] = [1.0] * 13

    training_batch_size: int = 2
    training_epochs: int = 10
    training_learning_rate: float = 2e-5
    training_warmup_steps: int = 100
    training_patience: int = 3
    training_dropout: float = 0.1

    min_samples_per_category: int = 50

    api_host: str = "0.0.0.0"
    api_port: int = 5000


settings = Settings()

