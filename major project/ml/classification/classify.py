"""
News Classification using DistilBERT.
Categorizes articles into 10 classes:
  Entertainment, Business, Politics, Judiciary, Crime,
  Culture, Sports, Science, International, Technology

Requires: distilbert_model.h5 (trained model file)
"""

import os
import numpy as np
from transformers import DistilBertTokenizer

CATEGORIES = {
    0: "Entertainment",
    1: "Business",
    2: "Politics",
    3: "Judiciary",
    4: "Crime",
    5: "Culture",
    6: "Sports",
    7: "Science",
    8: "International",
    9: "Technology",
}

MAX_LENGTH = 512


class NewsClassifier:
    """Wraps the DistilBERT classification model."""

    def __init__(self, model_path=None):
        print("[Classification] Loading DistilBERT tokenizer...")
        self.tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

        self.model = None
        if model_path and os.path.exists(model_path):
            print(f"[Classification] Loading model from {model_path}...")
            try:
                from keras.models import load_model
                from transformers import TFDistilBertModel
                custom_objects = {'TFDistilBertModel': TFDistilBertModel}
                self.model = load_model(model_path, custom_objects=custom_objects)
                print("[Classification] Model loaded successfully.")
            except Exception as e:
                print(f"[Classification] WARNING: Could not load model: {e}")
                print("[Classification] Will use fallback keyword-based classification.")
        else:
            print("[Classification] WARNING: No model file found.")
            print("[Classification] Will use fallback keyword-based classification.")
            if model_path:
                print(f"  Expected path: {model_path}")

    def _predict_with_model(self, text):
        """Predict using the trained DistilBERT model."""
        inputs = self.tokenizer(text, return_tensors='tf', truncation=True,
                                padding='max_length', max_length=MAX_LENGTH)
        input_ids = inputs['input_ids']
        attention_mask = inputs['attention_mask']
        predictions = self.model.predict([input_ids, attention_mask], verbose=0)
        class_idx = predictions[0].argmax()
        return CATEGORIES[class_idx]

    def _predict_with_keywords(self, text):
        """Fallback keyword-based classification when model is not available."""
        text_lower = str(text).lower()
        keyword_map = {
            "Sports": ["cricket", "football", "match", "player", "team", "sport", "olympic",
                        "tournament", "goal", "wicket", "ipl", "fifa", "tennis", "hockey"],
            "Politics": ["minister", "parliament", "election", "political", "government", "bjp",
                         "congress", "vote", "campaign", "modi", "rahul", "opposition", "bill"],
            "Business": ["market", "stock", "economy", "company", "profit", "revenue", "trade",
                         "investment", "gdp", "inflation", "rbi", "bank", "startup", "ipo"],
            "Technology": ["technology", "software", "app", "digital", "ai", "artificial",
                           "computer", "internet", "cyber", "tech", "google", "apple", "robot"],
            "Entertainment": ["movie", "film", "bollywood", "actor", "actress", "celebrity",
                              "music", "song", "album", "award", "netflix", "series", "show"],
            "Crime": ["murder", "arrested", "police", "crime", "theft", "robbery", "fraud",
                      "accused", "suspect", "criminal", "jail", "prison", "investigation"],
            "Judiciary": ["court", "judge", "verdict", "supreme", "high court", "petition",
                          "hearing", "bail", "lawyer", "legal", "judicial", "bench"],
            "International": ["us ", "china", "pakistan", "russia", "ukraine", "united nations",
                              "global", "world", "foreign", "international", "nato", "eu "],
            "Science": ["science", "research", "nasa", "isro", "space", "discovery",
                        "scientist", "study", "experiment", "climate", "environment"],
            "Culture": ["culture", "festival", "tradition", "heritage", "temple", "religion",
                        "art", "museum", "dance", "diwali", "eid", "christmas"],
        }
        scores = {}
        for category, keywords in keyword_map.items():
            scores[category] = sum(1 for kw in keywords if kw in text_lower)

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "Politics"  # default fallback

    def classify(self, text):
        """Classify a single article text into one of 10 categories."""
        text = str(text)
        if not text.strip():
            return "Politics"  # default

        if self.model is not None:
            return self._predict_with_model(text)
        else:
            return self._predict_with_keywords(text)

    def classify_series(self, series):
        """Classify a pandas Series of texts. Returns list of category strings."""
        results = []
        total = len(series)
        for i, text in enumerate(series):
            if (i + 1) % 10 == 0 or i == 0:
                print(f"  [Classification] Processing {i + 1}/{total}...")
            results.append(self.classify(text))
        print(f"  [Classification] Done - {total} articles classified")
        return results


if __name__ == "__main__":
    classifier = NewsClassifier()
    test_texts = [
        "India beat Australia by 5 wickets in the third ODI at Wankhede stadium.",
        "Supreme Court upholds the constitutional validity of the new amendment.",
        "Sensex crosses 70000 mark as global markets rally on Fed decision.",
        "NASA launches new Mars rover to search for signs of ancient life.",
        "Bollywood star announces new film directed by acclaimed filmmaker.",
    ]
    for text in test_texts:
        cat = classifier.classify(text)
        print(f"\n  [{cat}] {text[:80]}...")
