import pandas as pd
import re

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.linear_model import LogisticRegression

import matplotlib.pyplot as plt
import seaborn as sns

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datasets"


# ============================================================
# NLTK DATA
# ============================================================

nltk.download("stopwords")
nltk.download("wordnet")


# ============================================================
# LOAD DATA
# ============================================================

emotion_df = pd.read_csv(DATA_DIR / "emotiondataset1.csv")
music_df = pd.read_csv(DATA_DIR / "music_datasets.csv")

emotion_df = emotion_df.dropna(subset=["text", "emotion"])
music_df = music_df.dropna(subset=["emotion", "song", "link"])


# ============================================================
# TEXT PREPROCESSING
# ============================================================

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()


def preprocess(text):

    text = text.lower()

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)

    words = text.split()

    words = [word for word in words if word not in stop_words]

    words = [lemmatizer.lemmatize(word) for word in words]

    return " ".join(words)


emotion_df["clean_text"] = emotion_df["text"].apply(preprocess)


# ============================================================
# TRAIN-TEST SPLIT
# ============================================================

X = emotion_df["clean_text"]
y = emotion_df["emotion"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42
)


# ============================================================
# MODEL
# ============================================================

model = Pipeline([

    (
        "tfidf",
        TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=15000,
            min_df=2,
            max_df=0.9,
            sublinear_tf=True
        )
    ),

    (
        "clf",
        LogisticRegression(
            max_iter=2000,
            C=4,
            class_weight="balanced",
            solver="lbfgs",
            n_jobs=-1
        )
    )
])


# ============================================================
# TRAIN MODEL
# ============================================================

model.fit(X_train, y_train)


# ============================================================
# EVALUATION
# ============================================================

pred = model.predict(X_test)

accuracy = accuracy_score(y_test, pred)


def evaluate_model():
    """
    Display model accuracy and confusion matrix.
    """

    print("\n==============================")
    print("Logistic Regression Accuracy")
    print("==============================")
    print(f"Accuracy: {accuracy:.2f}")
    print("==============================\n")

    # Accuracy plot
    plt.figure(figsize=(6, 4))

    sns.barplot(
        x=["Logistic Regression"],
        y=[accuracy]
    )

    plt.title("Overall Model Accuracy")
    plt.ylim(0, 1)
    plt.ylabel("Accuracy")

    plt.show()

    # Confusion matrix
    cm = confusion_matrix(y_test, pred)

    plt.figure(figsize=(10, 8))

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=model.classes_,
        yticklabels=model.classes_
    )

    plt.title("Confusion Matrix: Predicted vs Actual Emotions")
    plt.ylabel("Actual Label")
    plt.xlabel("Predicted Label")

    plt.show()


# ============================================================
# EMOTION PREDICTION
# ============================================================

def predict_emotion(text):

    text = preprocess(text)

    emotion = model.predict([text])[0]

    return emotion


# ============================================================
# MUSIC RECOMMENDATION
# ============================================================

def recommend_music(emotion, n=5):

    songs = music_df[music_df["emotion"] == emotion]

    if len(songs) == 0:
        return [("No song found", "https://youtube.com")]

    songs = songs.sample(n=min(n, len(songs)))

    result = []

    for _, row in songs.iterrows():
        result.append(
            (row["song"], row["link"])
        )

    return result


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    evaluate_model()
