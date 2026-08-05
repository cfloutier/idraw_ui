from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MachineModelDefinition:
    key: str
    label: str
    runtime_model: int
    width_mm: int
    height_mm: int


_MODEL_DEFINITIONS = (
    MachineModelDefinition(
        key="idraw-a4",
        label="iDraw A4",
        runtime_model=1,
        width_mm=300,
        height_mm=210,
    ),
    MachineModelDefinition(
        key="idraw-a3",
        label="iDraw A3",
        runtime_model=2,
        width_mm=430,
        height_mm=297,
    ),
    MachineModelDefinition(
        key="idraw-a2",
        label="iDraw A2",
        runtime_model=6,
        width_mm=594,
        height_mm=432,
    ),
    MachineModelDefinition(
        key="idraw-a1",
        label="iDraw A1",
        runtime_model=5,
        width_mm=864,
        height_mm=594,
    ),
    MachineModelDefinition(
        key="idraw-a0",
        label="iDraw A0",
        runtime_model=8,
        width_mm=1189,
        height_mm=841,
    ),
)

MACHINE_MODELS = {model.key: model for model in _MODEL_DEFINITIONS}

_MODEL_ALIASES = {
    "idraw-1.0": "idraw-a1",
    "idraw-2.0": "idraw-a2",
    "idraw a0": "idraw-a0",
    "idraw a1": "idraw-a1",
    "idraw a2": "idraw-a2",
    "idraw a3": "idraw-a3",
    "idraw a4": "idraw-a4",
}


def list_machine_models() -> list[MachineModelDefinition]:
    return list(_MODEL_DEFINITIONS)


def get_machine_model(model_name: str) -> MachineModelDefinition:
    normalized = model_name.strip().lower()
    normalized = _MODEL_ALIASES.get(normalized, normalized)
    return MACHINE_MODELS.get(normalized, MACHINE_MODELS["idraw-a2"])
