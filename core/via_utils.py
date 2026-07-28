"""Back-drill aware via geometry, shared by every rendering engine.

A back-drill is a second, larger-diameter drilling performed AFTER plating: it
removes the unused portion of a plated barrel (the `stub`), shortening the
electrically live length of the via. It is stored as OPTIONAL flat fields on
the via dictionary, so projects saved before this feature keep loading and
rendering exactly as before (a missing `backdrill_side` means "none").

Field convention (industry standard "drill to layer"): the stop layer is the
LAST layer that must remain CONNECTED.
* `top` side    -> the barrel is removed from the top surface down to
  `backdrill_stub` mm above `backdrill_top_layer`.
* `bottom` side -> the barrel is removed from the bottom surface up to
  `backdrill_stub` mm below `backdrill_bottom_layer`.

Layer indices used here are positions in the TOP-DOWN `layers` list
(index 0 = top of the stack), the same convention every engine already uses.
"""

BACKDRILL_SIDES = ["none", "top", "bottom", "both"]

# Added to the drill diameter when `backdrill_diameter` is left at 0 (auto).
BACKDRILL_AUTO_OVERSIZE_MM = 0.2

# Schematic engines (html/svg) use a compressed, non-linear thickness -> px
# mapping, so the stub cannot be converted to pixels: use a fixed tick instead.
BACKDRILL_STUB_PX = 3.0

BACKDRILL_FIELD_DEFAULTS = {
    "backdrill_side": "none",
    "backdrill_top_layer": "",
    "backdrill_bottom_layer": "",
    "backdrill_diameter": 0.0,  # 0 -> auto (drill + BACKDRILL_AUTO_OVERSIZE_MM)
    "backdrill_stub": 0.1,      # mm of barrel left beyond the stop layer
}

DEFAULT_DRILL_DIAMETER = 0.3


def _to_float(value, default):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result != result:  # NaN from the data editor
        return default
    return result


def get_side(via) -> str:
    """Normalized back-drill side; anything unknown/missing means 'none'."""
    side = str(via.get('backdrill_side', 'none') or 'none').strip().lower()
    return side if side in BACKDRILL_SIDES else 'none'


def get_stub(via) -> float:
    """Residual barrel length (mm) left beyond the stop layer."""
    return max(0.0, _to_float(via.get('backdrill_stub'), BACKDRILL_FIELD_DEFAULTS['backdrill_stub']))


def get_diameter(via) -> float:
    """Back-drill bit diameter (mm). 0/empty means auto = drill + oversize."""
    diameter = _to_float(via.get('backdrill_diameter'), 0.0)
    if diameter > 0.0:
        return diameter
    drill = _to_float(via.get('drill_diameter'), DEFAULT_DRILL_DIAMETER)
    return drill + BACKDRILL_AUTO_OVERSIZE_MM


def resolve(via, id_to_idx):
    """Resolve the nominal and the post-back-drill span of a via.

    `id_to_idx` maps layer ID -> position in the top-down layers list.
    Returns None when the via references layers that do not exist (the caller
    already skips those vias). Back-drill entries that are out of range, or
    that would remove the whole barrel, are silently ignored so a half-edited
    project still renders.
    """
    start_idx = id_to_idx.get(via.get('start_layer'))
    end_idx = id_to_idx.get(via.get('end_layer'))
    if start_idx is None or end_idx is None:
        return None

    top_idx = min(start_idx, end_idx)
    bot_idx = max(start_idx, end_idx)

    side = get_side(via)
    bd_top_idx = None
    bd_bot_idx = None

    if side in ('top', 'both'):
        stop_idx = id_to_idx.get(via.get('backdrill_top_layer'))
        # Must stop strictly below the entry layer, otherwise nothing is removed.
        if stop_idx is not None and top_idx < stop_idx <= bot_idx:
            bd_top_idx = stop_idx

    if side in ('bottom', 'both'):
        stop_idx = id_to_idx.get(via.get('backdrill_bottom_layer'))
        if stop_idx is not None and top_idx <= stop_idx < bot_idx:
            bd_bot_idx = stop_idx

    # Crossing back-drills would consume the whole barrel: drop the pair.
    if bd_top_idx is not None and bd_bot_idx is not None and bd_top_idx > bd_bot_idx:
        bd_top_idx = None
        bd_bot_idx = None

    return {
        'top_idx': top_idx,
        'bot_idx': bot_idx,
        'bd_top_idx': bd_top_idx,
        'bd_bot_idx': bd_bot_idx,
        'eff_top_idx': bd_top_idx if bd_top_idx is not None else top_idx,
        'eff_bot_idx': bd_bot_idx if bd_bot_idx is not None else bot_idx,
        'stub': get_stub(via),
        'bd_diameter': get_diameter(via),
        'has_backdrill': bd_top_idx is not None or bd_bot_idx is not None,
    }


def classify_layer(layer_idx, geom):
    """How a layer relates to the via once the back-drill is applied.

    * 'connected'   -> the via lands on this layer (pad).
    * 'unconnected' -> the live barrel crosses it (antipad clearance).
    * 'backdrilled' -> the layer sits in a removed section: the larger
      back-drill bit cut the copper away and the via no longer reaches it.
    * None          -> the via does not touch this layer at all.
    """
    if geom is None or layer_idx < geom['top_idx'] or layer_idx > geom['bot_idx']:
        return None
    if layer_idx < geom['eff_top_idx'] or layer_idx > geom['eff_bot_idx']:
        return 'backdrilled'
    if layer_idx in (geom['eff_top_idx'], geom['eff_bot_idx']):
        return 'connected'
    return 'unconnected'


def clearance_diameter(via, geom, intersect_type, layer_idx=None):
    """Diameter of the hole opened in a metal layer crossed by the via."""
    antipad = _to_float(via.get('antipad_diameter'), 0.8)
    if intersect_type == 'backdrilled':
        # The bit removes copper over its own diameter. A layer the via used to
        # land on had a pad, so only the bore is gone; a layer that was merely
        # crossed already had an antipad, so the wider of the two wins.
        was_connected = layer_idx is not None and layer_idx in (geom['top_idx'], geom['bot_idx'])
        return geom['bd_diameter'] if was_connected else max(geom['bd_diameter'], antipad)
    if intersect_type == 'unconnected':
        return antipad
    return 0.0


def max_radius(via, geom):
    """Largest radius the via occupies, used to space vias apart on X."""
    radii = [
        _to_float(via.get('drill_diameter'), DEFAULT_DRILL_DIAMETER) / 2.0,
        _to_float(via.get('pad_diameter'), 0.0) / 2.0,
        _to_float(via.get('antipad_diameter'), 0.8) / 2.0,
    ]
    if geom is not None and geom['has_backdrill']:
        radii.append(geom['bd_diameter'] / 2.0)
    return max(radii)


def describe(via, geom, layer_ids=None):
    """Short human-readable back-drill summary (hover/tooltip text)."""
    if geom is None or not geom['has_backdrill']:
        return ""

    def label(idx):
        if layer_ids and 0 <= idx < len(layer_ids):
            return str(layer_ids[idx])
        return f"#{idx}"

    parts = []
    if geom['bd_top_idx'] is not None:
        parts.append(f"top &rarr; {label(geom['bd_top_idx'])}")
    if geom['bd_bot_idx'] is not None:
        parts.append(f"bottom &rarr; {label(geom['bd_bot_idx'])}")
    return f"Back-drill {' / '.join(parts)} (&#8960;{geom['bd_diameter']:.3f} mm)"
