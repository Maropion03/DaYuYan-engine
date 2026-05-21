from typing import Any, Dict

from scene_runtime.contracts import build_error_result, normalize_scene_request
from scene_runtime.plugins import get_scene_plugin


def handle_scene_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    req = normalize_scene_request(payload)
    plugin = get_scene_plugin(req.scene)
    if plugin is None:
        return build_error_result(
            request_id=req.request_id,
            scene=req.scene,
            message="unsupported scene",
        )
    return plugin.run(req)
