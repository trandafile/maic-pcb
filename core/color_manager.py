from __future__ import annotations

from copy import deepcopy
import re


DEFAULT_PALETTE_NAME = "Classic"
PALETTE_SLOTS = [
    ("metal", 1, "Metal Layer"),
    ("core", 2, "Dielectric Core"),
    ("prepreg", 3, "Prepreg"),
    ("cover", 4, "Cover"),
]

PALETTES = {
    "Classic": {
        "metal": {"name": "Standard Copper", "hex": "#D47335"},
        "core": {"name": "Olive FR4 Green", "hex": "#768A48"},
        "prepreg": {"name": "Lighter Khaki/Green", "hex": "#95A969"},
        "cover": {"name": "Dark Solder Mask Green", "hex": "#1E5631"},
    },
    "Dark Mode": {
        "metal": {"name": "Bright Copper", "hex": "#E88C30"},
        "core": {"name": "Dark Slate", "hex": "#2C3E50"},
        "prepreg": {"name": "Muted Blue-Grey", "hex": "#4B6584"},
        "cover": {"name": "Near Black/Charcoal", "hex": "#111418"},
    },
    "Blueprint": {
        "metal": {"name": "Technical Gold/Yellow", "hex": "#F9A826"},
        "core": {"name": "Deep Drafting Blue", "hex": "#004B87"},
        "prepreg": {"name": "Light Cyan", "hex": "#4AA3DF"},
        "cover": {"name": "Paper Off-White", "hex": "#E0E6ED"},
    },
    "Industrial": {
        "metal": {"name": "Vibrant Orange/Copper", "hex": "#FF6B35"},
        "core": {"name": "Cool Gunmetal Grey", "hex": "#8D99AE"},
        "prepreg": {"name": "Light Silver/Grey", "hex": "#EDF2F4"},
        "cover": {"name": "Dark Matte Navy/Black", "hex": "#2B2D42"},
    },
}


def normalize_hex_color(value, fallback="#708090"):
    color = str(value or "").strip()
    if not color:
        color = fallback

    if not color.startswith("#"):
        color = f"#{color}"

    if re.fullmatch(r"#[0-9a-fA-F]{3}", color):
        color = "#" + "".join(ch * 2 for ch in color[1:])

    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        color = fallback

    return color.upper()


def _shift_color(hex_value, factor):
    hex_value = normalize_hex_color(hex_value)
    r = int(hex_value[1:3], 16)
    g = int(hex_value[3:5], 16)
    b = int(hex_value[5:7], 16)

    if factor >= 1:
        r = min(255, int(r + (255 - r) * (factor - 1)))
        g = min(255, int(g + (255 - g) * (factor - 1)))
        b = min(255, int(b + (255 - b) * (factor - 1)))
    else:
        r = max(0, int(r * factor))
        g = max(0, int(g * factor))
        b = max(0, int(b * factor))

    return f"#{r:02X}{g:02X}{b:02X}"


def get_palette_names():
    return list(PALETTES.keys())


def get_palette_definition(palette_name=None):
    palette_name = palette_name if palette_name in PALETTES else DEFAULT_PALETTE_NAME
    return deepcopy(PALETTES[palette_name])


def _build_palette_color_map(palette_name):
    palette = get_palette_definition(palette_name)
    return {
        role: normalize_hex_color(item['hex']) for role, item in palette.items()
    }


def ensure_palette_state(session_state):
    if 'palette_overrides' not in session_state:
        session_state['palette_overrides'] = {
            name: _build_palette_color_map(name) for name in PALETTES
        }
    else:
        for name in PALETTES:
            session_state['palette_overrides'].setdefault(name, _build_palette_color_map(name))

    if 'active_palette_name' not in session_state or session_state['active_palette_name'] not in PALETTES:
        session_state['active_palette_name'] = DEFAULT_PALETTE_NAME

    session_state['active_palette_colors'] = dict(
        session_state['palette_overrides'][session_state['active_palette_name']]
    )


def get_palette_colors(session_state, palette_name=None):
    ensure_palette_state(session_state)
    palette_name = palette_name if palette_name in PALETTES else session_state['active_palette_name']
    return dict(session_state['palette_overrides'][palette_name])


def set_active_palette(session_state, palette_name):
    ensure_palette_state(session_state)
    palette_name = palette_name if palette_name in PALETTES else DEFAULT_PALETTE_NAME
    session_state['active_palette_name'] = palette_name
    session_state['active_palette_colors'] = get_palette_colors(session_state, palette_name)


