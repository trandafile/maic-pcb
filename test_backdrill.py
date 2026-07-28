"""Tests for the back-drill feature (core/via_utils.py + every 2D/3D engine).

Back-drill fields are optional: the first test class pins the guarantee that a
project saved before the feature existed keeps rendering exactly as before.
"""

import copy
import unittest

from core import (
    html_engine_2d,
    plotly_engine_2d,
    plotly_engine_3d,
    svg_engine_2d,
    via_utils,
)
from views import view_editor


def build_layers():
    """L1..L8 copper, D1..D7 core, stored top-down (index 0 = top)."""
    layers = []
    for i in range(1, 9):
        layers.append({
            "id": f"L{i}", "name": f"Layer {i}", "type": "copper",
            "thickness": 0.035, "material_ref": "Generic Copper",
        })
        if i < 8:
            layers.append({
                "id": f"D{i}", "name": f"Diel {i}", "type": "core",
                "thickness": 0.2, "material_ref": "Generic FR4",
            })
    return layers


LAYERS = build_layers()
IDX = {layer["id"]: i for i, layer in enumerate(LAYERS)}

LEGACY_VIA = {
    "id": "V_LEGACY", "name": "Legacy PTH", "type": "PTH",
    "start_layer": "L1", "end_layer": "L8",
    "drill_diameter": 0.3, "pad_diameter": 0.5,
    "antipad_diameter": 0.8, "plating_thickness": 0.025, "fill_type": "empty",
}
BD_BOTTOM = {
    **LEGACY_VIA, "id": "V_BD_BOT", "name": "Stub removed",
    "backdrill_side": "bottom", "backdrill_bottom_layer": "L4",
    "backdrill_diameter": 0.0, "backdrill_stub": 0.1,
}
BD_BOTH = {
    **LEGACY_VIA, "id": "V_BD_BOTH", "name": "Both sides",
    "backdrill_side": "both",
    "backdrill_top_layer": "L3", "backdrill_bottom_layer": "L6",
    "backdrill_diameter": 0.55, "backdrill_stub": 0.05,
}


class TestBackwardCompatibility(unittest.TestCase):
    """A via without any back-drill field must behave exactly as before."""

    def setUp(self):
        self.data = {"layers": LAYERS, "vias": [copy.deepcopy(LEGACY_VIA)]}

    def test_geometry_is_inert(self):
        geom = via_utils.resolve(LEGACY_VIA, IDX)
        self.assertFalse(geom["has_backdrill"])
        self.assertEqual(geom["eff_top_idx"], geom["top_idx"])
        self.assertEqual(geom["eff_bot_idx"], geom["bot_idx"])

    def test_html_has_no_backdrill_markup(self):
        html = html_engine_2d.render_html(self.data, palette="Classic")
        self.assertNotIn('class="via-backdrill"', html)

    def test_svg_has_no_backdrill_markup(self):
        svg = svg_engine_2d.render_svg(self.data, palette="Classic")
        self.assertNotIn("stroke-dasharray", svg)

    def test_plotly_2d_has_no_bore_shape(self):
        fig = plotly_engine_2d.build_2d_figure(self.data)
        dashed = [s for s in fig.layout.shapes if s.line and s.line.dash == "dot"]
        self.assertEqual(dashed, [])

    def test_plotly_3d_draws_one_surface_per_via(self):
        fig = plotly_engine_3d.build_3d_figure(self.data, explosion_factor=0.0)
        surfaces = [t for t in fig.data if t.type == "surface"]
        self.assertEqual(len(surfaces), 1)

    def test_sanitize_injects_inert_defaults(self):
        cleaned, errors, warnings = view_editor._sanitize_vias([dict(LEGACY_VIA)], LAYERS)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(cleaned[0]["backdrill_side"], "none")
        self.assertEqual(cleaned[0]["backdrill_diameter"], 0.0)


