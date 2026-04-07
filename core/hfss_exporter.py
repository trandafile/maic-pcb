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


def _build_change_property_block(properties: List[Dict[str, str]], separator_name: Optional[str] = None) -> List[str]:
    lines = [
        "oDesign.ChangeProperty(",
        "    [",
        '        "NAME:AllTabs",',
        "        [",
        '            "NAME:LocalVariableTab",',
        "            [",
        '                "NAME:PropServers", ',
        '                "LocalVariables"',
        "            ],",
        "            [",
        '                "NAME:NewProps",',
    ]

    blocks: List[List[str]] = []
    if separator_name:
        blocks.append([
            "                [",
            f'                    "NAME:{separator_name}",',
            '                    "PropType:="        , "SeparatorProp",',
            '                    "UserDef:="         , True,',
            '                    "Value:="           , ""',
            "                ]",
        ])

    for prop in properties:
        blocks.append([
            "                [",
            f'                    "NAME:{prop["name"]}",',
            f'                    "PropType:="        , "{prop.get("prop_type", "VariableProp")}",',
            '                    "UserDef:="         , True,',
            f'                    "Value:="           , "{prop["value"]}"',
            "                ]",
        ])

    for idx, block in enumerate(blocks):
        if idx < len(blocks) - 1:
            block[-1] += ","
        lines.extend(block)

    lines.extend([
        "            ]",
        "        ]",
        "    ])",
    ])
    return lines


def _build_create_box_block(entry: Dict[str, Any]) -> List[str]:
    return [
        "oEditor.CreateBox(",
        "    [",
        '        "NAME:BoxParameters",',
        '        "XPosition:="        , "-dielX/2",',
        '        "YPosition:="        , "-dielY/2",',
        f'        "ZPosition:="        , "{entry["id"]}_low",',
        '        "XSize:="            , "dielX",',
        '        "YSize:="            , "dielY",',
        f'        "ZSize:="            , "{entry["id"]}_h"',
        "    ], ",
        "    [",
        '        "NAME:Attributes",',
        f'        "Name:="             , "{entry["id"]}_box",',
        '        "Flags:="            , "",',
        f'        "Color:="            , "{entry["color_rgb"]}",',
        f'        "Transparency:="     , {entry["transparency"]},',
        '        "PartCoordinateSystem:=", "Global",',
        '        "UDMId:="            , "",',
        f'        "MaterialValue:="     , "\\"{entry["material_name"]}\\"",',
        '        "SurfaceMaterialValue:=", "\\"\\"",',
        '        "SolveInside:="      , True,',
        '        "ShellElement:="     , False,',
        '        "ShellElementThickness:=", "0mm",',
        '        "ReferenceTemperature:=", "20cel",',
        '        "IsMaterialEditable:=", True,',
        '        "UseMaterialAppearance:=", False,',
        '        "IsLightweight:="    , False',
        "    ])",
    ]


def generate_hfss_script(
    stackup_data: Dict[str, Any],
    diel_x: str = "10mm",
    diel_y: str = "10mm",
    project_name: Optional[str] = None,
    design_name: Optional[str] = None,
) -> str:
    """Generate an AEDT recorder-style Python script from the current stack-up."""
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
        f'oProject = oDesktop.SetActiveProject("{_escape_python_string(project_name)}")' if project_name else 'oProject = oDesktop.GetActiveProject()',
        'if oProject is None:',
        '    raise Exception("Loading project failed: no active AEDT project.")',
        f'oDesign = oProject.SetActiveDesign("{_escape_python_string(design_name)}")' if design_name else 'oDesign = oProject.GetActiveDesign()',
        'if oDesign is None:',
        '    raise Exception("Loading HFSS design failed: no active AEDT design.")',
        'oEditor = oDesign.SetActiveEditor("3D Modeler")',
        "",
        "# Global stack-up variables",
    ]

    lines.extend(
        _build_change_property_block(
            [
                {"name": "dielX", "value": _escape_python_string(diel_x)},
                {"name": "dielY", "value": _escape_python_string(diel_y)},
            ],
            separator_name="PCB_stack_up",
        )
    )
    lines.append("")
    lines.append("# Z = 0 at the base of the lowest dielectric")

    for entry in layer_definitions:
        lines.append(f"# [{entry['raw_id']}] {entry['name']}")

        if entry["family"] == "metal":
            lines.append(f"# {entry['logic_note']}")
            if entry["direction"] == "down":
                props = [
                    {"name": f"{entry['id']}_h", "value": entry["h_expr"]},
                    {"name": f"{entry['id']}_high", "value": entry["high_expr"]},
                    {"name": f"{entry['id']}_low", "value": entry["low_expr"]},
                ]
            else:
                props = [
                    {"name": f"{entry['id']}_low", "value": entry["low_expr"]},
                    {"name": f"{entry['id']}_h", "value": entry["h_expr"]},
                    {"name": f"{entry['id']}_high", "value": entry["high_expr"]},
                ]
            lines.extend(_build_change_property_block(props))
        else:
            props = [
                {"name": f"{entry['id']}_low", "value": entry["low_expr"]},
                {"name": f"{entry['id']}_h", "value": entry["h_expr"]},
                {"name": f"{entry['id']}_high", "value": entry["high_expr"]},
            ]
            lines.extend(_build_change_property_block(props))
            lines.extend(_build_create_box_block(entry))

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