def update_palette_color(session_state, palette_name, role, color_hex):
    ensure_palette_state(session_state)
    palette_name = palette_name if palette_name in PALETTES else DEFAULT_PALETTE_NAME
    if role not in session_state['palette_overrides'][palette_name]:
        return
    fallback = get_palette_definition(palette_name).get(role, {}).get('hex', '#708090')
    session_state['palette_overrides'][palette_name][role] = normalize_hex_color(color_hex, fallback=fallback)

    if session_state.get('active_palette_name') == palette_name:
        session_state['active_palette_colors'] = dict(session_state['palette_overrides'][palette_name])


def update_active_palette_color(session_state, role, color_hex):
    ensure_palette_state(session_state)
    update_palette_color(session_state, get_active_palette_name(session_state), role, color_hex)


def reset_palette_colors(session_state, palette_name=None):
    ensure_palette_state(session_state)
    palette_name = palette_name if palette_name in PALETTES else get_active_palette_name(session_state)
    session_state['palette_overrides'][palette_name] = _build_palette_color_map(palette_name)
    if session_state.get('active_palette_name') == palette_name:
        session_state['active_palette_colors'] = dict(session_state['palette_overrides'][palette_name])


def get_active_palette_name(session_state):
    ensure_palette_state(session_state)
    return session_state['active_palette_name']


def get_active_palette_colors(session_state):
    ensure_palette_state(session_state)
    return dict(session_state['active_palette_colors'])


def get_default_palette_role(layer_type):
    layer_type = str(layer_type or "").strip().lower()
    if layer_type in {"metal", "copper"} or "copper" in layer_type:
        return "metal"
    if "prepreg" in layer_type:
        return "prepreg"
    if any(token in layer_type for token in ["cover", "solder", "silk"]):
        return "cover"
    return "core"


def get_role_color(session_state, role):
    ensure_palette_state(session_state)
    fallback = get_palette_definition(get_active_palette_name(session_state)).get(role, {}).get('hex', '#708090')
    return normalize_hex_color(session_state['active_palette_colors'].get(role), fallback=fallback)


def build_preset_options(session_state, palette_name=None):
    ensure_palette_state(session_state)
    palette_name = palette_name if palette_name in PALETTES else get_active_palette_name(session_state)
    palette_def = get_palette_definition(palette_name)
    palette_colors = get_palette_colors(session_state, palette_name)

    preset_options = []
    for role, number, display_name in PALETTE_SLOTS:
        role_info = palette_def[role]
        hex_value = normalize_hex_color(palette_colors.get(role), fallback=role_info['hex'])
        preset_options.append({
            "role": role,
            "number": number,
            "display_name": display_name,
            "name": role_info['name'],
            "hex": hex_value,
            "label": f"Col#{number} - {display_name}: {role_info['name']} ({hex_value})",
        })

    return preset_options


def apply_palette_to_layer(layer, session_state, keep_custom=True):
    color_source = layer.get('color_source', 'palette')
    if keep_custom and color_source == 'custom':
        return

    role = layer.get('palette_role') or get_default_palette_role(layer.get('type'))
    layer['palette_role'] = role
    layer['color_source'] = 'palette'
    layer['color_hex'] = get_role_color(session_state, role)


def apply_palette_to_stackup(session_state, keep_custom=True):
    ensure_palette_state(session_state)
    stackup_data = session_state.get('stackup_data', {})
    for layer in stackup_data.get('layers', []):
        apply_palette_to_layer(layer, session_state, keep_custom=keep_custom)


def build_render_palette(palette_name=None, palette_colors=None):
    palette_def = get_palette_definition(palette_name)
    colors = {}
    for role, _, _ in PALETTE_SLOTS:
        base = palette_def[role]['hex']
        colors[role] = normalize_hex_color((palette_colors or {}).get(role, base), fallback=base)

    metal = colors['metal']
    core = colors['core']
    prepreg = colors['prepreg']
    cover = colors['cover']

    return {
        "cu_top": _shift_color(metal, 1.10),
        "cu_bot": _shift_color(metal, 0.85),
        "cu_text": _shift_color(metal, 0.35),
        "core_top": _shift_color(core, 1.06),
        "core_bot": _shift_color(core, 0.82),
        "core_text": _shift_color(core, 1.45),
        "pp_top": _shift_color(prepreg, 1.04),
        "pp_bot": _shift_color(prepreg, 0.88),
        "pp_text": _shift_color(prepreg, 0.45),
        "sm_top": _shift_color(cover, 1.06),
        "sm_bot": _shift_color(cover, 0.82),
        "sm_text": _shift_color(cover, 1.55),
        "ss_top": "#FFFFFF",
        "ss_bot": "#E0E0E0",
        "ss_text": "#000000",
        "via_l": _shift_color(metal, 0.75),
        "via_c": metal,
        "via_r": _shift_color(metal, 0.75),
        "via_pad_t": _shift_color(metal, 1.10),
        "via_pad_b": _shift_color(metal, 0.92),
        "via_hole": "#1A1A1A",
    }
