from pathlib import Path
import joblib
import pandas as pd
from sklearn.datasets import load_wine
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


def main() -> None:
    wine = load_wine(as_frame=True)
    X: pd.DataFrame = wine.data
    y = wine.target

    #Делим на обучающие и тестовые выборки
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    #Обучаем модель
    model = LogisticRegression(max_iter=1000, multi_class="auto", random_state=42)
    model.fit(X_train, y_train)

    #Сохраняем модель
    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / "model.pkl"
    joblib.dump(model, model_path)

    #Считаем метрики
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"Модель сохранена в: {model_path}")
    print(f"Accuracy на train: {train_score:.3f}")
    print(f"Accuracy на test: {test_score:.3f}")


if __name__ == "__main__":
    main()
