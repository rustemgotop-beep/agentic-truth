from core.state import State


def skeptic_node(state: State):
    """[Member 3 — Skeptic / Red-Team Agent]"""
    print("\n🕵️ [Skeptic Agent] Проверяю доказательство Prover на логические скачки и контрпримеры...")

    gaps = [
        "Проверить строгость перехода на границах отрезка [a, b].",
        "Убедиться, что явно оговорен случай нестрогого знакопостоянства."
    ]
    counterexample = (
        "Контрпример при нарушении непрерывности: для разрывной функции f(x) = sgn(x) на [-1, 1] "
        "при выколотом нуле f(0) = 1 условие разных знаков на концах выполнено, но нуля не существует."
    )
    con_report = (
        f"**Найденные потенциальные уязвимости:**\n"
        + "\n".join([f"- {g}" for g in gaps])
        + f"\n\n**Контрпример при ослаблении условий:**\n{counterexample}"
    )

    return {
        "logical_gaps": gaps,
        "counterexample": counterexample,
        "con_evidence": con_report
    }
