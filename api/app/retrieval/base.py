"""The retriever interface. The rest of the API only ever sees this."""

from __future__ import annotations

from typing import Protocol

from ..schemas import Passage


class Retriever(Protocol):
    name: str

    def metadata(self) -> dict[str, object]:
        """Return index metadata when available, or an empty mapping for a stub."""
        ...

    def retrieve(self, question: str, k: int) -> list[Passage]:
        """Return up to k passages, best first."""
        ...
