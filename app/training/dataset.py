import torch
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Tuple
from transformers import AutoTokenizer
import numpy as np
from app.database.db import DatabaseManager
from app.config import settings


class TherapyLabelDataset(Dataset):
    def __init__(self, data: List[Dict], tokenizer, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.category_to_idx = {cat: idx for idx, cat in enumerate(settings.categories)}

        self.samples = {}
        for row in data:
            sample_id = row['id']
            if sample_id not in self.samples:
                self.samples[sample_id] = {
                    'text': row['text'],
                    'labels': [0] * len(settings.categories)
                }

            if row['is_positive']:
                cat_idx = self.category_to_idx[row['category']]
                self.samples[sample_id]['labels'][cat_idx] = 1

        self.sample_list = list(self.samples.values())

    def __len__(self):
        return len(self.sample_list)

    def __getitem__(self, idx):
        sample = self.sample_list[idx]

        encoding = self.tokenizer(
            sample['text'],
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': torch.tensor(sample['labels'], dtype=torch.float)
        }


def load_data_from_db(db_path: str, train_split: float = 0.8) -> Tuple[List[Dict], List[Dict]]:
    with DatabaseManager(db_path) as db:
        all_data = db.get_all_labeled_data()

    sample_ids = list(set([row['id'] for row in all_data]))
    np.random.shuffle(sample_ids)

    split_idx = int(len(sample_ids) * train_split)
    train_ids = set(sample_ids[:split_idx])
    val_ids = set(sample_ids[split_idx:])

    train_data = [row for row in all_data if row['id'] in train_ids]
    val_data = [row for row in all_data if row['id'] in val_ids]

    return train_data, val_data


def create_data_loaders(db_path: str, tokenizer, batch_size: int = 8,
                       train_split: float = 0.8) -> Tuple[DataLoader, DataLoader]:
    train_data, val_data = load_data_from_db(db_path, train_split)

    train_dataset = TherapyLabelDataset(train_data, tokenizer)
    val_dataset = TherapyLabelDataset(val_data, tokenizer)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader

