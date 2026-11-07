"""
Skeptic / Red-Team Agent (Степан Иванов: Critique & Counterexamples).
Реализует глубокий критический аудит математических доказательств:
1. Поиск скрытых логических скачков (Logical Gaps) и неоговоренных предпосылок.
2. Проверка граничных условий (замкнутость отрезков, непрерывность vs дифференцируемость).
3. Построение патологических контрпримеров при ослаблении условий теоремы.
4. Оценка критичности уязвимостей для передачи Судье и Prover Subgraph.
"""
import json
import re
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from core.state import State
from core.llm import get_gigachat_llm

SKEPTIC_SYSTEM_PROMPT = """Ты — Ведущий Математический Скептик и Red-Team Аудитор (Skeptic Agent) в мультиагентной системе Agentic Truth.
Твоя цель — найти скрытые уязвимости в доказательстве Prover, выявить пропущенные условия и предложить строгий математический контрпример при малейшем ослаблении предпосылок.

ЧТО ТЫ ИЩЕШЬ:
1. Граничные условия: Не забыл ли Prover потребовать замкнутость отрезка [a, b] вместо интервала (a, b)?
2. Гладкость: Не опущены ли требования дифференцируемости или непрерывности?
3. Деление на ноль: Не делил ли Prover на выражение, которое может обращаться в ноль (например, g(b) - g(a) или g'(c))?
4. Логические скачки: Не применен ли предельный переход без обоснования равномерной сходимости?
5. Контрпример: Приведи классическую патологическую функцию (функция Дирихле, sgn(x), f(x)=|x|, f(x)=x^2*sin(1/x), функция Вейерштрасса), которая опровергает утверждение, если убрать одно из условий!

ВЕРНИ СТРОГО ВАЛИДНЫЙ JSON БЕЗ ЛИШНЕГО ТЕКСТА:
{{
  "gaps": [
    "Проверить дифференцируемость строго на открытом интервале (a, b)",
    "Убедиться в отсутствии деления на ноль"
  ],
  "counterexample": {{
    "name": "Функция модуля f(x) = |x| на [-1, 1]",
    "violated_condition": "Отсутствие дифференцируемости в точке x = 0",
    "formula": "f(x) = |x|, \\ x \\in [-1, 1]",
    "explanation": "Непрерывна на отрезке, f(-1) = f(1) = 1, но производная в нуле не существует, и f'(c)=0 нигде не выполняется."
  }},
  "severity": "LOW",
  "summary": "Доказательство в целом состоятельно, но требует явного указания дифференцируемости на интервале."
}}

ШКАЛА КРИТИЧНОСТИ (severity):
- "LOW": Мелкие стилистические замечания или стандартные краевые оговорки.
- "MEDIUM": Неполнота условий применимости, требующая явной фиксации.
- "HIGH": Фатальный логический скачок или контрпример разрушает доказательство."""

SKEPTIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SKEPTIC_SYSTEM_PROMPT),
    ("user", """Проведи аудит доказательства:

ТЕОРЕМА:
{query}

ЗАФИКСИРОВАННЫЕ ПРЕДПОСЫЛКИ:
{assumptions}

ДОКАЗАТЕЛЬСТВО PROVER:
{pro_evidence}

СИМВОЛЬНЫЙ АУДИТ SYMPY:
{sympy_result}

Верни результат строго в формате JSON.""")
])


