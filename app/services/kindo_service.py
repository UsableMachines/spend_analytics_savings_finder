import os
import json
import time
import logging
import requests

logger = logging.getLogger(__name__)

KINDO_API_URL = "https://api.kindo.ai/v1/agents/runs"
POLL_INTERVAL = 2
DEFAULT_TIMEOUT = int(os.environ.get("APP_AGENT_POLL_TIMEOUT_SEC", "120"))


def get_kindo_config():
    token = os.environ.get("KINDO_API_TOKEN")
    agent_id = os.environ.get("KINDO_AGENT_ID")
    if not token or not agent_id:
        return None, None
    return token, agent_id


def is_configured():
    token, agent_id = get_kindo_config()
    return token is not None and agent_id is not None


def run_analysis(operation, entity_id, records, context=None, options=None, timeout=None):
    token, agent_id = get_kindo_config()
    if not token or not agent_id:
        return {
            "status": "error",
            "summary": "Kindo agent is not configured. Set KINDO_API_TOKEN and KINDO_AGENT_ID environment variables.",
            "findings": [],
            "recommendations": [],
        }

    payload = {
        "operation": operation,
        "entity_id": entity_id,
        "input_data": {
            "description": "Spend analytics data for analysis",
            "records": records if isinstance(records, list) else [records],
            "context": context or {},
        },
        "options": options or {
            "detail_level": "detailed",
            "include_recommendations": True,
            "return_confidence": True,
        },
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    body = {
        "agent_id": agent_id,
        "input": [{"name": "request", "value": json.dumps(payload)}],
    }

    try:
        resp = requests.post(KINDO_API_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        run_data = resp.json()
    except requests.RequestException as exc:
        logger.exception("Kindo API call failed: %s", exc)
        return {
            "status": "error",
            "summary": f"Failed to start analysis: {exc}",
            "findings": [],
            "recommendations": [],
        }

    run_id = run_data.get("id") or run_data.get("run_id")
    if not run_id:
        return {
            "status": "error",
            "summary": "No run ID returned from Kindo API.",
            "findings": [],
            "recommendations": [],
        }

    poll_timeout = timeout or DEFAULT_TIMEOUT
    start = time.time()
    while time.time() - start < poll_timeout:
        try:
            poll = requests.get(
                f"{KINDO_API_URL}/{run_id}",
                headers=headers,
                timeout=15,
            )
            poll.raise_for_status()
            poll_data = poll.json()
        except requests.RequestException as exc:
            logger.warning("Poll error: %s", exc)
            time.sleep(POLL_INTERVAL)
            continue

        status = poll_data.get("status", "").lower()
        if status in ("completed", "succeeded", "success"):
            return _parse_result(poll_data)
        if status in ("failed", "error", "cancelled"):
            return {
                "status": "error",
                "summary": f"Analysis run failed with status: {status}",
                "findings": [],
                "recommendations": [],
            }
        time.sleep(POLL_INTERVAL)

    return {
        "status": "error",
        "summary": f"Analysis timed out after {poll_timeout}s.",
        "findings": [],
        "recommendations": [],
    }


def _parse_result(poll_data):
    output = poll_data.get("output") or poll_data.get("result") or ""
    if isinstance(output, dict):
        return _normalise(output)
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
            if isinstance(parsed, dict):
                return _normalise(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
        return {
            "status": "ok",
            "summary": output[:2000],
            "findings": [],
            "recommendations": [],
        }
    return {
        "status": "error",
        "summary": "Unexpected response format from Kindo agent.",
        "findings": [],
        "recommendations": [],
    }


def _normalise(d):
    return {
        "status": d.get("status", "ok"),
        "summary": d.get("summary", ""),
        "score": d.get("score"),
        "risk_level": d.get("risk_level"),
        "findings": d.get("findings", []),
        "recommendations": d.get("recommendations", []),
        "confidence": d.get("confidence"),
        "metadata": d.get("metadata"),
    }
