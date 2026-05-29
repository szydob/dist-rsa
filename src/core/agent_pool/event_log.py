from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_EVENT_LOG_PATH = Path(os.environ.get("AGENT_POOL_EVENT_LOG_PATH", "/app/logs/agent_pool_events.jsonl"))


def _event_log_path() -> Path:
	DEFAULT_EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
	return DEFAULT_EVENT_LOG_PATH


def append_event(event_type: str, **payload: Any) -> None:
	entry = {
		"ts": datetime.now(timezone.utc).isoformat(),
		"event_type": event_type,
		**payload,
	}
	line = json.dumps(entry, ensure_ascii=True, separators=(",", ":")) + "\n"
	path = _event_log_path()

	fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
	try:
		os.write(fd, line.encode("utf-8"))
	finally:
		os.close(fd)


def read_events(limit: int = 200) -> list[dict[str, Any]]:
	path = _event_log_path()
	if not path.exists():
		return []

	with path.open("r", encoding="utf-8") as handle:
		lines = handle.readlines()[-limit:]

	events: list[dict[str, Any]] = []
	for line in lines:
		line = line.strip()
		if not line:
			continue
		try:
			events.append(json.loads(line))
		except json.JSONDecodeError:
			continue
	return events