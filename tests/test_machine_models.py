from __future__ import annotations

from idraw_ui.backend.machine_models import (
    get_machine_model,
    list_machine_models,
    move_delta_to_center,
    move_delta_to_corner,
    table_relative_jog_vector,
)


def test_list_machine_models_returns_ui_models() -> None:
    models = list_machine_models()

    assert [model.key for model in models] == [
        "idraw-a4",
        "idraw-a3",
        "idraw-a2",
        "idraw-a1",
        "idraw-a0",
        "idraw-lab-reverse",
    ]
    assert models[0].width_mm == 300
    assert models[0].physical_home == "bottom-right"
    assert models[0].long_axis_is_y is True
    assert models[0].x_axis_toward_home is False
    assert models[0].y_axis_toward_home is True
    assert models[-2].height_mm == 841
    assert models[-1].physical_home == "bottom-left"
    assert models[-1].long_axis_is_y is False
    assert models[-1].x_axis_toward_home is True
    assert models[-1].y_axis_toward_home is False


def test_get_machine_model_supports_legacy_aliases() -> None:
    assert get_machine_model("idraw-2.0").runtime_model == 6
    assert get_machine_model("idraw-1.0").runtime_model == 5
    assert get_machine_model("iDraw A3").runtime_model == 2


def test_move_delta_to_corner_applies_padding() -> None:
    model = get_machine_model("idraw-a2")

    padded = move_delta_to_corner(
        model,
        "portrait",
        "top-left",
        padding_mm=10.0,
    )
    exact = move_delta_to_corner(
        model,
        "portrait",
        "top-left",
        padding_mm=0.0,
    )

    assert padded == (422.0, -584.0)
    assert exact == (432.0, -594.0)


def test_move_delta_to_center_uses_machine_geometry() -> None:
    model = get_machine_model("idraw-a2")

    assert move_delta_to_center(model, "portrait") == (216.0, -297.0)
    assert move_delta_to_center(model, "landscape") == (216.0, -297.0)


def test_table_relative_jog_vector_uses_display_orientation() -> None:
    model = get_machine_model("idraw-a2")

    assert table_relative_jog_vector(model, "portrait", "right") == (-1.0, 0.0)
    assert table_relative_jog_vector(model, "portrait", "left") == (1.0, 0.0)
    assert table_relative_jog_vector(model, "portrait", "forward") == (0.0, -1.0)
    assert table_relative_jog_vector(model, "portrait", "backward") == (0.0, 1.0)

    assert table_relative_jog_vector(model, "landscape", "right") == (0.0, -1.0)
    assert table_relative_jog_vector(model, "landscape", "left") == (0.0, 1.0)
    assert table_relative_jog_vector(model, "landscape", "forward") == (1.0, 0.0)
    assert table_relative_jog_vector(model, "landscape", "backward") == (-1.0, 0.0)
