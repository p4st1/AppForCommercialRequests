from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.trade_exporter import TradeExporter
from utilities.paths import user_path


def _load_cookies_from_storage_state(storage_state_path: str) -> dict[str, str]:
    state_path = Path(storage_state_path).expanduser().resolve()
    if not state_path.exists():
        raise FileNotFoundError(f"Не найден storage state с авторизацией: {state_path}")

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    cookies_node = payload.get("cookies") if isinstance(payload, dict) else None
    if not isinstance(cookies_node, list):
        raise ValueError("Некорректный storage_state: отсутствует список cookies")

    cookies: dict[str, str] = {}
    for cookie in cookies_node:
        if not isinstance(cookie, dict):
            continue
        name = str(cookie.get("name", "") or "").strip()
        value = str(cookie.get("value", "") or "").strip()
        if not name or not value:
            continue
        cookies[name] = value

    if not cookies:
        raise ValueError("В storage_state не найдено валидных cookies")
    return cookies


def export_all(
    bid_ids: list[int],
    *,
    storage_state_path: str = "storage_state.json",
    exports_dir: str = "exports",
    headless: bool = True,
) -> dict[int, str]:
    # headless сохранен для обратной совместимости сигнатуры.
    _ = headless

    if not bid_ids:
        return {}

    raw_exports_path = Path(exports_dir).expanduser()
    if exports_dir == "exports" and not raw_exports_path.is_absolute():
        exports_path = user_path("exports")
    else:
        exports_path = raw_exports_path.resolve()
    exports_path.mkdir(parents=True, exist_ok=True)

    cookies = _load_cookies_from_storage_state(storage_state_path)
    exporter = TradeExporter(headless=headless)
    exporter._load_cookies_for_export = lambda: dict(cookies)  # type: ignore[method-assign]

    results: dict[int, str] = {}
    for bid_id in bid_ids:
        bid_id_int = int(bid_id)
        target_file = exports_path / f"retrading_{bid_id_int}.xlsx"
        try:
            saved_file = exporter.export_retrade_bid_data(
                bid_id=bid_id_int,
                download_path=str(target_file),
            )
            results[bid_id_int] = saved_file
        except Exception as exc:
            print(f"[ERROR] bid_id={bid_id_int}: {exc}")
            error_payload: dict[str, Any] = {"bid_id": bid_id_int, "error": str(exc)}
            log_path = user_path("logs", "export_debug.log")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(error_payload, ensure_ascii=False) + "\n")

    return results
