from typing import Dict, List, Union
from kubernetes.client import (
    V1Toleration,
    V1PreferredSchedulingTerm,
    V1NodeSelectorTerm,
    V1LabelSelectorRequirement,
)


def generate_labels(model_name: str, model_size_megabytes: int) -> Dict[str, str]:
    return {
        "app.kubernetes.io/component": "model",
        "app.kubernetes.io/part-of": "eos-models",
        "app.kubernetes.io/instance": f"model-{model_name}",
        "ersilia.modelid": model_name,
        "ersilia.modelsize": f"{model_size_megabytes}Mi",
    }


def generate_image(model_name: str) -> str:
    return f"ersiliaos/{model_name}:latest"


def generate_memory_limit(
    model_size_megabytes: int, disable_memory_limit: bool
) -> Union[str, None]:
    if disable_memory_limit:
        return None

    if model_size_megabytes <= 512:
        return "700Mi"
    elif model_size_megabytes <= 1024:
        return "1200Mi"
    elif model_size_megabytes <= 2048:
        return "2200Mi"
    elif model_size_megabytes <= 3072:
        return "3200Mi"
    elif model_size_megabytes <= 4096:
        return "4300Mi"
    elif model_size_megabytes <= 5120:
        return "5300Mi"
    elif model_size_megabytes <= 6144:
        return "6400Mi"
    elif model_size_megabytes <= 7168:
        return "7400Mi"

    return None


def generate_affinity(model_size_megabytes: int) -> List[V1PreferredSchedulingTerm]:
    affinity: List[V1PreferredSchedulingTerm] = []

    if model_size_megabytes <= 1024:
        affinity.append(
            V1PreferredSchedulingTerm(
                preference=V1NodeSelectorTerm(
                    match_expressions=list[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["2Gi"]
                        )
                    ]
                ),
                weight=100,
            )
        )
        affinity.append(
            V1PreferredSchedulingTerm(
                preference=V1NodeSelectorTerm(
                    match_expressions=list[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["4Gi", "8Gi"]
                        )
                    ]
                ),
                weight=1,
            )
        )

    elif model_size_megabytes <= 3072:
        affinity.append(
            V1PreferredSchedulingTerm(
                preference=V1NodeSelectorTerm(
                    match_expressions=list[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["4Gi"]
                        )
                    ]
                ),
                weight=100,
            )
        )
        affinity.append(
            V1PreferredSchedulingTerm(
                preference=V1NodeSelectorTerm(
                    match_expressions=list[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["8Gi"]
                        )
                    ]
                ),
                weight=1,
            )
        )

    elif model_size_megabytes <= 7168:
        affinity.append(
            V1PreferredSchedulingTerm(
                preference=V1NodeSelectorTerm(
                    match_expressions=list[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["8Gi"]
                        )
                    ]
                ),
                weight=100,
            )
        )

        return affinity


def generate_tolerations(model_size_megabytes: int) -> List[V1Toleration]:
    tolerations: List[V1Toleration] = []

    if model_size_megabytes <= 2048:
        tolerations.append(
            V1Toleration(
                effect="NoSchedule", key="node.sku", operator="Equal", value="2Gi"
            )
        )

    if model_size_megabytes <= 3072:
        tolerations.append(
            V1Toleration(
                effect="NoSchedule", key="node.sku", operator="Equal", value="4Gi"
            )
        )

    if model_size_megabytes <= 7168:
        tolerations.append(
            V1Toleration(
                effect="NoSchedule", key="node.sku", operator="Equal", value="8Gi"
            )
        )

    return tolerations
