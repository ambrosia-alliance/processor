import torch
import torch.nn as nn
from torch.optim import AdamW
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from typing import Dict, Optional
import os
from datetime import datetime
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report
import numpy as np

from app.training.focal_loss import WeightedFocalLoss
from app.training.dataset import create_data_loaders
from app.database.db import DatabaseManager
from app.config import settings


class BARTMultiLabelClassifier(nn.Module):
    def __init__(self, model_name: str, num_labels: int, dropout: float = 0.1):
        super(BARTMultiLabelClassifier, self).__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_labels)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        return logits


class TherapyTrainer:
    def __init__(self, db_path: str, output_dir: str = "models/finetuned"):
        self.db_path = db_path
        self.output_dir = output_dir
        self.device = torch.device(settings.device)

        os.makedirs(output_dir, exist_ok=True)

    def train(self, epochs: int = 10, batch_size: int = 8, learning_rate: float = 2e-5,
              warmup_steps: int = 100, patience: int = 3) -> Dict:

        print("Loading tokenizer and creating datasets...")
        tokenizer = AutoTokenizer.from_pretrained(settings.model_name)

        train_loader, val_loader = create_data_loaders(
            self.db_path, tokenizer, batch_size=batch_size
        )

        if len(train_loader) == 0:
            raise ValueError("No training data available!")

        print(f"Training samples: {len(train_loader.dataset)}")
        print(f"Validation samples: {len(val_loader.dataset)}")

        print("\nInitializing model...")
        model = BARTMultiLabelClassifier(
            settings.model_name,
            num_labels=len(settings.categories),
            dropout=settings.training_dropout
        )
        model.to(self.device)

        class_weights = torch.tensor(settings.focal_loss_class_weights, dtype=torch.float)
        criterion = WeightedFocalLoss(
            alpha=settings.focal_loss_alpha,
            gamma=settings.focal_loss_gamma,
            class_weights=class_weights
        )

        optimizer = AdamW(model.parameters(), lr=learning_rate)

        total_steps = len(train_loader) * epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps
        )

        print(f"\nStarting training for {epochs} epochs...")
        print(f"Using focal loss with alpha={settings.focal_loss_alpha}, gamma={settings.focal_loss_gamma}")
        print(f"Device: {self.device}\n")

        best_val_loss = float('inf')
        patience_counter = 0
        best_model_path = None

        for epoch in range(epochs):
            train_loss = self._train_epoch(model, train_loader, criterion, optimizer, scheduler)
            val_loss, val_metrics = self._validate(model, val_loader, criterion)

            print(f"\nEpoch {epoch + 1}/{epochs}")
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss: {val_loss:.4f}")
            print(f"  Val F1 (macro): {val_metrics['f1_macro']:.4f}")
            print(f"  Val Precision (macro): {val_metrics['precision_macro']:.4f}")
            print(f"  Val Recall (macro): {val_metrics['recall_macro']:.4f}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                best_model_path = os.path.join(self.output_dir, f"model_{timestamp}")
                os.makedirs(best_model_path, exist_ok=True)

                torch.save(model.state_dict(), os.path.join(best_model_path, "model.pt"))
                tokenizer.save_pretrained(best_model_path)

                print(f"  Saved best model to {best_model_path}")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"\nEarly stopping after {epoch + 1} epochs")
                    break

        print("\nTraining complete!")
        print(f"Best model saved to: {best_model_path}")

        final_metrics = self._compute_detailed_metrics(model, val_loader)

        self._save_training_run(best_model_path, final_metrics)

        return {
            'model_path': best_model_path,
            'metrics': final_metrics
        }

    def _train_epoch(self, model, train_loader, criterion, optimizer, scheduler):
        model.train()
        total_loss = 0

        for batch in train_loader:
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)

            optimizer.zero_grad()

            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

        return total_loss / len(train_loader)

    def _validate(self, model, val_loader, criterion):
        model.eval()
        total_loss = 0
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                logits = model(input_ids, attention_mask)
                loss = criterion(logits, labels)

                total_loss += loss.item()

                preds = (torch.sigmoid(logits) > 0.5).float()
                all_preds.append(preds.cpu().numpy())
                all_labels.append(labels.cpu().numpy())

        all_preds = np.vstack(all_preds)
        all_labels = np.vstack(all_labels)

        metrics = {
            'f1_macro': f1_score(all_labels, all_preds, average='macro', zero_division=0),
            'precision_macro': precision_score(all_labels, all_preds, average='macro', zero_division=0),
            'recall_macro': recall_score(all_labels, all_preds, average='macro', zero_division=0),
        }

        return total_loss / len(val_loader), metrics

    def _compute_detailed_metrics(self, model, val_loader):
        model.eval()
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                logits = model(input_ids, attention_mask)
                preds = (torch.sigmoid(logits) > 0.5).float()

                all_preds.append(preds.cpu().numpy())
                all_labels.append(labels.cpu().numpy())

        all_preds = np.vstack(all_preds)
        all_labels = np.vstack(all_labels)

        report = classification_report(
            all_labels, all_preds,
            target_names=settings.categories,
            output_dict=True,
            zero_division=0
        )

        return report

    def _save_training_run(self, model_path: str, metrics: Dict):
        with DatabaseManager(self.db_path) as db:
            db.save_training_run(model_path, metrics)

