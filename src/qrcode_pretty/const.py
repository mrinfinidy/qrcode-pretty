#!/usr/bin/env python

from qrcode.image.styles.moduledrawers.pil import (
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer
)

from qrcode.constants import (
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
    ERROR_CORRECT_H
)

ALLOWED_STYLES = {
    "square",
    "gapped-square",
    "circle",
    "round",
    "vertical-bars",
    "horizontal-bars"
}

DRAWER_CLASSES = {
    "square": SquareModuleDrawer,
    "gapped-square": GappedSquareModuleDrawer,
    "circle": CircleModuleDrawer,
    "round": RoundedModuleDrawer,
    "vertical-bars": VerticalBarsDrawer,
    "horizontal-bars": HorizontalBarsDrawer,
}


STYLE_MAPPING = {
    "SquareModuleDrawer": "square",
    "GappedSquareModuleDrawer": "gapped-square",
    "CircleModuleDrawer": "circle",
    "RoundedModuleDrawer": "round",
    "VerticalBarsDrawer": "vertical-bars",
    "HorizontalBarsDrawer": "horizontal-bars",
}

ERROR_CORRECTION_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H
}

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}
