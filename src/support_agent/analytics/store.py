from __future__ import annotations

import json
from pathlib import Path

from support_agent.analytics.models import AnalyticsRunRecord


class AnalyticsStore:
    """Persists analytics run records as JSON for dashboard consumption."""

    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path or "data/analytics/metrics.json")

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> list[AnalyticsRunRecord]:
        if not self._path.exists():
            return []

        payload = json.loads(self._path.read_text(encoding="utf-8"))
        return [AnalyticsRunRecord.model_validate(item) for item in payload]

    def save(self, records: list[AnalyticsRunRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        serialized = [record.model_dump(mode="json") for record in records]
        self._path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    def append(self, record: AnalyticsRunRecord) -> None:
        records = self.load()
        records.append(record)
        self.save(records)

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()
