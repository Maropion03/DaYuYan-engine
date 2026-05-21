from scene_runtime.plugins.contract import ContractScenePlugin
from scene_runtime.plugins.paper import PaperScenePlugin
from scene_runtime.plugins.resume import ResumeScenePlugin
from scene_runtime.plugins.statement import StatementScenePlugin


PLUGIN_REGISTRY = {
    "resume": ResumeScenePlugin(),
    "contract": ContractScenePlugin(),
    "statement": StatementScenePlugin(),
    "paper": PaperScenePlugin(),
}


def get_scene_plugin(scene: str):
    return PLUGIN_REGISTRY.get(scene)
