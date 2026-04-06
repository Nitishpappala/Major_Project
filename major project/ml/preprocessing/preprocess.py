"""
Text preprocessing pipeline for news articles.
Handles English, Hindi, and Punjabi text.
Input: raw .xlsx files from scrapers
Output: Final_Prepped_Data.xlsx with cleaned text
"""

import os
import re
import pandas as pd
import contractions
import nltk
from nltk.tokenize import ToktokTokenizer
import spacy

# Download required NLTK data (first run only)
nltk.download('stopwords', quiet=True)


def preprocess_english(series):
    """Preprocess English text: lowercase, contractions, punctuation, lemmatize, stopwords."""
    print("  - Lowercasing...")
    series = series.apply(lambda x: str(x).lower())

    print("  - Expanding contractions...")
    series = series.apply(lambda x: contractions.fix(x))

    print("  - Removing punctuation...")
    series = series.str.replace(r'[^\w\s]', '', regex=True)
    series = series.str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)

    print("  - Removing numbers...")
    pattern = r'[^a-zA-z.,!?/:;\"\'\s]'
    series = series.apply(lambda x: re.sub(pattern, '', x))

    print("  - Lemmatizing (spaCy)...")
    nlp = spacy.load('en_core_web_sm')

    def get_lem(text):
        doc = nlp(text)
        return ' '.join([word.lemma_ if word.lemma_ != '-PRON-' else word.text for word in doc])
    series = series.apply(get_lem)

    print("  - Removing stopwords (keeping 'not')...")
    tokenizer = ToktokTokenizer()
    stopword_list = nltk.corpus.stopwords.words('english')
    stopword_list.remove('not')

    def remove_stopwords(text):
        tokens = tokenizer.tokenize(text)
        tokens = [t.strip() for t in tokens if t.strip().lower() not in stopword_list]
        return ' '.join(tokens)
    series = series.apply(remove_stopwords)

    return series


def preprocess_hindi(series):
    """Preprocess Hindi text: remove special chars, Devanagari numerals, stopwords."""
    series = series.str.replace(r'[^\w\s]', '', regex=True)
    series = series.str.replace("\n", '')
    series = series.str.replace("\xa0", '')

    devanagari_nums = ('०', '१', '२', '३', '४', '५', '६', '७', '८', '९')

    def remove_nums(row):
        for c, n in enumerate(devanagari_nums):
            row = re.sub(n, str(c), row)
        return row

    stopwords_hi = [
        'तुम', 'मेरी', 'मुझे', 'क्योंकि', 'हम', 'प्रति', 'अबकी', 'आगे', 'माननीय',
        'शहर', 'बताएं', 'कौनसी', 'क्लिक', 'किसकी', 'बड़े', 'मैं', 'and', 'रही', 'आज',
        'लें', 'आपके', 'मिलकर', 'सब', 'मेरे', 'जी', 'श्री', 'वैसा', 'आपका', 'अंदर',
        'अत', 'अपना', 'अपनी', 'अपने', 'अभी', 'आदि', 'आप', 'इत्यादि', 'इन', 'इनका',
        'इन्हीं', 'इन्हें', 'इन्हों', 'इस', 'इसका', 'इसकी', 'इसके', 'इसमें', 'इसी',
        'इसे', 'उन', 'उनका', 'उनकी', 'उनके', 'उनको', 'उन्हीं', 'उन्हें', 'उन्हों',
        'उस', 'उसके', 'उसी', 'उसे', 'एक', 'एवं', 'एस', 'ऐसे', 'और', 'कई', 'कर',
        'करता', 'करते', 'करना', 'करने', 'करें', 'कहते', 'कहा', 'का', 'काफ़ी', 'कि',
        'कितना', 'किन्हें', 'किन्हों', 'किया', 'किर', 'किस', 'किसी', 'किसे', 'की',
        'कुछ', 'कुल', 'के', 'को', 'कोई', 'कौन', 'कौनसा', 'गया', 'घर', 'जब', 'जहाँ',
        'जा', 'जितना', 'जिन', 'जिन्हें', 'जिन्हों', 'जिस', 'जिसे', 'जीधर', 'जैसा',
        'जैसे', 'जो', 'तक', 'तब', 'तरह', 'तिन', 'तिन्हें', 'तिन्हों', 'तिस', 'तिसे',
        'तो', 'था', 'थी', 'थे', 'दबारा', 'दिया', 'दुसरा', 'दूसरे', 'दो', 'द्वारा',
        'न', 'नहीं', 'ना', 'निहायत', 'नीचे', 'ने', 'पर', 'पहले', 'पूरा', 'पे', 'फिर',
        'बनी', 'बही', 'बहुत', 'बाद', 'बाला', 'बिलकुल', 'भी', 'भीतर', 'मगर', 'मानो',
        'मे', 'में', 'यदि', 'यह', 'यहाँ', 'यही', 'या', 'यिह', 'ये', 'रखें', 'रहा',
        'रहे', 'ऱ्वासा', 'लिए', 'लिये', 'लेकिन', 'व', 'वर्ग', 'वह', 'वहाँ', 'वहीं',
        'वाले', 'वुह', 'वे', 'वग़ैरह', 'संग', 'सकता', 'सकते', 'सबसे', 'सभी', 'साथ',
        'साबुत', 'साभ', 'सारा', 'से', 'सो', 'ही', 'हुआ', 'हुई', 'हुए', 'है', 'हैं',
        'हो', 'होता', 'होती', 'होते', 'होना', 'होने',
    ]
    stopwords_en = nltk.corpus.stopwords.words('english')
    punctuations = ['nn', 'n', '।', '/', '`', '+', '\\', '"', '?', '(', '$', '@',
                    '[', '_', '!', ',', ':', '^', '|', ']', '=', '%', '&', '.', ')',
                    '#', '*', ';', '-', '}']
    to_be_removed = set(stopwords_hi + stopwords_en + punctuations)

    def remove_stopwords(text):
        words = str(text).split()
        return ' '.join(w for w in words if w not in to_be_removed)

    series = series.apply(remove_stopwords)
    series = series.apply(lambda x: remove_nums(str(x)))
    series = series.str.replace(r'\d+', '', regex=True)
    return series


