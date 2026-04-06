"""
Random Forest classifier for news article categorization.
This module provides a drop-in alternative to the DistilBERT-based classifier.

It supports:
- loading/saving a trained TF-IDF + RandomForest model
- training from text and label data
- classifying individual texts or pandas Series
- fallback keyword classification when a model is unavailable
"""

import os
import numpy as np

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

DEFAULT_KEYWORDS = {
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


class RandomForestNewsClassifier:
    """News classifier using TF-IDF features and a Random Forest model."""

    def __init__(self, model_path=None, vectorizer_path=None):
        self.model = None
        self.vectorizer = None
        self.loaded = False
        self.fallback = True

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.ensemble import RandomForestClassifier
            import joblib
            self._sklearn_available = True
            self._TfidfVectorizer = TfidfVectorizer
            self._RandomForestClassifier = RandomForestClassifier
            self._joblib = joblib
        except ImportError:
            self._sklearn_available = False
            self.fallback = True
            print("[RandomForest] sklearn or joblib is not installed. Falling back to keyword classification.")

        if model_path and vectorizer_path and self._sklearn_available:
            if os.path.exists(model_path) and os.path.exists(vectorizer_path):
                try:
                    self.model = self._joblib.load(model_path)
                    self.vectorizer = self._joblib.load(vectorizer_path)
                    self.loaded = True
                    self.fallback = False
                    print(f"[RandomForest] Loaded Random Forest model from {model_path}")
                except Exception as e:
                    print(f"[RandomForest] Could not load saved model: {e}")
                    print("[RandomForest] Using fallback keyword classifier instead.")
            else:
                print("[RandomForest] Saved model or vectorizer file not found.")
                print(f"  model_path={model_path}")
                print(f"  vectorizer_path={vectorizer_path}")
                print("[RandomForest] Using fallback keyword classifier instead.")

    def train(self, texts, labels, model_path=None, vectorizer_path=None, n_estimators=100, random_state=42):
        """Train a new Random Forest classifier from raw texts and category labels."""
        if not self._sklearn_available:
            raise RuntimeError("scikit-learn is required to train the Random Forest model.")

        texts = [str(text) for text in texts]
        labels = [str(label) for label in labels]

        self.vectorizer = self._TfidfVectorizer(max_features=10000, ngram_range=(1, 2), stop_words='english')
        X = self.vectorizer.fit_transform(texts)

        self.model = self._RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1,
        )
        self.model.fit(X, labels)
        self.loaded = True
        self.fallback = False

        if model_path:
            self._joblib.dump(self.model, model_path)
        if vectorizer_path:
            self._joblib.dump(self.vectorizer, vectorizer_path)

        return self.model

    def save(self, model_path, vectorizer_path):
        """Save the trained model and vectorizer to disk."""
        if not self.loaded or self.model is None or self.vectorizer is None:
            raise RuntimeError("No trained model available to save.")
        self._joblib.dump(self.model, model_path)
        self._joblib.dump(self.vectorizer, vectorizer_path)

    def _predict_with_model(self, text):
        inputs = [str(text)]
        X = self.vectorizer.transform(inputs)
        prediction = self.model.predict(X)
        return str(prediction[0])

    def _predict_with_keywords(self, text):
        text_lower = str(text).lower()
        scores = {category: 0 for category in DEFAULT_KEYWORDS}
        for category, keywords in DEFAULT_KEYWORDS.items():
            scores[category] = sum(1 for kw in keywords if kw in text_lower)

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "Politics"

    def classify(self, text):
        """Classify a single article text into one of the category labels."""
        if not str(text).strip():
            return "Politics"

        if self.loaded and self.model is not None and self.vectorizer is not None:
            return self._predict_with_model(text)

        return self._predict_with_keywords(text)

    def classify_series(self, series):
        """Classify a pandas Series or list of texts."""
        results = []
        for i, text in enumerate(series):
            if (i + 1) % 10 == 0 or i == 0:
                print(f"  [RandomForest] Processing {i + 1}/{len(series)}...")
            results.append(self.classify(text))
        return results

    def predict_proba(self, text):
        """Return prediction probabilities for each category if a trained model is available."""
        if not self.loaded or self.model is None or self.vectorizer is None:
            raise RuntimeError("No trained Random Forest model loaded for probability prediction.")
        X = self.vectorizer.transform([str(text)])
        proba = self.model.predict_proba(X)[0]
        return dict(zip(self.model.classes_, proba))


if __name__ == "__main__":
    classifier = RandomForestNewsClassifier()
    sample_texts = [
        "India beat Australia by 5 wickets in the third ODI at Wankhede stadium.",
        "Supreme Court upholds the constitutional validity of the new amendment.",
        "Sensex crosses 70000 mark as global markets rally on Fed decision.",
        "NASA launches new Mars rover to search for signs of ancient life.",
        "Bollywood star announces new film directed by acclaimed filmmaker.",
    ]
    for text in sample_texts:
        print(f"[{classifier.classify(text)}] {text}")