# --- Академический каталог математических контрпримеров и патологий (Fallback) ---
MATH_PATHOLOGY_CATALOG = [
    {
        "keywords": ["ролл", "нуле производной", "rolle"],
        "gaps": [
            "Проверить дифференцируемость строго на открытом интервале (a, b), а не на замкнутом отрезке [a, b].",
            "Убедиться, что случай константной функции (f(x) = const, M = m) разобран отдельно от случая строгого экстремума внутри отрезка."
        ],
        "counterexample_name": "Функция модуля $f(x) = |x|$ на отрезке $[-1, 1]$",
        "violated_condition": "Устранение дифференцируемости в точке $x = 0$",
        "formula": r"f(x) = |x|, \quad x \in [-1, 1]",
        "explanation": "Функция непрерывна на $[-1, 1]$, значения на концах равны $f(-1) = f(1) = 1$. Однако производная $f'(x) = \operatorname{sgn}(x)$ в нуле не существует, и ни в одной точке производная не обращается в ноль.",
        "severity": "MEDIUM"
    },
    {
        "keywords": ["лагранж", "конечном приращении", "lagrange"],
        "gaps": [
            "Проверить корректность построения секущей и вычитания линейной добавки.",
            "Убедиться, что отрезок имеет ненулевую длину ($a < b$), исключая деление на ноль при вычислении наклона."
        ],
        "counterexample_name": "Ступенчатая функция с разрывом $f(x) = \operatorname{sgn}(x)$",
        "violated_condition": "Нарушение непрерывности на отрезке $[-1, 2]$",
        "formula": r"f(x) = \operatorname{sgn}(x), \quad x \in [-1, 2]",
        "explanation": "Приращение $\frac{f(2) - f(-1)}{2 - (-1)} = \frac{1 - (-1)}{3} = \frac{2}{3} \neq 0$. Однако производная всюду вне нуля равна 0, поэтому точки с касательной, параллельной секущей, не существует.",
        "severity": "HIGH"
    },
    {
        "keywords": ["больцано", "коши об обращении", "ноль функции", "промежуточн"],
        "gaps": [
            "Убедиться, что отрезок является замкнутым (на полуинтервале теорема может не выполняться).",
            "Проверить строгость знаков $f(a) \cdot f(b) < 0$ (случай обращения в ноль на границе должен быть оговорен)."
        ],
        "counterexample_name": "Разрывная гиперболическая функция на открытом интервале",
        "violated_condition": "Нарушение непрерывности функции в нуле",
        "formula": r"f(x) = \begin{cases} -1, & x < 0 \\ 1, & x \ge 0 \end{cases} \quad \text{на } [-1, 1]",
        "explanation": "На концах функция имеет разные знаки ($f(-1) = -1, f(1) = 1$), но в ноль нигде не обращается из-за разрыва первого рода в точке $x = 0$.",
        "severity": "HIGH"
    },
    {
        "keywords": ["вейерштрасс", "максимум", "минимум", "ограниченност", "супремум"],
        "gaps": [
            "Строго оговорить компактность области определения (замкнутость и ограниченность отрезка).",
            "Обосновать переход от ограниченности множества значений к достижению точных граней."
        ],
        "counterexample_name": "Гипербола на полуинтервале $(0, 1]$",
        "violated_condition": "Отказ от замкнутости отрезка (открытая граница)",
        "formula": r"f(x) = \frac{1}{x}, \quad x \in (0, 1]",
        "explanation": "Функция непрерывна в каждой точке $(0, 1]$, однако неограниченна сверху и не достигает максимума, так как точка 0 не принадлежит области.",
        "severity": "HIGH"
    },
    {
        "keywords": ["предел", "замечательный", "sin", "синус"],
        "gaps": [
            "Убедиться, что угол $x$ измеряется строго в радианах (при градусной мере предел равен $\pi / 180$).",
            "Обосновать справедливость геометрического неравенства $\cos x < \frac{\sin x}{x} < 1$ для отрицательных $x$ через четность."
        ],
        "counterexample_name": "Аргумент в градусной мере",
        "violated_condition": "Использование неканонической градусной системы измерения углов",
        "formula": r"\lim_{x \to 0} \frac{\sin(x^\circ)}{x} = \frac{\pi}{180} \approx 0.01745 \neq 1",
        "explanation": "Предел отношения синуса к аргументу зависит от единиц измерения дуги. Формула $\lim \frac{\sin x}{x} = 1$ справедлива исключительно для радианов.",
        "severity": "MEDIUM"
    },
    {
        "keywords": ["шварц", "смешанн", "производн", "фнп"],
        "gaps": [
            "Проверить непрерывность смешанных производных $f''_{xy}$ и $f''_{yx}$ в самой исследуемой точке.",
            "Не делать вывод о равенстве смешанных производных только из их существования."
        ],
        "counterexample_name": "Патологическая функция Пеано — Шварца",
        "violated_condition": "Разрывность вторых смешанных производных в начале координат",
        "formula": r"f(x, y) = \frac{xy(x^2 - y^2)}{x^2 + y^2} \quad ((x,y) \neq (0,0)), \quad f(0,0)=0",
        "explanation": "Обе смешанные производные в нуле существуют, но не равны: $f''_{xy}(0, 0) = -1$, а $f''_{yx}(0, 0) = 1$. Причина — разрыв производных в точке $(0, 0)$.",
        "severity": "HIGH"
    },
    {
        "keywords": ["ряд", "сходимост", "лейбниц", "даламбер", "коши"],
        "gaps": [
            "Проверить знакопостоянство членов ряда при использовании признаков сравнения, Даламбера и Коши.",
            "Для признака Лейбница убедиться не только в $\lim a_n = 0$, но и в строгой монотонности убывания $|a_n| \ge |a_{n+1}|$."
        ],
        "counterexample_name": "Гармонический ряд и немонотонный знакочередующийся ряд",
        "violated_condition": "Убывание членов к нулю без выполнения монотонности",
        "formula": r"\sum_{n=1}^\infty \frac{1}{n} = \infty, \quad a_n = \frac{1}{n} \to 0",
        "explanation": "Стремление общего члена ряда к нулю является необходимым, но категорически недостаточным условием сходимости.",
        "severity": "HIGH"
    }
]


