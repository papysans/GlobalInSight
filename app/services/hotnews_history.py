from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from loguru import logger


@dataclass(frozen=True)
class HotNewsHistoryConfig:
    """File-based history store config.

    We intentionally store history under `outputs/` because it is gitignored.
    """

    history_path: Path
    retention_days: int = 30
    max_lines: int = 2000


class HotNewsHistoryStore:
    """Append-only JSONL history store with periodic compaction."""

    def __init__(self, config: HotNewsHistoryConfig):
        self.config = config
        self.config.history_path.parent.mkdir(parents=True, exist_ok=True)

    def append_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Append a snapshot dict to JSONL file."""
        ts = snapshot.get("ts") or snapshot.get("collection_time")
        if not ts:
            snapshot = {**snapshot, "ts": datetime.now().isoformat()}

        line = json.dumps(snapshot, ensure_ascii=False)
        with self.config.history_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

        self._maybe_compact()

    def load_recent_snapshots(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Load up to `limit` most recent snapshots (best-effort)."""
        path = self.config.history_path
        if not path.exists():
            return []

        # Read all lines then take the tail. For our capped file size this is fine.
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            logger.warning(f"[HotNewsHistory] Failed reading history: {e}")
            return []

        out: List[Dict[str, Any]] = []
        for raw in lines[-limit:]:
            raw = raw.strip()
            if not raw:
                continue
            try:
                out.append(json.loads(raw))
            except Exception:
                continue
        return out

    def _maybe_compact(self) -> None:
        """Compact history by retention + max_lines caps."""
        path = self.config.history_path
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return

        if len(lines) <= self.config.max_lines:
            # Still enforce time retention occasionally
            if len(lines) % 200 != 0:
                return

        cutoff = datetime.now() - timedelta(days=self.config.retention_days)

        kept: List[str] = []
        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                ts = obj.get("ts") or obj.get("collection_time")
                if ts:
                    try:
                        t = datetime.fromisoformat(ts)
                        if t < cutoff:
                            continue
                    except Exception:
                        pass
                kept.append(json.dumps(obj, ensure_ascii=False))
            except Exception:
                continue

        kept = kept[-self.config.max_lines :]

        try:
            path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
        except Exception as e:
            logger.warning(f"[HotNewsHistory] Failed compacting history: {e}")

