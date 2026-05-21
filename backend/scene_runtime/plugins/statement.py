from scene_runtime.analysis import analyze_scene
from scene_runtime.contracts import SceneRequest
from scene_runtime.plugins.base import BaseScenePlugin


class StatementScenePlugin(BaseScenePlugin):
    scene = "statement"

    def build_payload(self, req: SceneRequest):
        return analyze_scene(req, self.scene)