class TestGeometryResolution(unittest.TestCase):

    def test_auto_diameter_is_drill_plus_oversize(self):
        geom = via_utils.resolve(LEGACY_VIA, IDX)
        self.assertAlmostEqual(geom["bd_diameter"], 0.3 + via_utils.BACKDRILL_AUTO_OVERSIZE_MM)

    def test_explicit_diameter_wins(self):
        self.assertAlmostEqual(via_utils.resolve(BD_BOTH, IDX)["bd_diameter"], 0.55)

    def test_bottom_side_shortens_the_live_span(self):
        geom = via_utils.resolve(BD_BOTTOM, IDX)
        self.assertTrue(geom["has_backdrill"])
        self.assertIsNone(geom["bd_top_idx"])
        self.assertEqual(geom["bd_bot_idx"], IDX["L4"])
        self.assertEqual(geom["eff_top_idx"], IDX["L1"])
        self.assertEqual(geom["eff_bot_idx"], IDX["L4"])

    def test_layer_classification(self):
        geom = via_utils.resolve(BD_BOTTOM, IDX)
        self.assertEqual(via_utils.classify_layer(IDX["L1"], geom), "connected")
        self.assertEqual(via_utils.classify_layer(IDX["L3"], geom), "unconnected")
        self.assertEqual(via_utils.classify_layer(IDX["L4"], geom), "connected")
        self.assertEqual(via_utils.classify_layer(IDX["L6"], geom), "backdrilled")
        self.assertEqual(via_utils.classify_layer(IDX["L8"], geom), "backdrilled")

    def test_both_sides(self):
        geom = via_utils.resolve(BD_BOTH, IDX)
        self.assertEqual(geom["bd_top_idx"], IDX["L3"])
        self.assertEqual(geom["bd_bot_idx"], IDX["L6"])
        self.assertEqual(via_utils.classify_layer(IDX["L1"], geom), "backdrilled")
        self.assertEqual(via_utils.classify_layer(IDX["L3"], geom), "connected")
        self.assertEqual(via_utils.classify_layer(IDX["L6"], geom), "connected")

    def test_out_of_span_stop_layer_is_ignored(self):
        via = {
            "id": "V", "type": "PTH", "start_layer": "L2", "end_layer": "L5",
            "drill_diameter": 0.3, "backdrill_side": "top", "backdrill_top_layer": "L7",
        }
        self.assertFalse(via_utils.resolve(via, IDX)["has_backdrill"])

    def test_stop_on_the_start_layer_removes_nothing(self):
        via = {**BD_BOTTOM, "backdrill_side": "top", "backdrill_top_layer": "L1"}
        self.assertIsNone(via_utils.resolve(via, IDX)["bd_top_idx"])

    def test_crossing_backdrills_are_dropped(self):
        via = {**BD_BOTH, "backdrill_top_layer": "L6", "backdrill_bottom_layer": "L3"}
        geom = via_utils.resolve(via, IDX)
        self.assertFalse(geom["has_backdrill"])

    def test_missing_layers_return_none(self):
        via = {"id": "V", "start_layer": "NOPE", "end_layer": "L8"}
        self.assertIsNone(via_utils.resolve(via, IDX))

    def test_clearance_on_a_formerly_connected_layer_is_the_bore(self):
        geom = via_utils.resolve(BD_BOTTOM, IDX)
        # L8 was the landing layer: it had a pad, so only the bore is removed.
        self.assertAlmostEqual(
            via_utils.clearance_diameter(BD_BOTTOM, geom, "backdrilled", IDX["L8"]), 0.5
        )
        # L6 was merely crossed: it already had a 0.8 mm antipad.
        self.assertAlmostEqual(
            via_utils.clearance_diameter(BD_BOTTOM, geom, "backdrilled", IDX["L6"]), 0.8
        )

    def test_max_radius_accounts_for_a_wide_bore(self):
        via = {**BD_BOTH, "backdrill_diameter": 1.2}
        self.assertAlmostEqual(via_utils.max_radius(via, via_utils.resolve(via, IDX)), 0.6)


