import unittest

from core.hfss_exporter import generate_hfss_script


class TestHfssExporter(unittest.TestCase):
    def test_generates_dielectric_boxes_and_external_copper_references(self):
        stackup_data = {
            "layers": [
                {"id": "L2", "name": "L2 - Top Copper", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
                {"id": "D1", "name": "D1 - FR4 Core", "type": "core", "thickness": 1.5, "material_ref": "FR4"},
                {"id": "L1", "name": "L1 - Bottom Copper", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
            ],
            "vias": []
        }

        script = generate_hfss_script(stackup_data)

        self.assertIn('"NAME:D1_low"', script)
        self.assertIn('"Value:=", "0mm"', script)
        self.assertIn('"NAME:D1_h"', script)
        self.assertIn('"NAME:D1_high"', script)
        self.assertIn('CreateBox(', script)
        self.assertIn('Name:=", "D1_box"', script)
        self.assertIn('"NAME:L1_high"', script)
        self.assertIn('"Value:=", "D1_low"', script)
        self.assertIn('"NAME:L2_low"', script)
        self.assertIn('"Value:=", "D1_high"', script)

    def test_handles_core_to_prepreg_metal_penetration(self):
        stackup_data = {
            "layers": [
                {"id": "D2", "name": "D2 - FR4 Core", "type": "core", "thickness": 0.8, "material_ref": "FR4"},
                {"id": "L2", "name": "L2 - Inner Copper", "type": "metal", "thickness": 0.018, "material_ref": "Copper"},
                {"id": "D1", "name": "D1 - Prepreg", "type": "prepreg", "thickness": 0.1, "material_ref": "PP"},
            ],
            "vias": []
        }

        script = generate_hfss_script(stackup_data)

        self.assertIn('"NAME:D1_low"', script)
        self.assertIn('"NAME:D2_low"', script)
        self.assertIn('"Value:=", "D1_high"', script)
        self.assertIn('"NAME:L2_high"', script)
        self.assertIn('"Value:=", "D2_low"', script)
        self.assertIn('"NAME:L2_low"', script)
        self.assertIn('"Value:=", "L2_high-L2_h"', script)


if __name__ == "__main__":
    unittest.main()
