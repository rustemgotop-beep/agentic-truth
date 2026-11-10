import os
import atexit
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from rag.corpus import MATH_SEED_CORPUS

COLLECTION_NAME = "math_theorems"
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "qdrant_db")


class QdrantMathStore:
    """
    Полноценная локальная векторная база данных Qdrant для хранения и поиска
    академических теорем математического анализа.
    
    Особенности реализации:
    - Embedded-режим (локально на диске в qdrant_db) без Docker.
    - Автоматический fallback в in-memory при блокировке дисковых файлов другим процессом.
    - Автоматическая синхронизация размерности векторов при изменении корпуса.
    - Char-WB TF-IDF векторизация (3-5 n-grams), идеально учитывающая русскую морфологию и мат. термины.
    - Поддержка динамического добавления теорем в реальном времени.
    - Корректное освобождение дескрипторов при завершении процесса через atexit.
    """

    def __init__(self, persistent_path: str = DEFAULT_DB_PATH):
        self.persistent_path = persistent_path
        self.collection_name = COLLECTION_NAME
        self.theorems_registry: List[Dict[str, Any]] = [dict(t) for t in MATH_SEED_CORPUS]
        
        # 1. Настройка векторизатора
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True
        )
        self._fit_vectorizer()

        # 2. Инициализация клиента Qdrant
        self.client = self._init_client()
        atexit.register(self.close)

        # 3. Гарантия создания коллекции и валидации размерности
        self._ensure_indexed()

    def _format_text_for_embedding(self, item: Dict[str, Any]) -> str:
        """Объединяет заголовок, категорию, теги, формулы, контент и цитату для максимальной релевантности поиска."""
        category = item.get("category", "")
        tags = "".join(item.get("tags", []))
        formula = item.get("latex_formula", "")
        return f"{item.get('theorem', '')} {category} {tags} {formula} {item.get('content', '')} {item.get('citation', '')}"

    def _fit_vectorizer(self):
        """Обучает векторизатор на всех зарегистрированных теоремах."""
        texts = [self._format_text_for_embedding(t) for t in self.theorems_registry]
        self.vectors = self.vectorizer.fit_transform(texts).toarray()
        self.vector_dim = self.vectors.shape[1]

    def _init_client(self) -> QdrantClient:
        """Безопасная инициализация клиента с защитой от блокировки файлов."""
        if self.persistent_path == ":memory:":
            return QdrantClient(location=":memory:")
        try:
            os.makedirs(self.persistent_path, exist_ok=True)
            return QdrantClient(path=self.persistent_path)
        except Exception as e:
            print(f"[Qdrant] Локальный файл базы занят другим процессом ({e}). Запущен in-memory режим.")
            return QdrantClient(location=":memory:")

    def _ensure_indexed(self, force: bool = False):
        """Создает коллекцию и индексирует теоремы, если коллекция отсутствует или размерность устарела."""
        try:
            collections_info = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections_info)

            recreate = force or not exists
            if exists and not recreate:
                info = self.client.get_collection(self.collection_name)
                existing_size = info.config.params.vectors.size
                existing_count = self.client.count(collection_name=self.collection_name).count
                if existing_size != self.vector_dim or existing_count != len(self.theorems_registry):
                    recreate = True

            if recreate:
                if exists:
                    self.client.delete_collection(collection_name=self.collection_name)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dim,
                        distance=Distance.COSINE
                    )
                )
                self._upsert_corpus()
        except Exception as e:
            print(f"Ошибка индексации Qdrant: {e}")

    def _upsert_corpus(self):
        """Пакетная вставка всех теорем корпуса в Qdrant."""
        points = []
        for i, (item, vec) in enumerate(zip(self.theorems_registry, self.vectors)):
            points.append(
                PointStruct(
                    id=i + 1,
                    vector=vec.tolist(),
                    payload=item
                )
            )
        self.client.upsert(collection_name=self.collection_name, points=points)
        print(f"[Qdrant] Синхронизировано {len(points)} теорем (размерность векторов: {self.vector_dim})")

    def search(self, query: str, top_k: int = 3, min_score: float = 0.02) -> List[Dict[str, Any]]:
        """
        Семантический векторный поиск по коллекции теорем Qdrant.
        """
        if not query or not query.strip():
            return []

        try:
            query_vec = self.vectorizer.transform([query]).toarray()[0].tolist()
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vec,
                limit=top_k
            )

            results: List[Dict[str, Any]] = []
            for pt in response.points:
                score = float(pt.score)
                if score >= min_score:
                    results.append({
                        "id": pt.payload.get("id", str(pt.id)),
                        "score": round(score, 4),
                        "category": pt.payload.get("category", "Математический анализ"),
                        "theorem": pt.payload.get("theorem", ""),
                        "source": pt.payload.get("source", ""),
                        "content": pt.payload.get("content", ""),
                        "citation": pt.payload.get("citation", ""),
                        "latex_formula": pt.payload.get("latex_formula", ""),
                        "tags": pt.payload.get("tags", [])
                    })
            return results
        except Exception as e:
            print(f"Ошибка при поиске в Qdrant: {e}")
            return []

    def get_categories(self) -> List[str]:
        """Возвращает уникальные разделы математического анализа из базы."""
        cats = []
        for t in self.theorems_registry:
            cat = t.get("category", "Математический анализ")
            if cat not in cats:
                cats.append(cat)
        return cats

    def get_theorem_by_id(self, theorem_id: str) -> Optional[Dict[str, Any]]:
        """Поиск теоремы по её уникальному идентификатору."""
        for t in self.theorems_registry:
            if t.get("id") == theorem_id:
                return dict(t)
        return None

    def list_theorems(self) -> List[Dict[str, Any]]:
        """Возвращает список всех теорем в базе данных."""
        return [dict(t) for t in self.theorems_registry]

    def count(self) -> int:
        """Возвращает число записей в векторной базе."""
        try:
            return self.client.count(collection_name=self.collection_name).count
        except Exception:
            return len(self.theorems_registry)

    def stats(self) -> Dict[str, Any]:
        """Возвращает сводные метрики и состояние векторной БД."""
        return {
            "collection_name": self.collection_name,
            "persistent_path": self.persistent_path,
            "points_count": self.count(),
            "vector_dimension": self.vector_dim,
            "distance_metric": "COSINE",
            "vectorizer": "TF-IDF (char_wb n-grams 3-5)",
            "status": "ready"
        }

    def add_theorem(self, theorem: Dict[str, Any]) -> bool:
        """
        Динамическое добавление новой пользовательской теоремы в векторную базу данных.
        """
        if not theorem.get("theorem") or not theorem.get("content"):
            return False

        if not theorem.get("id"):
            theorem["id"] = f"custom_thm_{len(self.theorems_registry) + 1}"

        self.theorems_registry.append(theorem)
        self._fit_vectorizer()
        
        try:
            collections_info = self.client.get_collections().collections
            if any(c.name == self.collection_name for c in collections_info):
                self.client.delete_collection(collection_name=self.collection_name)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_dim,
                    distance=Distance.COSINE
                )
            )
            self._upsert_corpus()
            return True
        except Exception as e:
            print(f"Ошибка динамического добавления в Qdrant: {e}")
            return False

    def close(self):
        """Корректное закрытие клиента Qdrant при завершении программы."""
        try:
            if hasattr(self, "client") and self.client is not None:
                self.client.close()
        except Exception:
            pass


# Глобальный синглтон векторного хранилища
qdrant_store = QdrantMathStore()
