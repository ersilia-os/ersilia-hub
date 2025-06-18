from typing import Dict, List, Tuple, Union
from kubernetes.client import (
    V1Toleration,
    V1PreferredSchedulingTerm,
    V1NodeSelectorTerm,
    V1LabelSelectorRequirement,
)

# NOTE: needs to be in reserved order
MODEL_SIZE_MEMORY_LIMIT: List[Tuple[int, str]] = [
    (10240, "10600Mi"),
    (9216, "9500Mi"),
    (8192, "8500Mi"),
    (7168, "7500Mi"),
    (6144, "6500Mi"),
    (5120, "5400Mi"),
    (4096, "4400Mi"),
    (3072, "3400Mi"),
    (2048, "2300Mi"),
    (1024, "1300Mi"),
    (512, "800Mi"),
]


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

    best_limit_string = None

    for reference, limit_string in MODEL_SIZE_MEMORY_LIMIT:
        if model_size_megabytes < reference:
            best_limit_string = limit_string
        else:
            break

    print("BEST LIMIT STRING = ", best_limit_string)

    return best_limit_string


def generate_affinity(model_size_megabytes: int) -> List[V1PreferredSchedulingTerm]:
    affinity: List[V1PreferredSchedulingTerm] = []

    if model_size_megabytes <= 1024:
        affinity.append(
            V1PreferredSchedulingTerm(
                preference=V1NodeSelectorTerm(
                    match_expressions=[
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
                    match_expressions=[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["4Gi", "8Gi"]
                        )
                    ]
                ),
                weight=20,
            )
        )
        affinity.append(
            V1PreferredSchedulingTerm(
                preference=V1NodeSelectorTerm(
                    match_expressions=[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["16Gi"]
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
                    match_expressions=[
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
                    match_expressions=[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["8Gi"]
                        )
                    ]
                ),
                weight=20,
            )
        )
        affinity.append(
            V1PreferredSchedulingTerm(
                preference=V1NodeSelectorTerm(
                    match_expressions=[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["16Gi"]
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
                    match_expressions=[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["8Gi"]
                        )
                    ]
                ),
                weight=100,
            )
        )
        affinity.append(
            V1PreferredSchedulingTerm(
                preference=V1NodeSelectorTerm(
                    match_expressions=[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["16Gi"]
                        )
                    ]
                ),
                weight=1,
            )
        )

    elif model_size_megabytes <= 15360:
        affinity.append(
            V1PreferredSchedulingTerm(
                preference=V1NodeSelectorTerm(
                    match_expressions=[
                        V1LabelSelectorRequirement(
                            key="node.sku", operator="In", values=["16Gi"]
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

    if model_size_megabytes <= 15360:
        tolerations.append(
            V1Toleration(
                effect="NoSchedule", key="node.sku", operator="Equal", value="16Gi"
            )
        )

    return tolerations
