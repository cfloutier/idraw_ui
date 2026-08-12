from __future__ import annotations

import pathlib
import tempfile
import unittest

from idraw_ui.ui.svg_page_preview import (
    BBoxMm,
    SvgPageSize,
    calculate_page_placement,
    drawing_exceeds_page,
    read_svg_drawing_bbox,
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
            '<svg xmlns="http://www.w3.org/2000/svg" width="105mm" height="148mm" viewBox="0 0 396.85 559.37" />'
        )

        self.assertEqual((size.width, size.height, size.label), (105.0, 148.0, "mm"))

    def test_converts_inches_to_mm(self) -> None:
        size = self._read('<svg xmlns="http://www.w3.org/2000/svg" width="2in" height="1in" />')

        self.assertEqual((size.width, size.height, size.label), (50.8, 25.4, "mm"))

    def test_uses_view_box_ratio_for_missing_physical_dimension(self) -> None:
        size = self._read('<svg xmlns="http://www.w3.org/2000/svg" width="100mm" viewBox="0 0 200 100" />')

        self.assertEqual((size.width, size.height, size.label), (100.0, 50.0, "mm"))

    def test_falls_back_to_view_box_units(self) -> None:
        size = self._read('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200" />')

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


class SvgDrawingBBoxTests(unittest.TestCase):
    def _read_bbox(self, svg: str):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = pathlib.Path(tmp_dir) / "page.svg"
            path.write_text(svg, encoding="utf-8")
            return read_svg_drawing_bbox(path)

    def test_computes_bbox_from_path_lines(self) -> None:
        bbox = self._read_bbox(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" '
            'viewBox="0 0 100 100">'
            '<path d="M 10,20 L 90,20 L 90,80 Z" /></svg>'
        )
        self.assertIsNotNone(bbox)
        self.assertAlmostEqual(bbox.min_x, 10.0)
        self.assertAlmostEqual(bbox.min_y, 20.0)
        self.assertAlmostEqual(bbox.max_x, 90.0)
        self.assertAlmostEqual(bbox.max_y, 80.0)

    def test_applies_nested_transforms(self) -> None:
        bbox = self._read_bbox(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" '
            'viewBox="0 0 100 100">'
            '<g transform="translate(10,10)">'
            '<rect x="0" y="0" width="20" height="5" transform="scale(2)" />'
            "</g></svg>"
        )
        self.assertIsNotNone(bbox)
        self.assertAlmostEqual(bbox.min_x, 10.0)
        self.assertAlmostEqual(bbox.min_y, 10.0)
        self.assertAlmostEqual(bbox.max_x, 50.0)
        self.assertAlmostEqual(bbox.max_y, 20.0)

    def test_converts_view_box_scale_to_mm(self) -> None:
        bbox = self._read_bbox(
            '<svg xmlns="http://www.w3.org/2000/svg" width="50mm" height="50mm" '
            'viewBox="0 0 200 200">'
            '<line x1="0" y1="0" x2="100" y2="100" /></svg>'
        )
        self.assertIsNotNone(bbox)
        self.assertAlmostEqual(bbox.min_x, 0.0)
        self.assertAlmostEqual(bbox.max_x, 25.0)
        self.assertAlmostEqual(bbox.max_y, 25.0)

    def test_ignores_defs_content(self) -> None:
        bbox = self._read_bbox(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" '
            'viewBox="0 0 100 100">'
            '<defs><rect x="0" y="0" width="99" height="99" /></defs>'
            '<circle cx="50" cy="50" r="5" /></svg>'
        )
        self.assertIsNotNone(bbox)
        self.assertAlmostEqual(bbox.min_x, 45.0, delta=0.1)
        self.assertAlmostEqual(bbox.max_x, 55.0, delta=0.1)

    def test_ignores_hidden_content(self) -> None:
        bbox = self._read_bbox(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" '
            'viewBox="0 0 100 100">'
            '<g style="display:none"><rect x="0" y="0" width="99" height="99" /></g>'
            '<g style="visibility:hidden"><rect x="1" y="1" width="98" height="98" /></g>'
            '<circle cx="50" cy="50" r="5" /></svg>'
        )
        self.assertIsNotNone(bbox)
        self.assertAlmostEqual(bbox.min_x, 45.0, delta=0.1)
        self.assertAlmostEqual(bbox.max_x, 55.0, delta=0.1)

    def test_returns_none_without_physical_scale(self) -> None:
        bbox = self._read_bbox(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M 0,0 L 10,10" /></svg>'
        )
        self.assertIsNone(bbox)

    def test_returns_none_when_no_drawable_content(self) -> None:
        bbox = self._read_bbox(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" viewBox="0 0 100 100"></svg>'
        )
        self.assertIsNone(bbox)


class DrawingExceedsPageTests(unittest.TestCase):
    def test_false_when_bbox_within_page(self) -> None:
        page = SvgPageSize(100.0, 100.0, "mm")
        bbox = BBoxMm(10.0, 10.0, 90.0, 90.0)
        self.assertFalse(drawing_exceeds_page(page, bbox))

    def test_true_when_bbox_extends_past_right_edge(self) -> None:
        page = SvgPageSize(100.0, 100.0, "mm")
        bbox = BBoxMm(10.0, 10.0, 110.0, 90.0)
        self.assertTrue(drawing_exceeds_page(page, bbox))

    def test_true_when_bbox_extends_before_origin(self) -> None:
        page = SvgPageSize(100.0, 100.0, "mm")
        bbox = BBoxMm(-5.0, 10.0, 90.0, 90.0)
        self.assertTrue(drawing_exceeds_page(page, bbox))

    def test_false_when_bbox_exactly_matches_page(self) -> None:
        page = SvgPageSize(100.0, 100.0, "mm")
        bbox = BBoxMm(0.0, 0.0, 100.0, 100.0)
        self.assertFalse(drawing_exceeds_page(page, bbox))


if __name__ == "__main__":
    unittest.main()
