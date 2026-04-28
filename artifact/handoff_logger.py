from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable


MAX_TEXT_PREVIEW = 280


def _handoff_file() -> Path:
    return Path(__file__).resolve().parent.parent / "AGENTIC_HANDOFF.md"


def _compact_text(value: str, limit: int = MAX_TEXT_PREVIEW) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _format_kv_line(data: Dict[str, str]) -> str:
    return " | ".join([f"{k}: {v}" for k, v in data.items() if v is not None])


def _append(section_title: str, lines: Iterable[str]) -> None:
    path = _handoff_file()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n### {section_title}\n")
        for line in lines:
            f.write(f"- {line}\n")


def log_run_start(configs: Dict[str, str]) -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    _append(
        "Runtime Log",
        [
            _format_kv_line(
                {
                    "timestamp": now,
                    "event": "run_start",
                    "test_name": str(configs.get("test_name", "n/a")),
                    "data_path": str(configs.get("data_path", "n/a")),
                }
            )
        ],
    )


def log_tool_event(configs: Dict[str, str], tool_name: str, iteration: int, result: str) -> None:
    _append(
        "Runtime Log",
        [
            _format_kv_line(
                {
                    "event": "tool_result",
                    "test_name": str(configs.get("test_name", "n/a")),
                    "iteration": str(iteration),
                    "tool": tool_name,
                }
            ),
            f"summary: {_compact_text(result)}",
        ],
    )


def log_run_end(configs: Dict[str, str], final_summary: str) -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    _append(
        "Runtime Log",
        [
            _format_kv_line(
                {
                    "timestamp": now,
                    "event": "run_end",
                    "test_name": str(configs.get("test_name", "n/a")),
                    "status": "completed",
                }
            ),
            f"final_summary: {_compact_text(final_summary)}",
        ],
    )
