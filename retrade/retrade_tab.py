from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetradeTabBoundary:
    """Declarative boundary for the existing retrade tab.

    The live tab is still assembled by ExportMixin so the production workflow is
    not disturbed. New code should depend on this boundary instead of reaching
    into the submission package.
    """

    title: str = "Переторжка"
    purpose: str = "Excel переторжки: скачать, рассчитать, изменить, импортировать"
    uses_submission_state: bool = False
