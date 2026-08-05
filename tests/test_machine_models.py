from __future__ import annotations

from idraw_ui.backend.machine_models import get_machine_model, list_machine_models


def test_list_machine_models_returns_ui_models() -> None:
    models = list_machine_models()

    assert [model.key for model in models] == [
        "idraw-a4",
        "idraw-a3",
        "idraw-a2",
        "idraw-a1",
        "idraw-a0",
    ]
    assert models[0].width_mm == 300
    assert models[-1].height_mm == 841


def test_get_machine_model_supports_legacy_aliases() -> None:
    assert get_machine_model("idraw-2.0").runtime_model == 6
    assert get_machine_model("idraw-1.0").runtime_model == 5
    assert get_machine_model("iDraw A3").runtime_model == 2
