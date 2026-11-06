"""
Автоматизированный комплекс тестов для векторной базы данных Qdrant и RAG-слоя.
Проверяет:
1. Индексацию академического корпуса теорем матанализа (Зорич, Фихтенгольц, Кудрявцев).
2. Семантический векторный поиск по ключевым запросам (Ролль, Вейерштрасс, Тейлор, Коши).
3. Динамическое добавление новых теорем в Qdrant.
4. Работу ретривера retrieve_math_knowledge.
"""
import sys
import unittest
from rag.qdrant_store import qdrant_store, QdrantMathStore
from rag.retriever import retrieve_math_knowledge
from rag.corpus import MATH_SEED_CORPUS


class TestQdrantDatabase(unittest.TestCase):

    def setUp(self):
        self.store = qdrant_store

    def test_01_corpus_indexing_count(self):
        """Проверка полноты индексации стартового корпуса."""
        self.assertGreaterEqual(self.store.count(), len(MATH_SEED_CORPUS))
        stats = self.store.stats()
        self.assertEqual(stats["status"], "ready")
        self.assertEqual(stats["distance_metric"], "COSINE")
        self.assertGreater(stats["vector_dimension"], 100)
        print(f"\n[Test 1 OK] Векторная БД содержит {stats['points_count']} теорем, размерность {stats['vector_dimension']}")

    def test_02_search_rolle_theorem(self):
        """Проверка семантического поиска теоремы Ролля."""
        query = "теорема ролля о нуле производной f(a) = f(b)"
        results = self.store.search(query, top_k=2)
        self.assertTrue(len(results) > 0)
        top = results[0]
        self.assertIn("Ролл", top["theorem"])
        self.assertGreater(top["score"], 0.2)
        print(f"[Test 2 OK] Ролль найден с оценкой {top['score']}: '{top['theorem']}'")

    def test_03_search_taylor_formula(self):
        """Проверка семантического поиска формулы Тейлора с остаточным членом."""
        query = "многочлен тейлора остаточный член пеано лагранж"
        results = self.store.search(query, top_k=2)
        self.assertTrue(len(results) > 0)
        top = results[0]
        self.assertIn("Тейлор", top["theorem"])
        print(f"[Test 3 OK] Тейлор найден с оценкой {top['score']}: '{top['theorem']}'")

    def test_04_search_remarkable_limit(self):
        """Проверка поиска первого замечательного предела."""
        query = "предел отношения sin(x) / x при x стремящемся к 0"
        results = self.store.search(query, top_k=2)
        self.assertTrue(len(results) > 0)
        top = results[0]
        self.assertIn("Первый замечательный предел", top["theorem"])
        print(f"[Test 4 OK] Предел найден с оценкой {top['score']}: '{top['theorem']}'")

    def test_05_dynamic_addition(self):
        """Проверка динамического добавления пользовательской теоремы в реальном времени."""
        new_thm = {
            "id": "darboux_theorem",
            "theorem": "Теорема Дарбу о промежуточных значениях производной",
            "source": "В.А. Зорич, «Математический анализ», Ч. 1, Гл. 5",
            "content": "Если функция дифференцируема на [a, b], то ее производная принимает все промежуточные значения между f'(a) и f'(b).",
            "citation": "«Производная обладает свойством Дарбу даже при отсутствии непрерывности» (Зорич).",
            "latex_formula": r"\forall \gamma \in (f'(a), f'(b)) \ \exists c \in (a, b) : f'(c) = \gamma",
            "tags": ["дарбу", "производная", "промежуточные значения", "дифференцируемость"]
        }
        success = self.store.add_theorem(new_thm)
        self.assertTrue(success)

        # Проверяем, что теперь Дарбу моментально находится поиском
        results = self.store.search("теорема дарбу промежуточные значения производной", top_k=1)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["id"], "darboux_theorem")
        print(f"[Test 5 OK] Теорема Дарбу успешно добавлена в Qdrant и найдена с оценкой {results[0]['score']}")

    def test_06_retriever_pipeline(self):
        """Проверка работы верхнеуровневого ретривера retrieve_math_knowledge."""
        context, chunks = retrieve_math_knowledge("интеграл формула ньютона лейбница первообразная")
        self.assertTrue(len(chunks) > 0)
        self.assertIn("Ньютон", context)
        self.assertIn("Векторная БД Qdrant", chunks[0]["origin"])
        print(f"[Test 6 OK] Ретривер успешно сформировал {len(chunks)} источников для LLM")


if __name__ == "__main__":
    unittest.main()