class TestRenderers(unittest.TestCase):

    def setUp(self):
        self.data = {
            "layers": LAYERS,
            "vias": [copy.deepcopy(LEGACY_VIA), copy.deepcopy(BD_BOTTOM), copy.deepcopy(BD_BOTH)],
        }

    def test_plotly_2d_draws_one_bore_per_removed_section(self):
        fig = plotly_engine_2d.build_2d_figure(self.data)
        dashed = [s for s in fig.layout.shapes if s.line and s.line.dash == "dot"]
        self.assertEqual(len(dashed), 3)  # 1 (bottom side) + 2 (both sides)

    def test_plotly_2d_live_barrel_stops_before_the_stop_layer(self):
        data = {"layers": LAYERS, "vias": [copy.deepcopy(BD_BOTTOM)]}
        fig = plotly_engine_2d.build_2d_figure(data)
        z_map = plotly_engine_2d.calculate_z_map(LAYERS)
        walls = [s for s in fig.layout.shapes if s.fillcolor == "#B87333"]
        self.assertEqual(len(walls), 2)
        expected_bottom = z_map["L4"]["y_bottom"] - 0.1
        for wall in walls:
            self.assertAlmostEqual(wall.y1, z_map["L1"]["y_top"])
            self.assertAlmostEqual(wall.y0, expected_bottom)

    def test_plotly_3d_adds_a_surface_per_bore(self):
        fig = plotly_engine_3d.build_3d_figure(self.data, explosion_factor=0.0)
        surfaces = [t for t in fig.data if t.type == "surface"]
        self.assertEqual(len(surfaces), 6)  # 3 barrels + 1 + 2 bores

    def test_plotly_3d_survives_the_explosion_slider(self):
        fig = plotly_engine_3d.build_3d_figure(self.data, explosion_factor=4.0)
        self.assertGreater(len(fig.data), 0)

    def test_html_marks_every_removed_section(self):
        html = html_engine_2d.render_html(self.data, palette="Classic")
        self.assertEqual(html.count('class="via-backdrill"'), 3)

    def test_html_barrel_and_bore_line_up(self):
        data = {"layers": LAYERS, "vias": [copy.deepcopy(BD_BOTTOM)]}
        html = html_engine_2d.render_html(data, palette="Classic")
        import re

        barrel = re.search(r'class="via-zone"[^>]*top:([\d.]+)px; height:([\d.]+)px', html)
        bore = re.search(r'class="via-backdrill"[^>]*top:([\d.]+)px; height:([\d.]+)px', html)
        self.assertIsNotNone(barrel)
        self.assertIsNotNone(bore)
        barrel_bottom = float(barrel.group(1)) + float(barrel.group(2))
        # The bore starts exactly where the live barrel ends: no gap, no overlap.
        self.assertAlmostEqual(barrel_bottom, float(bore.group(1)), places=1)

    def test_svg_is_well_formed_and_annotated(self):
        svg = svg_engine_2d.render_svg(self.data, palette="Classic")
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.rstrip().endswith("</svg>"))
        self.assertIn("stroke-dasharray", svg)
        self.assertIn(">BD ", svg)


class TestEditorValidation(unittest.TestCase):

    def _errors(self, via):
        _, errors, _ = view_editor._sanitize_vias([via], LAYERS)
        return " | ".join(errors)

    def test_valid_backdrill_passes(self):
        cleaned, errors, warnings = view_editor._sanitize_vias([dict(BD_BOTTOM)], LAYERS)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(cleaned[0]["backdrill_bottom_layer"], "L4")

    def test_bore_must_be_wider_than_the_drill(self):
        self.assertIn("must be larger", self._errors({**BD_BOTTOM, "backdrill_diameter": 0.2}))

    def test_missing_stop_layer_is_rejected(self):
        self.assertIn("needs a stop layer", self._errors({**BD_BOTTOM, "backdrill_bottom_layer": ""}))

    def test_unknown_stop_layer_is_rejected(self):
        self.assertIn("does not exist", self._errors({**BD_BOTTOM, "backdrill_bottom_layer": "L99"}))

    def test_stop_layer_outside_the_span_is_rejected(self):
        via = {**BD_BOTTOM, "start_layer": "L1", "end_layer": "L3", "backdrill_bottom_layer": "L6"}
        self.assertIn("must be inside the via span", self._errors(via))

    def test_overlapping_backdrills_are_rejected(self):
        via = {**BD_BOTH, "backdrill_top_layer": "L6", "backdrill_bottom_layer": "L3"}
        self.assertIn("overlap", self._errors(via))

    def test_non_metal_stop_layer_only_warns(self):
        _, errors, warnings = view_editor._sanitize_vias(
            [{**BD_BOTTOM, "backdrill_bottom_layer": "D4"}], LAYERS
        )
        self.assertEqual(errors, [])
        self.assertTrue(any("not a metal layer" in w for w in warnings))

    def test_side_none_skips_backdrill_validation(self):
        via = {**BD_BOTTOM, "backdrill_side": "none", "backdrill_bottom_layer": ""}
        self.assertEqual(self._errors(via), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
