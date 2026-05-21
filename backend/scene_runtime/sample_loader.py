from copy import deepcopy
from typing import Any, Dict


_SAMPLES: Dict[str, Dict[str, Any]] = {
    "resume": {
        "facts": {
            "candidate_name": "陈晨",
            "target_role": "AI 产品经理",
            "years_of_experience": "4年",
            "current_focus": "多模态产品策略",
            "core_strengths": [
                "简历筛选流程搭建",
                "数据复盘与指标拆解",
                "跨产品与运营协同",
            ],
        },
    },
    "contract": {
        "facts": {
            "contract_type": "采购合同",
            "counterparty": "星河科技",
            "amount": "CNY 480,000",
            "effective_date": "2026-05-01",
            "delivery_deadline": "2026-06-15",
        },
    },
    "statement": {
        "facts": {
            "account_name": "杭州云山贸易",
            "statement_month": "2026-04",
            "recognized_amount": "128,540.00",
            "ledger_amount": "127,980.00",
            "tax_base": "117,320.00",
        },
    },
    "paper": {
        "facts": {
            "paper_title": "LCM-LoRA: A Universal Stable-Diffusion Acceleration Module",
            "year": "2023",
            "domain": "Generative Model Acceleration / On-device Inference",
            "dataset": "Stable-Diffusion (SD-V1.5 / SSD-1B / SDXL)",
            "primary_metric": "4-step sampling · LoRA trainable params 67.5M–197M · ~32 A100 GPU·hours",
        },
    },
}


def load_scene_sample(scene: str) -> Dict[str, Any]:
    sample = _SAMPLES.get(scene)
    return deepcopy(sample) if isinstance(sample, dict) else {}


def _load_scene_facts(scene: str) -> Dict[str, Any]:
    sample = load_scene_sample(scene)
    facts = sample.get("facts")
    return deepcopy(facts) if isinstance(facts, dict) else {}


def load_resume_sample() -> Dict[str, Any]:
    return _load_scene_facts("resume")


def load_contract_sample() -> Dict[str, Any]:
    return _load_scene_facts("contract")


def load_statement_sample() -> Dict[str, Any]:
    return _load_scene_facts("statement")


def load_paper_sample() -> Dict[str, Any]:
    return _load_scene_facts("paper")
