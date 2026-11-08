"""
Автоматизированный комплекс тестов для векторной базы данных Qdrant и RAG-слоя.
Проверяет:
1. Индексацию расширенного академического корпуса теорем матанализа (40+ теорем).
2. Семантический векторный поиск по 1-му и 2-му курсу (Ролль, Тейлор, Грин, Пикар, ТФКП).
3. Динамическое добавление пользовательских теорем в Qdrant в рантайме.
4. Работу гибридного ретривера retrieve_math_knowledge.
"""
import unittest
from rag.qdrant_store import qdrant_store
from rag.retriever import retrieve_math_knowledge
from rag.corpus import MATH_SEED_CORPUS


class TestQdrantDatabase(unittest.TestCase):

    def setUp(self):
        self.store = qdrant_store

    def test_01_corpus_indexing_count(self):
        """Проверка полноты индексации стартового корпуса (более 40 теорем)."""
        self.assertGreaterEqual(self.store.count(), 40)
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

    def test_05_search_advanced_multivariable_and_complex(self):
        """Проверка поиска теорем 2-го курса (Грин, Пикар, ТФКП, Банах)."""
        # Поиск формулы Грина
        green_res = self.store.search("криволинейный интеграл формула грина двойной интеграл", top_k=1)
        self.assertTrue(len(green_res) > 0)
        self.assertIn("Грин", green_res[0]["theorem"])
        print(f"[Test 5.1 OK] Формула Грина найдена с оценкой {green_res[0]['score']}")

        # Поиск условий Коши-Римана (ТФКП)
        tfkp_res = self.store.search("условия коши римана голоморфность частные производные u и v", top_k=1)
        self.assertTrue(len(tfkp_res) > 0)
        self.assertIn("Коши — Риман", tfkp_res[0]["theorem"])
        print(f"[Test 5.2 OK] Условия Коши-Римана найдены с оценкой {tfkp_res[0]['score']}")

    def test_06_dynamic_addition(self):
        """Проверка динамического добавления новой пользовательской теоремы в реальном времени."""
        from rag.qdrant_store import QdrantMathStore
        isolated_store = QdrantMathStore(persistent_path=":memory:")
        new_thm = {
            "id": "cauchy_schwarz_inequality",
            "category": "Функциональный анализ и неравенства",
            "theorem": "Неравенство Коши — Буняковского — Шварца для интегралов",
            "source": "А.Н. Колмогоров, С.В. Фомин, «Элементы теории функций»",
            "content": "Для любых интегрируемых с квадратом функций f(x) и g(x) квадрат интеграла от их произведения не превосходит произведения интегралов их квадратов.",
            "citation": "«Одно из важнейших неравенств математического анализа» (Колмогоров, Фомин).",
            "latex_formula": r"\left( \int_a^b f(x) g(x) dx \right)^2 \le \left( \int_a^b f^2(x) dx \right) \left( \int_a^b g^2(x) dx \right)",
            "tags": ["неравенство", "коши-буняковский", "шварц", "интеграл"]
        }
        success = isolated_store.add_theorem(new_thm)
        self.assertTrue(success)

        # Проверяем, что теперь Коши-Буняковский моментально находится поиском
        results = isolated_store.search("неравенство коши буняковского для интегралов", top_k=1)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["id"], "cauchy_schwarz_inequality")
        print(f"[Test 6 OK] Неравенство Коши-Буняковского успешно добавлено и найдено с оценкой {results[0]['score']}")

    def test_07_retriever_pipeline(self):
        """Проверка работы верхнеуровневого ретривера retrieve_math_knowledge."""
        context, chunks = retrieve_math_knowledge("интеграл формула ньютона лейбница первообразная")
        self.assertTrue(len(chunks) > 0)
        self.assertIn("Ньютон", context)
        self.assertIn("Векторная БД Qdrant", chunks[0]["origin"])
        print(f"[Test 7 OK] Ретривер успешно сформировал {len(chunks)} источников для LLM")


if __name__ == "__main__":
    unittest.main()
