from __future__ import annotations

from idraw_ui.backend.machine_models import get_machine_model
from idraw_ui.ui.machine_tab import MachineTab


def test_display_axis_vectors_swap_in_landscape_for_a2() -> None:
    model = get_machine_model("idraw-a2")

    assert MachineTab._display_axis_vectors(model, "portrait") == ((-1, 0), (0, 1))
    assert MachineTab._display_axis_vectors(model, "landscape") == ((0, -1), (-1, 0))


def test_margin_input_accepts_only_non_negative_integers() -> None:
    assert MachineTab._is_valid_margin_input("")
    assert MachineTab._is_valid_margin_input("0")
    assert MachineTab._is_valid_margin_input("125")
    assert not MachineTab._is_valid_margin_input("-1")
    assert not MachineTab._is_valid_margin_input("1.5")
    assert not MachineTab._is_valid_margin_input("abc")
