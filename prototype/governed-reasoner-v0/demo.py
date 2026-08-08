from core import DeterministicRenderer, GovernedReasoner, Implication, Proposition


def run_demo() -> None:
    reasoner = GovernedReasoner(governing_referent="Jesus Christ the Logos")

    truth_is_binding = Proposition("truth", "binding", True, "governing prior")
    logic_answers_to_truth = Proposition("logic", "answerable to truth", True, "governing prior")
    reasoning_answers_to_logic = Proposition("reasoning", "answerable to logic", True, "governing prior")
    governed_reasoning = Proposition("reasoning", "governed", True, "derived")

    reasoner.assert_proposition(truth_is_binding)
    reasoner.assert_proposition(logic_answers_to_truth)
    reasoner.assert_proposition(reasoning_answers_to_logic)

    reasoner.add_rule(
        Implication(
            antecedent=reasoning_answers_to_logic,
            consequent=governed_reasoning,
            source="v0 governance rule",
        )
    )

    result = reasoner.run()
    print(DeterministicRenderer.render(result))
    print("\nCommitment ledger:")
    for entry in result.ledger:
        print(f"[{entry.kind}] {entry.statement} <- {entry.basis}")


if __name__ == "__main__":
    run_demo()
