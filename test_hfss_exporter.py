import unittest

from core.hfss_exporter import generate_hfss_script


class TestHfssExporter(unittest.TestCase):
    def test_generated_script_is_valid_python_and_builds_dielectric_boxes(self):
        stackup_data = {
            "layers": [
                {"id": "L2", "name": "L2 - Top Copper", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
                {"id": "D1", "name": "D1 - FR4 Core", "type": "core", "thickness": 1.5, "material_ref": "FR4"},
                {"id": "L1", "name": "L1 - Bottom Copper", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
            ],
            "vias": [],
        }

        script = generate_hfss_script(stackup_data)
        compile(script, "pcb_stackup_hfss.py", "exec")

        self.assertIn('add_local_variable("D1_low", "0mm")', script)
        self.assertIn('add_local_variable("D1_h", "1.5mm")', script)
        self.assertIn('add_local_variable("D1_high", "D1_low+D1_h")', script)
        self.assertIn('create_dielectric_box("D1_box", "D1_low", "D1_h"', script)
        self.assertIn('add_local_variable("L1_high", "D1_low")', script)
        self.assertIn('add_local_variable("L1_low", "L1_high-L1_h")', script)
        self.assertIn('add_local_variable("L2_low", "D1_high")', script)

    def test_handles_prepreg_core_penetration_rule(self):
        stackup_data = {
            "layers": [
                {"id": "D2", "name": "D2 - FR4 Core", "type": "core", "thickness": 0.8, "material_ref": "FR4"},
                {"id": "L2", "name": "L2 - Inner Copper", "type": "metal", "thickness": 0.018, "material_ref": "Copper"},
                {"id": "D1", "name": "D1 - Prepreg", "type": "prepreg", "thickness": 0.1, "material_ref": "PP"},
            ],
            "vias": [],
        }

        script = generate_hfss_script(stackup_data)
        compile(script, "pcb_stackup_hfss.py", "exec")

        self.assertIn('add_local_variable("D2_low", "D1_high")', script)
        self.assertIn('add_local_variable("L2_high", "D2_low")', script)
        self.assertIn('add_local_variable("L2_low", "L2_high-L2_h")', script)


if __name__ == "__main__":
    unittest.main()
