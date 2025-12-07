import os
import sys
from concurrent import futures
from pathlib import Path
import grpc
from grpc_reflection.v1alpha import reflection
import joblib
import numpy as np



CURRENT_DIR = Path(__file__).resolve().parent           # .../server
ROOT_DIR = CURRENT_DIR.parent                           # корень проекта

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import model_pb2
import model_pb2_grpc


# --- Настройки модели и сервера ---

DEFAULT_MODEL_PATH = ROOT_DIR / "models" / "model.pkl"

MODEL_PATH = os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH))
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")
PORT = int(os.getenv("PORT", "50051"))

# Порядок признаков — как в sklearn.datasets.load_wine().feature_names
FEATURE_NAMES = [
    "alcohol",
    "malic_acid",
    "ash",
    "alcalinity_of_ash",
    "magnesium",
    "total_phenols",
    "flavanoids",
    "nonflavanoid_phenols",
    "proanthocyanins",
    "color_intensity",
    "hue",
    "od280/od315_of_diluted_wines",
    "proline",
]


class PredictionService(model_pb2_grpc.PredictionServiceServicer):
    def __init__(self):
        if not Path(MODEL_PATH).exists():
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        self.model = joblib.load(MODEL_PATH)
        self.model_version = MODEL_VERSION

    def Health(self, request, context):
        """
        Простой health-check.
        """
        return model_pb2.HealthResponse(
            status="ok",
            model_version=self.model_version,
        )

    def _features_to_array(self, features):
        """
        Преобразует список Feature в numpy-массив (1 x 13)
        в правильном порядке признаков.
        """
        if not features:
            raise ValueError("No features provided")

        feat_dict = {}
        for f in features:
            if not f.name:
                raise ValueError("Feature name cannot be empty")
            if f.name in feat_dict:
                raise ValueError(f"Duplicate feature name: {f.name}")
            feat_dict[f.name] = float(f.value)

        # Проверяем, что есть все нужные признаки
        missing = [name for name in FEATURE_NAMES if name not in feat_dict]
        if missing:
            raise ValueError(f"Missing features: {', '.join(missing)}")

        # Собираем в правильном порядке
        values = [feat_dict[name] for name in FEATURE_NAMES]
        x = np.array([values], dtype=float)  # shape: (1, 13)
        return x

    def Predict(self, request, context):
        """
        Основной метод предсказания.
        """
        try:
            x = self._features_to_array(request.features)

            # Предсказанный класс
            y_pred = self.model.predict(x)[0]

            # Уверенность (максимальная вероятность)
            if hasattr(self.model, "predict_proba"):
                proba = self.model.predict_proba(x)[0]
                confidence = float(np.max(proba))
            else:
                confidence = 1.0

            return model_pb2.PredictResponse(
                prediction=str(int(y_pred)),
                confidence=confidence,
                model_version=self.model_version,
            )

        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return model_pb2.PredictResponse()

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal server error: {e}")
            return model_pb2.PredictResponse()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    model_pb2_grpc.add_PredictionServiceServicer_to_server(
        PredictionService(),
        server,
    )

    SERVICE_NAMES = (
        model_pb2.DESCRIPTOR.services_by_name['PredictionService'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    listen_addr = f"[::]:{PORT}"
    server.add_insecure_port(listen_addr)

    print(f"gRPC server is starting on {listen_addr}")
    print(f"Using model: {MODEL_PATH}, version: {MODEL_VERSION}")

    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