def _parse_skeptic_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Парсит структурированный JSON из ответа модели."""
    clean_text = raw_text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
    if match:
        clean_text = match.group(1)
    else:
        start = clean_text.find("{")
        end = clean_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean_text = clean_text[start:end+1]

    try:
        data = json.loads(clean_text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None


def _get_catalog_counterexample(query: str) -> Dict[str, Any]:
    """Подбирает точный академический контрпример из каталога патологий."""
    query_lower = query.lower()
    for item in MATH_PATHOLOGY_CATALOG:
        if any(kw in query_lower for kw in item["keywords"]):
            return item

    # Дефолтный контрпример (по общей непрерывности и разрывам)
    return {
        "gaps": [
            "Проверить строгость поведения функции на границах множества определения.",
            "Убедиться в отсутствии точек разрыва первого и второго рода в области доказательства."
        ],
        "counterexample_name": "Разрывная знакопеременная функция $f(x) = \operatorname{sgn}(x)$",
        "violated_condition": "Нарушение условий гладкости или непрерывности",
        "formula": r"f(x) = \operatorname{sgn}(x), \quad x \in [-1, 1]",
        "explanation": "При ослаблении условий регулярности функции классические теоремы анализа перестают выполняться из-за скачков значений.",
        "severity": "MEDIUM"
    }


def skeptic_node(state: State) -> Dict[str, Any]:
    """
    Узел Скептика (Member 3 — Степан Иванов):
    Проводит Red-Team тестирование доказательства Prover и формирует контрпримеры.
    """
    iteration = state.get("iteration", 1)
    print(f"\n🕵️ [Skeptic Agent (Степан Иванов)] Аудит доказательства на уязвимости и контрпримеры (Итерация #{iteration})...")

    query = state.get("query", "")
    pro_evidence = state.get("pro_evidence", "")
    sympy_result = state.get("sympy_result", "")
    assumptions = state.get("assumptions", [])

    gaps: List[str] = []
    counterexample_str = ""
    severity = "LOW"
    summary = ""

    # 1. Попытка вызвать LLM (GigaChat) с защитой по таймауту
    llm = get_gigachat_llm(temperature=0.2)
    parsed: Optional[Dict[str, Any]] = None

    try:
        chain = SKEPTIC_PROMPT | llm
        response = chain.invoke({
            "query": query,
            "assumptions": "\n".join([f"- {a}" for a in assumptions]),
            "pro_evidence": pro_evidence,
            "sympy_result": sympy_result
        })
        content = response.content if hasattr(response, "content") else str(response)
        parsed = _parse_skeptic_json(content)
    except Exception as e:
        print(f"ℹ️ Вызов LLM в Skeptic пропущен ({e}). Задействован аналитический реестр контрпримеров.")

    # 2. Обработка результатов LLM или fallback на каталог патологий
    if parsed and parsed.get("gaps"):
        gaps = parsed.get("gaps", [])
        ce_obj = parsed.get("counterexample", {})
        if isinstance(ce_obj, dict):
            ce_name = ce_obj.get("name", "Математический контрпример")
            ce_formula = ce_obj.get("formula", "")
            ce_exp = ce_obj.get("explanation", "")
            ce_viol = ce_obj.get("violated_condition", "")
            counterexample_str = (
                f"**Контрпример**: {ce_name}\n"
                f"- **Формула**: ${ce_formula}$\n"
                f"- **Нарушенное условие**: {ce_viol}\n"
                f"- **Обоснование**: {ce_exp}"
            )
        else:
            counterexample_str = str(ce_obj)
        severity = parsed.get("severity", "MEDIUM")
        summary = parsed.get("summary", "Обнаружены потенциальные краевые оговорки.")
    else:
        # Надежный академический каталог
        matched = _get_catalog_counterexample(query)
        gaps = matched["gaps"]
        counterexample_str = (
            f"**Контрпример**: {matched['counterexample_name']}\n"
            f"- **Формула**: $${matched['formula']}$$\n"
            f"- **Нарушенное условие**: {matched['violated_condition']}\n"
            f"- **Обоснование**: {matched['explanation']}"
        )
        severity = matched["severity"]
        summary = f"Выявлены критические предпосылки: {matched['violated_condition']}."

    print(f"⚠️ [Skeptic Agent] Найдено замечаний: {len(gaps)} шт. | Критичность: {severity}")

    # 3. Формирование структурированного отчета контрдоказательств (con_evidence)
    con_report = (
        f"### 🕵️ Экспертный аудит Скептика (Степан Иванов):\n"
        f"**Критичность замечаний**: `{severity}`\n\n"
        f"**1. Потенциальные логические бреши (Logical Gaps):**\n"
        + "\n".join([f"- {g}" for g in gaps])
        + f"\n\n**2. Патологический контрпример при ослаблении условий:**\n"
        + f"{counterexample_str}\n\n"
        f"**3. Резюме для Судьи:**\n"
        f"> {summary}"
    )

    return {
        "logical_gaps": gaps,
        "counterexample": counterexample_str,
        "con_evidence": con_report
    }