def preprocess_punjabi(series):
    """Preprocess Punjabi text: remove special chars and numerals."""
    series = series.str.replace(r'[^\w\s]', '', regex=True)
    devanagari_nums = ('०', '१', '२', '३', '४', '५', '६', '७', '८', '९')

    def remove_nums(row):
        for c, n in enumerate(devanagari_nums):
            row = re.sub(n, str(c), row)
        return row
    series = series.apply(lambda x: remove_nums(str(x)))
    series = series.str.replace(r'\d+', '', regex=True)
    return series


def _clean_dataframe(df, preprocess_fn, source_name, filter_hindi_shows=False):
    """Apply common cleaning steps to a dataframe."""
    print(f"\n  Processing {source_name} ({len(df)} rows)...")

    # Skip empty dataframes
    if df.empty or 'Body' not in df.columns or 'Heading' not in df.columns:
        print(f"  {source_name}: SKIPPED (empty or missing columns)")
        return pd.DataFrame()

    # Remove rows where Body is not text
    df = df[~df['Body'].apply(lambda x: isinstance(x, (float, int)))]

    # Remove horoscope articles
    df = df[~df['Heading'].str.contains('horoscope', case=False, na=False)]

    # Remove specific shows (for Hindi sources)
    if filter_hindi_shows:
        df = df.loc[~(df['Heading'].str.contains("Aaj Ki Baat", na=False) |
                       df['Heading'].str.contains("Horoscope", na=False) |
                       df['Heading'].str.contains("Aap Ki Adalat", na=False))]

    # Remove "dear subscriber" content
    df = df[~df['Body'].str.contains('dear subscriber', case=False, na=False)]

    # Remove "Edited By:" sections
    def remove_edited(row):
        idx = str(row).find("Edited By: ")
        return row[:idx] if idx != -1 else row
    df['Body'] = df['Body'].apply(lambda x: remove_edited(str(x)))

    # Apply language-specific preprocessing
    df['Body'] = preprocess_fn(df['Body'])
    df = df.dropna()
    df = df[df['Body'] != ""]

    print(f"  {source_name}: {len(df)} rows after cleaning")
    return df


def preprocess_all(data_dir, output_path=None):
    """
    Load all scraped .xlsx files from data_dir, preprocess them,
    and save the merged result as Final_Prepped_Data.xlsx.

    Returns the merged DataFrame.
    """
    if output_path is None:
        output_path = os.path.join(data_dir, "Final_Prepped_Data.xlsx")

    print("\n========== PREPROCESSING PIPELINE ==========")
    frames = []

    # English sources
    english_sources = {
        "IndiaToday": "IndiaToday.xlsx",
        "News18": "News18.xlsx",
        "IndiaTv": "IndiaTv.xlsx",
        "ThePrint": "ThePrint.xlsx",
    }
    for name, filename in english_sources.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            df = pd.read_excel(filepath)
            df = _clean_dataframe(df, preprocess_english, name)
            frames.append(df)
        else:
            print(f"  [SKIP] {filename} not found")

    # Hindi text source (AajTak text - already translated to English by scraper)
    for name, filename in [("AajTak", "AajTak.xlsx")]:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            df = pd.read_excel(filepath)
            df = _clean_dataframe(df, preprocess_english, name)
            frames.append(df)
        else:
            print(f"  [SKIP] {filename} not found")

    # Video sources (already translated to English by video scrapers)
    video_sources = {
        "AajTak_Video": "AajTak_Video.xlsx",
        "IndianExpress_Video": "IndianExpress_Video.xlsx",
        "ZeeNews_Video": "ZeeNews_Video.xlsx",
    }
    for name, filename in video_sources.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            df = pd.read_excel(filepath)
            df = _clean_dataframe(df, preprocess_english, name, filter_hindi_shows=(name == "AajTak_Video"))
            frames.append(df)
        else:
            print(f"  [SKIP] {filename} not found")

    # Punjabi source
    filepath = os.path.join(data_dir, "News18_Punjab.xlsx")
    if os.path.exists(filepath):
        df = pd.read_excel(filepath)
        df = _clean_dataframe(df, preprocess_punjabi, "News18_Punjab")
        frames.append(df)

    if not frames:
        print("\n  ERROR: No data files found! Run data collection first.")
        return pd.DataFrame()

    # Merge all dataframes
    print(f"\n  Merging {len(frames)} sources...")
    df_final = pd.concat(frames, ignore_index=True, axis=0, join='outer')
    df_final = df_final.dropna(subset=['Heading'])
    df_final = df_final[df_final['Body'] != ""]

    # Save
    df_final.to_excel(output_path, index=False)
    print(f"\n  Saved: {output_path}")
    print(f"  Total articles: {len(df_final)}")
    print("========== PREPROCESSING COMPLETE ==========\n")

    return df_final


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    preprocess_all(data_dir)
