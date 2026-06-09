from __future__ import annotations

from typing import Any


def normalize_total(raw_total: Any) -> int:
    try:
        normalized_total = int(raw_total)
    except (TypeError, ValueError):
        return 0
    return max(0, normalized_total)


def normalize_trade_json(raw_payload: Any) -> dict[str, Any]:
    if not isinstance(raw_payload, dict):
        return {}
    if isinstance(raw_payload.get("submissionStages"), list):
        return raw_payload

    data_node = raw_payload.get("data")
    if isinstance(data_node, dict):
        if isinstance(data_node.get("submissionStages"), list):
            return data_node
        trade_node = data_node.get("trade")
        if isinstance(trade_node, dict) and isinstance(
            trade_node.get("submissionStages"),
            list,
        ):
            return trade_node

    trade_node = raw_payload.get("trade")
    if isinstance(trade_node, dict) and isinstance(trade_node.get("submissionStages"), list):
        return trade_node

    return raw_payload


def parse_trade_search_response(raw_payload: Any) -> dict[str, Any]:
    if not isinstance(raw_payload, dict):
        return {"items": [], "total": 0}

    data_root = raw_payload.get("data")
    if not isinstance(data_root, dict):
        return {"items": [], "total": 0}

    trades = data_root.get("trades")
    if not isinstance(trades, dict):
        return {"items": [], "total": 0}

    items = trades.get("items")
    if not isinstance(items, list):
        items = []

    return {
        "items": items,
        "total": normalize_total(trades.get("total", 0)),
    }


def parse_retrade_trade(trade: Any) -> dict[str, Any] | None:
    if not isinstance(trade, dict):
        return None

    lots_raw = trade.get("lots")
    lots = lots_raw if isinstance(lots_raw, list) else []
    first_lot = lots[0] if lots and isinstance(lots[0], dict) else {}
    lot_id = first_lot.get("id")
    current_stage = trade.get("currentStage")

    return {
        "id": trade.get("id"),
        "stage_id": current_stage.get("id") if isinstance(current_stage, dict) else None,
        "number": trade.get("registeredNumber"),
        "title": trade.get("title"),
        "status": trade.get("processStatus"),
        "endDate": trade.get("bidSubmissionEndDate") or "",
        "lot_id": lot_id,
        "lots": lots,
        "organizer": trade.get("organizer"),
        "customer": trade.get("customer"),
        "currency": trade.get("currency"),
    }


def parse_retrades(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    parsed: list[dict[str, Any]] = []
    for item in items:
        retrade = parse_retrade_trade(item)
        if retrade is not None:
            parsed.append(retrade)
    return parsed


def parse_retrade_bids(trade_json: dict) -> list[dict]:
    normalized_trade = normalize_trade_json(trade_json)

    stages = normalized_trade.get("submissionStages", [])
    if not isinstance(stages, list):
        stages = []

    bids: list[dict[str, Any]] = []
    seen_bid_ids: set[int] = set()

    for stage in stages:
        if not isinstance(stage, dict):
            continue
        trade_result = stage.get("tradeResult")
        if not isinstance(trade_result, dict):
            continue

        lot_results = trade_result.get("lotResults", [])
        if not isinstance(lot_results, list):
            lot_results = []

        for lot in lot_results:
            if not isinstance(lot, dict):
                continue
            bid_places = lot.get("bidPlaces", [])
            if not isinstance(bid_places, list):
                bid_places = []

            for place in bid_places:
                if not isinstance(place, dict):
                    continue
                bid = place.get("bid")
                if not isinstance(bid, dict):
                    continue

                bid_id_raw = bid.get("id")
                try:
                    bid_id = int(bid_id_raw)
                except (TypeError, ValueError):
                    continue
                if bid_id <= 0 or bid_id in seen_bid_ids:
                    continue

                status_node = bid.get("status")
                status_title = ""
                if isinstance(status_node, dict):
                    status_title = str(status_node.get("title", "") or "")

                bidder_node = bid.get("bidder")
                bidder_title = ""
                if isinstance(bidder_node, dict):
                    bidder_title = str(bidder_node.get("title", "") or "")

                bids.append(
                    {
                        "bid_id": bid_id,
                        "number": str(bid.get("number", "") or ""),
                        "price": bid.get("price"),
                        "status": status_title,
                        "bid_date": bid.get("bidDate"),
                        "bidder_title": bidder_title,
                    }
                )
                seen_bid_ids.add(bid_id)

    return bids
