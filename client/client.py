import sys
import os
from pathlib import Path

import grpc
import model_pb2
import model_pb2_grpc

# --- Добавляем корень проекта в sys.path, чтобы видеть model_pb2.py ---

CURRENT_DIR = Path(__file__).resolve().parent   # .../client
ROOT_DIR = CURRENT_DIR.parent                   # корень проекта

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))



# Пример объекта из датасета wine (13 признаков)
EXAMPLE_WINE_FEATURES = {
    "alcohol": 14.23,
    "malic_acid": 1.71,
    "ash": 2.43,
    "alcalinity_of_ash": 15.6,
    "magnesium": 127.0,
    "total_phenols": 2.8,
    "flavanoids": 3.06,
    "nonflavanoid_phenols": 0.28,
    "proanthocyanins": 2.29,
    "color_intensity": 5.64,
    "hue": 1.04,
    "od280/od315_of_diluted_wines": 3.92,
    "proline": 1065.0,
}


def make_stub(address: str = "localhost:50051") -> model_pb2_grpc.PredictionServiceStub:
    channel = grpc.insecure_channel(address)
    return model_pb2_grpc.PredictionServiceStub(channel)


def call_health(stub: model_pb2_grpc.PredictionServiceStub) -> None:
    response = stub.Health(model_pb2.HealthRequest(), timeout=2.0)
    print(f"[Health] status={response.status}, model_version={response.model_version}")


def call_predict(
    stub: model_pb2_grpc.PredictionServiceStub,
    features: dict[str, float],
) -> None:
    feature_messages = [
        model_pb2.Feature(name=name, value=float(value))
        for name, value in features.items()
    ]

    request = model_pb2.PredictRequest(features=feature_messages)
    response = stub.Predict(request, timeout=3.0)

    print(
        f"[Predict] prediction={response.prediction}, "
        f"confidence={round(response.confidence, 4)}, "
        f"model_version={response.model_version}"
    )


if __name__ == "__main__":
    localhost = os.environ.get("CUSTOM_LOCALHOST", "localhost")
    stub = make_stub(f"{localhost}:50051")
    call_health(stub)
    call_predict(stub, EXAMPLE_WINE_FEATURES)
