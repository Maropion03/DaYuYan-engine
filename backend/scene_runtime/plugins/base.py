from typing import Any, Dict

from scene_runtime.contracts import SceneRequest, build_error_result


class BaseScenePlugin:
    scene = ""

    def run(self, req: SceneRequest) -> Dict[str, Any]:
        if req.scene != self.scene:
            return build_error_result(
                request_id=req.request_id,
                scene=req.scene,
                message="scene/plugin mismatch",
            )
        try:
            payload = self.build_payload(req)
        except KeyError as exc:
            missing_field = str(exc.args[0]) if exc.args else "unknown"
            return build_error_result(
                request_id=req.request_id,
                scene=req.scene,
                message=f"runtime payload missing field: {missing_field}",
            )
        except (TypeError, ValueError) as exc:
            return build_error_result(
                request_id=req.request_id,
                scene=req.scene,
                message=f"runtime payload invalid: {exc}",
            )
        except Exception as exc:
            return build_error_result(
                request_id=req.request_id,
                scene=req.scene,
                message=f"runtime analysis failed: {exc}",
            )
        if not self._is_valid_payload(payload):
            return build_error_result(
                request_id=req.request_id,
                scene=req.scene,
                message="runtime payload unavailable",
            )
        include_evidence = self._option_enabled(req, "include_evidence", True)
        include_card_payload = self._option_enabled(req, "include_card_payload", True)
        return {
            "request_id": req.request_id,
            "scene": req.scene,
            "status": str(payload.get("status") or "ok"),
            "confidence": str(payload.get("confidence") or "low"),
            "degraded": bool(payload.get("degraded", False)),
            "decision": str(payload.get("decision") or "review"),
            "summary": str(payload.get("summary") or ""),
            "facts": self._as_dict(payload.get("facts")),
            "judgement": self._as_dict(payload.get("judgement")),
            "evidence": self._as_list(payload.get("evidence")) if include_evidence else [],
            "cards": self._normalize_cards(payload.get("cards"), include_card_payload),
            "warnings": self._as_list(payload.get("warnings")),
            "missing_inputs": self._as_list(payload.get("missing_inputs")),
        }

    def build_payload(self, req: SceneRequest) -> Dict[str, Any]:
        raise NotImplementedError

    def _as_dict(self, value: Any) -> Dict[str, Any]:
        return dict(value) if isinstance(value, dict) else {}

    def _as_list(self, value: Any) -> list:
        return list(value) if isinstance(value, list) else []

    def _option_enabled(self, req: SceneRequest, name: str, default: bool) -> bool:
        value = req.output_options.get(name)
        return bool(value) if isinstance(value, bool) else default

    def _normalize_cards(self, value: Any, include_card_payload: bool) -> list:
        cards = self._as_list(value)
        normalized = []
        for card in cards:
            card_dict = self._as_dict(card)
            if include_card_payload:
                normalized.append(card_dict)
                continue
            normalized.append(
                {
                    "key": card_dict.get("key"),
                    "title": card_dict.get("title"),
                    "preview": card_dict.get("preview"),
                    "detail_mode": card_dict.get("detail_mode"),
                    "detail_payload": {},
                }
            )
        return normalized

    def _is_valid_payload(self, payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        cards = payload.get("cards")
        return isinstance(cards, list) and len(cards) > 0
