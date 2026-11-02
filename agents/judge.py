from core.state import State


def judge_node(state: State):
    """[Member 4 — Judge / Verifier Agent]"""
    print("\n⚖️ [Judge Agent] Оцениваю доказательство Prover и аудит Skeptic...")

    verdict = "ACCEPT"
    confidence = 0.95

    final_answer = (
        f"## 🎓 Итоговый вердикт системы: {verdict} (Уверенность: {int(confidence * 100)}%)\n\n"
        f"{state.get('pro_evidence', '')}\n\n"
        f"---\n### 🕵️ Замечания Агента-Скептика (Краевые случаи):\n"
        f"{state.get('con_evidence', '')}"
    )

    return {
        "verdict": verdict,
        "confidence_score": confidence,
        "final_answer": final_answer if verdict == "ACCEPT" else ""
    }


def judge_router(state: State) -> str:
    verdict = state.get("verdict", "ACCEPT")
    iteration = state.get("iteration", 1)

    if verdict == "ACCEPT" or iteration >= 2:
        print(f"🏁 [Judge Router] Вердикт: {verdict} (Итерация {iteration}) -> Завершение.")
        return "finish"

    print(f"🔄 [Judge Router] Вердикт: REVISE (Итерация {iteration}) -> Возврат на доработку!")
    return "retry"
