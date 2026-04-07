# Lessons Learned

*This file tracks continuous self-improvement lessons regarding Plotly Z-axis logic, Streamlit state bugs, and architectural rules to avoid repeating mistakes.*

## Initial Architecture Setup (Date: {{Current Date}})
* **Rule:** Streamlit State Initialization must happen before any component reads variables (`KeyError` prevention).
* **Rule:** Toggles and UI controls update `st.session_state` values synchronously.

## HFSS Script Export - Layer Ordering Logic (Date: 2026-04-07)
* **Issue:** PCB stack-up layers are stored top-down (index 0 = top), but HFSS needs bottom-up processing with Z=0 at the base.
* **Solution:** Always reverse the layers list before processing (`layers_bottom_up = list(reversed(layers))`). 
* **Rule:** When generating HFSS scripts:
  - Dielectrics get Box objects with `_low`, `_h`, `_high` variables
  - Metals get only variables (no boxes)
  - Metal placement depends on adjacent dielectric types:
    * **Case A** (core-metal-core or external): metal sits ON TOP of lower dielectric
    * **Case B** (core-metal-prepreg): metal penetrates INTO prepreg direction
    * **Case C** (prepreg-metal-core): metal penetrates DOWNWARD into prepreg
* **Rule:** Layer IDs must be numbered bottom-up (L1 = bottom, L2 = top) for physical clarity.

## Layer ID Visibility Across All Views (Date: 2026-04-07)
* **Rule:** Every view (2D Plotly, 2D HTML, 3D) must display the layer ID explicitly in labels and tooltips.
* **Format:** `[{layer_id}] {layer_name}` (e.g., `[L1] Bottom Copper`)
* **Implementation:** Updated `plotly_engine_2d.py`, `html_engine_2d.py`, and `plotly_engine_3d.py` hoverinfo.

## Material Library Category Dropdown (Date: 2026-04-07)
* **Rule:** The Category column in `view_library.py` must use `st.column_config.SelectboxColumn` with strict options: `["copper", "core", "prepreg"]`.
* **Benefit:** Prevents user input errors and ensures consistent data for HFSS exporter logic.

## HFSS Export Syntax Safety (Date: 2026-04-07)
* **Issue:** The exported AEDT script broke with a bracket mismatch caused by manually assembling deeply nested `ChangeProperty` lists.
* **Solution:** Generate smaller, reusable helper calls (`add_local_variable`, `add_separator`, `create_dielectric_box`) instead of one giant nested block.
* **Rule:** For HFSS/AEDT exports, prefer compact helper-based Python output and always verify the generated script with `compile(...)` before considering the export complete.

## HFSS Variable Re-run Safety (Date: 2026-04-07)
* **Issue:** Re-running a generated HFSS macro can fail or create conflicts if local variables already exist in the design.
* **Solution:** Use an `add_local_variable(name, value)` helper that checks `oDesign.GetVariables()`, updates existing variables with `oDesign.SetVariableValue(...)`, and creates them only if missing.
* **Rule:** In AEDT export scripts, local variables should be emitted in create-or-update form, and dielectric references must be defined before metal variables that depend on them.
