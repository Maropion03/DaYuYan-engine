from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SupplementInput:
    mode: str
    form: Optional[Dict[str, str]] = None
    file: Optional[Dict[str, Any]] = None


@dataclass
class SceneRequest:
    request_id: str
    scene: str
    main_file: Dict[str, Any]
    supplement: SupplementInput
    runtime: Dict[str, Any]
    output_options: Dict[str, Any]


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def normalize_scene_request(payload: Dict[str, Any]) -> SceneRequest:
    payload_dict = payload if isinstance(payload, dict) else {}
    supplement = _as_dict(payload_dict.get("supplement"))
    form = supplement.get("form")
    file_input = supplement.get("file")
    return SceneRequest(
        request_id=str(payload_dict.get("request_id") or ""),
        scene=str(payload_dict.get("scene") or ""),
        main_file=_as_dict(payload_dict.get("main_file")),
        supplement=SupplementInput(
            mode=str(supplement.get("mode") or "none"),
            form=_as_dict(form) or None,
            file=_as_dict(file_input) or None,
        ),
        runtime=_as_dict(payload_dict.get("runtime")),
        output_options=_as_dict(payload_dict.get("output_options")),
    )


def build_error_result(
    request_id: str,
    scene: str,
    message: str,
    missing_inputs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "scene": scene,
        "status": "failed",
        "confidence": "low",
        "degraded": True,
        "decision": "error",
        "summary": message,
        "facts": {},
        "judgement": {},
        "evidence": [],
        "cards": [],
        "warnings": [message],
        "missing_inputs": missing_inputs or [],
    }
