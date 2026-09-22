from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Proposition:
    subject: str
    predicate: str
    value: bool = True
    source: str = "given"

    @property
    def key(self) -> Tuple[str, str]:
        return (self.subject.strip().lower(), self.predicate.strip().lower())

    def text(self) -> str:
        neg = "not " if not self.value else ""
        return f"{self.subject} is {neg}{self.predicate}"


@dataclass(frozen=True)
class Implication:
    antecedent: Proposition
    consequent: Proposition
    source: str = "rule"


@dataclass
class LedgerEntry:
    kind: str
    statement: str
    basis: str


@dataclass
class ReasoningResult:
    propositions: List[Proposition]
    ledger: List[LedgerEntry]
    contradictions: List[str]


class GovernedReasoner:
    """A deliberately small, auditable reasoning kernel.

    It does not retrieve facts, imitate expert consensus, or generate prose.
    It accepts normalized propositions and explicit rules, then records what follows.
    """

    def __init__(self, governing_referent: str):
        self.governing_referent = governing_referent
        self._facts: Dict[Tuple[str, str], Proposition] = {}
        self._rules: List[Implication] = []
        self._ledger: List[LedgerEntry] = [
            LedgerEntry("governance", f"governing referent = {governing_referent}", "runtime configuration")
        ]
        self._contradictions: List[str] = []

    def assert_proposition(self, proposition: Proposition) -> None:
        existing = self._facts.get(proposition.key)
        if existing is not None and existing.value != proposition.value:
            message = f"CONTRADICTION: {existing.text()} / {proposition.text()}"
            if message not in self._contradictions:
                self._contradictions.append(message)
                self._ledger.append(LedgerEntry("contradiction", message, proposition.source))
            return
        if existing is None:
            self._facts[proposition.key] = proposition
            self._ledger.append(LedgerEntry("premise", proposition.text(), proposition.source))

    def add_rule(self, implication: Implication) -> None:
        self._rules.append(implication)
        self._ledger.append(
            LedgerEntry(
                "rule",
                f"IF {implication.antecedent.text()} THEN {implication.consequent.text()}",
                implication.source,
            )
        )

    def run(self) -> ReasoningResult:
        changed = True
        while changed:
            changed = False
            for rule in self._rules:
                known = self._facts.get(rule.antecedent.key)
                if known is None or known.value != rule.antecedent.value:
                    continue
                before = len(self._facts)
                self.assert_proposition(
                    Proposition(
                        subject=rule.consequent.subject,
                        predicate=rule.consequent.predicate,
                        value=rule.consequent.value,
                        source=f"inference from {rule.source}",
                    )
                )
                if len(self._facts) > before:
                    self._ledger.append(
                        LedgerEntry(
                            "inference",
                            rule.consequent.text(),
                            f"modus ponens from {rule.antecedent.text()}",
                        )
                    )
                    changed = True
        return ReasoningResult(list(self._facts.values()), list(self._ledger), list(self._contradictions))


class DeterministicRenderer:
    """Presentation layer. It reports adjudicated state; it does not decide it."""

    @staticmethod
    def render(result: ReasoningResult) -> str:
        lines = []
        if result.contradictions:
            lines.append("Reasoning halted: contradiction detected.")
            lines.extend(result.contradictions)
            return "\n".join(lines)
        lines.append("Adjudicated propositions:")
        for proposition in result.propositions:
            lines.append(f"- {proposition.text()}.")
        return "\n".join(lines)
