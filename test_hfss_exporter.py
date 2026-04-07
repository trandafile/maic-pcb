import unittest

from core.hfss_exporter import generate_hfss_script


class TestHfssExporter(unittest.TestCase):
    def test_uses_active_aedt_project_instead_of_hardcoded_project1(self):
        stackup_data = {
            "layers": [
                {"id": "L2", "name": "Top", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
                {"id": "D1", "name": "Core", "type": "core", "thickness": 1.0, "material_ref": "FR4"},
                {"id": "L1", "name": "Bottom", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
            ],
            "vias": [],
        }

        script = generate_hfss_script(stackup_data)

        self.assertIn('oProject = oDesktop.GetActiveProject()', script)
        self.assertIn('oDesign = oProject.GetActiveDesign()', script)
        self.assertNotIn('SetActiveProject("Project1")', script)

    def test_uses_recorder_style_separator_and_dimension_names(self):
        stackup_data = {
            "layers": [
                {"id": "L2", "name": "Top", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
                {"id": "D1", "name": "Core", "type": "core", "thickness": 1.0, "material_ref": "FR4"},
                {"id": "L1", "name": "Bottom", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
            ],
            "vias": [],
        }

        script = generate_hfss_script(stackup_data)

        self.assertIn('"NAME:PCB_stack_up"', script)
        self.assertIn('"NAME:dielX"', script)
        self.assertIn('"NAME:dielY"', script)
        self.assertNotIn('"NAME:PCB_variables"', script)
        self.assertNotIn('"NAME:DielX"', script)
        self.assertNotIn('"NAME:DielY"', script)

    def test_matches_hfss_recorder_style_blocks(self):
        stackup_data = {
            "layers": [
                {"id": "L2", "name": "Top", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
                {"id": "D1", "name": "Core", "type": "core", "thickness": 1.0, "material_ref": "FR4"},
                {"id": "L1", "name": "Bottom", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
            ],
            "vias": [],
        }

        script = generate_hfss_script(stackup_data)

        self.assertIn('oDesign.ChangeProperty(', script)
        self.assertIn('oEditor.CreateBox(', script)
        self.assertNotIn('def add_local_variable', script)
        self.assertNotIn('def create_dielectric_box', script)

    def test_defines_dielectric_variables_before_dependent_metal_variables(self):
        stackup_data = {
            "layers": [
                {"id": "L2", "name": "Top", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
                {"id": "D1", "name": "Core", "type": "core", "thickness": 0.2, "material_ref": "FR4"},
                {"id": "L1", "name": "Bottom", "type": "metal", "thickness": 0.035, "material_ref": "Generic Copper"},
            ],
            "vias": [],
        }

        script = generate_hfss_script(stackup_data)

        self.assertLess(script.index('"NAME:D1_low"'), script.index('"NAME:L1_high"'))
        self.assertLess(script.index('"NAME:D1_high"'), script.index('"NAME:L2_low"'))

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

        self.assertIn('"NAME:D1_low"', script)
        self.assertIn('"NAME:D1_h"', script)
        self.assertIn('"NAME:D1_high"', script)
        self.assertIn('oEditor.CreateBox(', script)
        self.assertIn('"Name:="             , "D1_box"', script)
        self.assertIn('"NAME:L1_high"', script)
        self.assertIn('"Value:="           , "D1_low"', script)
        self.assertIn('"NAME:L2_low"', script)
        self.assertIn('"Value:="           , "D1_high"', script)

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

        self.assertIn('"NAME:D2_low"', script)
        self.assertIn('"NAME:L2_high"', script)
        self.assertIn('"Value:="           , "D2_low"', script)
        self.assertIn('"NAME:L2_low"', script)
        self.assertIn('"Value:="           , "L2_high-L2_h"', script)


if __name__ == "__main__":
    unittest.main()
