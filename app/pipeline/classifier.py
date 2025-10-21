import pytorch_lightning as pl
from transformers import pipeline, AutoTokenizer
from typing import List, Dict, Optional
import torch
import os


class TherapyClassifier(pl.LightningModule):
    def __init__(self, model_name: str, categories: List[str], device: str = "cpu",
                 confidence_threshold: float = 0.2, max_categories: int = 2,
                 finetuned_model_path: Optional[str] = None):
        super().__init__()
        self.categories = categories
        self.device_name = device
        self.confidence_threshold = confidence_threshold
        self.max_categories = max_categories
        self.finetuned_model_path = finetuned_model_path
        self.use_finetuned = False

        if finetuned_model_path and os.path.exists(finetuned_model_path):
            try:
                self._load_finetuned_model(finetuned_model_path, device)
                self.use_finetuned = True
            except Exception as e:
                print(f"Warning: Could not load fine-tuned model: {e}")
                print("Falling back to zero-shot classification")
                self._load_zero_shot_model(model_name, device)
        else:
            self._load_zero_shot_model(model_name, device)

    def _load_zero_shot_model(self, model_name: str, device: str):
        self.classifier = pipeline(
            "zero-shot-classification",
            model=model_name,
            device=0 if device == "cuda" else -1
        )

    def _load_finetuned_model(self, model_path: str, device: str):
        from app.training.trainer import BARTMultiLabelClassifier
        from app.config import settings

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = BARTMultiLabelClassifier(
            model_name=settings.model_name,
            num_labels=len(self.categories)
        )

        state_dict_path = os.path.join(model_path, "model.pt")
        self.model.load_state_dict(torch.load(state_dict_path, map_location=device, weights_only=True))
        self.model.to(device)
        self.model.eval()

    def classify_sentence(self, sentence: str) -> List[Dict[str, any]]:
        if self.use_finetuned:
            return self._classify_finetuned(sentence)
        else:
            return self._classify_zero_shot(sentence)

    def _classify_zero_shot(self, sentence: str) -> List[Dict[str, any]]:
        result = self.classifier(sentence, self.categories, multi_label=True)

        classifications = []
        for label, score in zip(result['labels'], result['scores']):
            if score >= self.confidence_threshold and len(classifications) < self.max_categories:
                classifications.append({
                    "sentence": sentence,
                    "category": label,
                    "confidence": score
                })

        return classifications

    def _classify_finetuned(self, sentence: str) -> List[Dict[str, any]]:
        encoding = self.tokenizer(
            sentence,
            max_length=512,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        input_ids = encoding['input_ids'].to(self.device_name)
        attention_mask = encoding['attention_mask'].to(self.device_name)

        with torch.no_grad():
            logits = self.model(input_ids, attention_mask)
            probs = torch.sigmoid(logits).squeeze(0).cpu().numpy()

        classifications = []
        category_scores = [(self.categories[i], probs[i]) for i in range(len(self.categories))]
        category_scores.sort(key=lambda x: x[1], reverse=True)

        for category, score in category_scores:
            if score >= self.confidence_threshold and len(classifications) < self.max_categories:
                classifications.append({
                    "sentence": sentence,
                    "category": category,
                    "confidence": float(score)
                })

        return classifications

    def classify_batch(self, sentences: List[str]) -> List[List[Dict[str, any]]]:
        results = []
        for sentence in sentences:
            results.append(self.classify_sentence(sentence))
        return results

