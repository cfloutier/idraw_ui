from __future__ import annotations

import pathlib
import tempfile
import unittest

from idraw_ui.ui.svg_page_preview import (
    calculate_page_placement,
    read_svg_page_size,
)


class SvgPageSizeTests(unittest.TestCase):
    def _read(self, svg: str):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = pathlib.Path(tmp_dir) / "page.svg"
            path.write_text(svg, encoding="utf-8")
            return read_svg_page_size(path)

    def test_reads_physical_mm_dimensions(self) -> None:
        size = self._read(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="105mm" height="148mm" viewBox="0 0 396.85 559.37" />'
        )

        self.assertEqual((size.width, size.height, size.label), (105.0, 148.0, "mm"))

    def test_converts_inches_to_mm(self) -> None:
        size = self._read(
            '<svg xmlns="http://www.w3.org/2000/svg" width="2in" height="1in" />'
        )

        self.assertEqual((size.width, size.height, size.label), (50.8, 25.4, "mm"))

    def test_uses_view_box_ratio_for_missing_physical_dimension(self) -> None:
        size = self._read(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="100mm" viewBox="0 0 200 100" />'
        )

        self.assertEqual((size.width, size.height, size.label), (100.0, 50.0, "mm"))

    def test_falls_back_to_view_box_units(self) -> None:
        size = self._read(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200" />'
        )

        self.assertEqual(
            (size.width, size.height, size.label),
            (300.0, 200.0, "SVG units"),
        )

    def test_places_page_inward_from_each_home(self) -> None:
        expected = {
            "top-left": (30.0, 10.0, 130.0, 60.0),
            "top-right": (160.0, 10.0, 260.0, 60.0),
            "bottom-left": (30.0, 130.0, 130.0, 180.0),
            "bottom-right": (160.0, 130.0, 260.0, 180.0),
        }

        for home_corner, coordinates in expected.items():
            with self.subTest(home_corner=home_corner):
                placement = calculate_page_placement(
                    table_width=300.0,
                    table_height=200.0,
                    page_width=100.0,
                    page_height=50.0,
                    home_corner=home_corner,
                    margin_top=10.0,
                    margin_bottom=20.0,
                    margin_left=30.0,
                    margin_right=40.0,
                )

                self.assertEqual(
                    (
                        placement.left,
                        placement.top,
                        placement.right,
                        placement.bottom,
                    ),
                    coordinates,
                )

    def test_detects_page_outside_table(self) -> None:
        placement = calculate_page_placement(
            table_width=300.0,
            table_height=200.0,
            page_width=310.0,
            page_height=100.0,
            home_corner="top-left",
            margin_top=10.0,
            margin_bottom=20.0,
            margin_left=30.0,
            margin_right=40.0,
        )

        self.assertFalse(
            placement.fits_within(
                300.0,
                200.0,
                margin_top=10.0,
                margin_bottom=20.0,
                margin_left=30.0,
                margin_right=40.0,
            )
        )


if __name__ == "__main__":
    unittest.main()
