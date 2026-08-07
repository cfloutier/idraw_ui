from __future__ import annotations

from idraw_ui.backend.machine_models import get_machine_model
from idraw_ui.ui.machine_tab import MachineTab


def test_display_axis_vectors_swap_in_landscape_for_a2() -> None:
    model = get_machine_model("idraw-a2")

    assert MachineTab._display_axis_vectors(model, "portrait") == ((-1, 0), (0, 1))
    assert MachineTab._display_axis_vectors(model, "landscape") == ((0, -1), (-1, 0))


def test_display_axis_vectors_follow_home_convention_for_lab_reverse() -> None:
    model = get_machine_model("idraw-lab-reverse")

    assert MachineTab._display_axis_vectors(model, "portrait") == ((0, 1), (1, 0))
    assert MachineTab._display_axis_vectors(model, "landscape") == ((-1, 0), (0, 1))
