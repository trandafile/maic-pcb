"""HFSS AEDT Python exporter for the PCB Stack-up visualizer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _safe_str(value: Any) -> str:
    return str(value or "").strip()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _sanitize_identifier(value: Any) -> str:
    raw = _safe_str(value) or "Layer"
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in raw)
    if cleaned and cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    return cleaned or "Layer"


def _format_length(value_mm: Any, prefer_um: bool = False) -> str:
    value = _to_float(value_mm)
    if abs(value) < 1e-12:
        return "0mm"

    if prefer_um or abs(value) < 0.1:
        value_um = value * 1000.0
        if abs(value_um - round(value_um)) < 1e-9:
            return f"{int(round(value_um))}um"
        return f"{value_um:.3f}".rstrip("0").rstrip(".") + "um"

    return f"{value:.4f}".rstrip("0").rstrip(".") + "mm"


def _layer_family(layer: Dict[str, Any]) -> str:
    combined = " ".join(
        [
            _safe_str(layer.get("type")).lower(),
            _safe_str(layer.get("name")).lower(),
            _safe_str(layer.get("material_ref")).lower(),
        ]
    )

    if any(token in combined for token in ["metal", "copper"]):
        return "metal"
    if "prepreg" in combined:
        return "prepreg"
    if "core" in combined:
        return "core"
    if any(token in combined for token in ["dielectric", "cover", "soldermask", "silkscreen"]):
        return "core"
    return "core"


def _infer_hfss_material(layer: Dict[str, Any]) -> str:
    combined = " ".join(
        [
            _safe_str(layer.get("material_ref")).lower(),
            _safe_str(layer.get("name")).lower(),
        ]
    )

    if "vacuum" in combined:
        return "vacuum"
    if "air" in combined:
        return "air"
    if "fr4" in combined or _layer_family(layer) in {"core", "prepreg"}:
        return "FR4_epoxy"
    return "FR4_epoxy"


def _hex_to_rgb_string(hex_color: Any, fallback: str = "#708090") -> str:
    value = _safe_str(hex_color) or fallback
    value = value.lstrip("#")
    if len(value) != 6:
        value = fallback.lstrip("#")

    try:
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
    except ValueError:
        fallback = fallback.lstrip("#")
        r = int(fallback[0:2], 16)
        g = int(fallback[2:4], 16)
        b = int(fallback[4:6], 16)

    return f"({r} {g} {b})"


def _escape_python_string(value: Any) -> str:
    return _safe_str(value).replace("\\", "\\\\").replace('"', '\\"')


def _resolve_metal_position(
    metal_id: str,
    lower_dielectric: Optional[Dict[str, Any]],
    upper_dielectric: Optional[Dict[str, Any]],
) -> tuple[str, str, str, str]:
    if lower_dielectric is None and upper_dielectric is None:
        return (
            "up",
            "0mm",
            f"{metal_id}_low+{metal_id}_h",
            "Fallback placement: no dielectric neighbours were found.",
        )

    if lower_dielectric is None and upper_dielectric is not None:
        return (
            "down",
            f"{metal_id}_high-{metal_id}_h",
            f"{upper_dielectric['id']}_low",
            "External bottom metal: referenced to the lower face of the first dielectric.",
        )

    if lower_dielectric is not None and upper_dielectric is None:
        return (
            "up",
            f"{lower_dielectric['id']}_high",
            f"{metal_id}_low+{metal_id}_h",
            "External top metal: sits on the upper face of the dielectric below.",
        )

    lower_family = lower_dielectric["family"]
    upper_family = upper_dielectric["family"]

    if lower_family == "prepreg" and upper_family == "core":
        return (
            "down",
            f"{metal_id}_high-{metal_id}_h",
            f"{upper_dielectric['id']}_low",
            "prepreg-metal-core: the copper grows downward into the prepreg.",
        )

    if lower_family == "core" and upper_family == "prepreg":
        return (
            "up",
            f"{lower_dielectric['id']}_high",
            f"{metal_id}_low+{metal_id}_h",
            "core-metal-prepreg: the copper grows upward into the prepreg.",
        )

    if lower_family == "core" and upper_family == "core":
        return (
            "up",
            f"{lower_dielectric['id']}_high",
            f"{metal_id}_low+{metal_id}_h",
            "core-metal-core: the copper sits on the upper face of the lower core.",
        )

    return (
        "up",
        f"{lower_dielectric['id']}_high",
        f"{metal_id}_low+{metal_id}_h",
        "prepreg-metal-prepreg fallback: the copper is referenced upward from the lower dielectric.",
    )


def _build_layer_definitions(layers_bottom_up: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    definitions: List[Dict[str, Any]] = []

    for index, layer in enumerate(layers_bottom_up):
        family = _layer_family(layer)
        layer_id = _sanitize_identifier(layer.get("id", f"Layer_{index + 1}"))
        display_name = _safe_str(layer.get("name")) or layer_id
        thickness_mm = _to_float(layer.get("thickness"), 0.0)

        entry = {
            "id": layer_id,
            "raw_id": _safe_str(layer.get("id", layer_id)) or layer_id,
            "name": display_name,
            "family": family,
            "thickness_mm": thickness_mm,
            "material_name": _escape_python_string(_infer_hfss_material(layer)),
            "color_rgb": _hex_to_rgb_string(
                layer.get("color_hex"),
                fallback="#CC5500" if family == "metal" else "#708090",
            ),
            "transparency": 0.35 if family == "core" else 0.55,
        }
        definitions.append(entry)

    previous_dielectric_id: Optional[str] = None
    for entry in definitions:
        if entry["family"] == "metal":
            continue

        entry["low_expr"] = "0mm" if previous_dielectric_id is None else f"{previous_dielectric_id}_high"
        entry["h_expr"] = _format_length(entry["thickness_mm"], prefer_um=False)
        entry["high_expr"] = f"{entry['id']}_low+{entry['id']}_h"
        previous_dielectric_id = entry["id"]

    for index, entry in enumerate(definitions):
        if entry["family"] != "metal":
            continue

        lower_dielectric = next(
            (definitions[i] for i in range(index - 1, -1, -1) if definitions[i]["family"] != "metal"),
            None,
        )
        upper_dielectric = next(
            (definitions[i] for i in range(index + 1, len(definitions)) if definitions[i]["family"] != "metal"),
            None,
        )

        direction, low_expr, high_expr, logic_note = _resolve_metal_position(
            metal_id=entry["id"],
            lower_dielectric=lower_dielectric,
            upper_dielectric=upper_dielectric,
        )

        entry["direction"] = direction
        entry["low_expr"] = low_expr
        entry["h_expr"] = _format_length(entry["thickness_mm"], prefer_um=True)
        entry["high_expr"] = high_expr
        entry["logic_note"] = logic_note

    return definitions


def generate_hfss_script(
    stackup_data: Dict[str, Any],
    diel_x: str = "10mm",
    diel_y: str = "10mm",
    project_name: str = "Project1",
    design_name: str = "HFSSDesign1",
) -> str:
    """Generate a syntactically valid AEDT Python script from the current stack-up."""
    layers = stackup_data.get("layers", [])
    if not layers:
        return "# No layers defined in stackup_data.\n"

    layer_definitions = _build_layer_definitions(list(reversed(layers)))

    lines = [
        "# ----------------------------------------------",
        "# Script Generated by PCB Stack-up & Via Visualizer",
        "# ----------------------------------------------",
        "import ScriptEnv",
        'ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")',
        "oDesktop.RestoreWindow()",
        f'oProject = oDesktop.SetActiveProject("{_escape_python_string(project_name)}")',
        f'oDesign = oProject.SetActiveDesign("{_escape_python_string(design_name)}")',
        'oEditor = oDesign.SetActiveEditor("3D Modeler")',
        "",
        "def add_local_variable(name, value):",
        "    oDesign.ChangeProperty(",
        "        [",
        '            "NAME:AllTabs",',
        "            [",
        '                "NAME:LocalVariableTab",',
        '                ["NAME:PropServers", "LocalVariables"],',
        "                [",
        '                    "NAME:NewProps",',
        "                    [",
        '                        "NAME:" + name,',
        '                        "PropType:=", "VariableProp",',
        '                        "UserDef:=", True,',
        '                        "Value:=", value,',
        "                    ],",
        "                ],",
        "            ],",
        "        ]",
        "    )",
        "",
        "def add_separator(name):",
        "    oDesign.ChangeProperty(",
        "        [",
        '            "NAME:AllTabs",',
        "            [",
        '                "NAME:LocalVariableTab",',
        '                ["NAME:PropServers", "LocalVariables"],',
        "                [",
        '                    "NAME:NewProps",',
        "                    [",
        '                        "NAME:" + name,',
        '                        "PropType:=", "SeparatorProp",',
        '                        "UserDef:=", True,',
        '                        "Value:=", "",',
        "                    ],",
        "                ],",
        "            ],",
        "        ]",
        "    )",
        "",
        "def create_dielectric_box(name, z_position, z_size, material_name, color_rgb, transparency=0.55):",
        "    oEditor.CreateBox(",
        "        [",
        '            "NAME:BoxParameters",',
        '            "XPosition:=", "-DielX/2",',
        '            "YPosition:=", "-DielY/2",',
        '            "ZPosition:=", z_position,',
        '            "XSize:=", "DielX",',
        '            "YSize:=", "DielY",',
        '            "ZSize:=", z_size,',
        "        ],",
        "        [",
        '            "NAME:Attributes",',
        '            "Name:=", name,',
        '            "Flags:=", "",',
        '            "Color:=", color_rgb,',
        '            "Transparency:=", transparency,',
        '            "PartCoordinateSystem:=", "Global",',
        '            "UDMId:=", "",',
        '            "MaterialValue:=", "\\\"{}\\\"".format(material_name),',
        '            "SurfaceMaterialValue:=", "",',
        '            "SolveInside:=", True,',
        '            "ShellElement:=", False,',
        '            "ShellElementThickness:=", "0mm",',
        '            "ReferenceTemperature:=", "20cel",',
        '            "IsMaterialEditable:=", True,',
        '            "UseMaterialAppearance:=", False,',
        '            "IsLightweight:=", False,',
        "        ],",
        "    )",
        "",
        "# Global stack-up variables",
        f'add_local_variable("DielX", "{_escape_python_string(diel_x)}")',
        f'add_local_variable("DielY", "{_escape_python_string(diel_y)}")',
        'add_separator("PCB_Stackup")',
        "",
        "# Z = 0 at the base of the lowest dielectric",
    ]

    for entry in layer_definitions:
        lines.append(f"# [{entry['raw_id']}] {entry['name']}")

        if entry["family"] == "metal":
            lines.append(f"# {entry['logic_note']}")
            if entry["direction"] == "down":
                lines.append(f'add_local_variable("{entry["id"]}_h", "{entry["h_expr"]}")')
                lines.append(f'add_local_variable("{entry["id"]}_high", "{entry["high_expr"]}")')
                lines.append(f'add_local_variable("{entry["id"]}_low", "{entry["low_expr"]}")')
            else:
                lines.append(f'add_local_variable("{entry["id"]}_low", "{entry["low_expr"]}")')
                lines.append(f'add_local_variable("{entry["id"]}_h", "{entry["h_expr"]}")')
                lines.append(f'add_local_variable("{entry["id"]}_high", "{entry["high_expr"]}")')
        else:
            lines.append(f'add_local_variable("{entry["id"]}_low", "{entry["low_expr"]}")')
            lines.append(f'add_local_variable("{entry["id"]}_h", "{entry["h_expr"]}")')
            lines.append(f'add_local_variable("{entry["id"]}_high", "{entry["high_expr"]}")')
            lines.append(
                f'create_dielectric_box("{entry["id"]}_box", "{entry["id"]}_low", "{entry["id"]}_h", '
                f'"{entry["material_name"]}", "{entry["color_rgb"]}", transparency={entry["transparency"]})'
            )

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
