import nltk
from typing import List
import re


class SentenceChunker:
    def __init__(self, min_length: int = 10):
        self.min_length = min_length
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)

    def chunk(self, text: str) -> List[str]:
        sentences = nltk.sent_tokenize(text)

        cleaned_sentences = []
        for sentence in sentences:
            cleaned = self._clean_sentence(sentence)
            if len(cleaned) >= self.min_length:
                cleaned_sentences.append(cleaned)

        return cleaned_sentences

    def _clean_sentence(self, sentence: str) -> str:
        sentence = sentence.strip()
        sentence = re.sub(r'\s+', ' ', sentence)
        return sentence

