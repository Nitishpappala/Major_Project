"""
Sentiment Analysis using RoBERTa (cardiffnlp/twitter-roberta-base-sentiment).
Input: text string or pandas Series
Output: [positive_score, negative_score, neutral_score] per article
"""

import os
import csv
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


class SentimentAnalyzer:
    """Wraps the RoBERTa sentiment model for reuse across articles."""

    def __init__(self, mapping_file=None):
        print("[Sentiment] Loading RoBERTa model...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            "cardiffnlp/twitter-roberta-base-sentiment"
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "cardiffnlp/twitter-roberta-base-sentiment"
        )
        self.model.eval()

        # Load label mapping
        self.labels = []
        if mapping_file and os.path.exists(mapping_file):
            with open(mapping_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                self.labels = [row[1] for row in reader if len(row) > 1]
        else:
            # Default mapping from the model
            self.labels = ["negative", "neutral", "positive"]

        print(f"[Sentiment] Model loaded. Labels: {self.labels}")

    def analyze(self, text):
        """
        Analyze sentiment of a single text string.
        Returns: [positive_score, negative_score, neutral_score]
        """
        # Truncate to first 1500 chars (model limit considerations)
        text = str(text)[:1500]
        if not text.strip():
            return [0.0, 0.0, 0.0]

        encoded = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        with torch.no_grad():
            output = self.model(**encoded)

        scores = torch.softmax(output.logits[0], dim=0)
        ranking = torch.argsort(scores, descending=True)

        ans = [0.0, 0.0, 0.0]  # [positive, negative, neutral]
        for i in range(scores.shape[0]):
            label = self.labels[ranking[i].item()]
            score = scores[ranking[i]].item()
            if label == "positive":
                ans[0] = score
            elif label == "negative":
                ans[1] = score
            elif label == "neutral":
                ans[2] = score

        return ans

    def analyze_series(self, series):
        """Analyze sentiment for a pandas Series. Returns list of [pos, neg, neutral] arrays."""
        results = []
        total = len(series)
        for i, text in enumerate(series):
            if (i + 1) % 10 == 0 or i == 0:
                print(f"  [Sentiment] Processing {i + 1}/{total}...")
            results.append(self.analyze(text))
        print(f"  [Sentiment] Done - {total} articles analyzed")
        return results


if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    test_texts = [
        "The government announced a new policy that will benefit millions of citizens.",
        "Massive corruption scandal rocks the ministry, public outraged.",
        "The weather today is partly cloudy with moderate temperatures."
    ]
    for text in test_texts:
        scores = analyzer.analyze(text)
        print(f"\nText: {text[:80]}...")
        print(f"  Positive: {scores[0]:.4f}  Negative: {scores[1]:.4f}  Neutral: {scores[2]:.4f}")
