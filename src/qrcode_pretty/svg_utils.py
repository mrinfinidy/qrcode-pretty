import os
import base64
import io

from qrcode_pretty.input_image_utils import find_default_image
from .const import MIME_TYPES, STYLE_MAPPING

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        image_extension = os.path.splitext(image_path)[1].lower()
        mime_type = MIME_TYPES.get(image_extension, "image/png")

        return f"data:{mime_type};base64,{image_base64}"

def get_eye_positions(modules_count):
    return [
        (0, 0),                 # top-left
        (modules_count - 7, 0), # top-right
        (0, modules_count - 7)  # bottom-left
    ]

def should_skip_module(x, y, modules_count):
    eye_positions = get_eye_positions(modules_count)

    for eye_x, eye_y in eye_positions:
        if eye_x <= x < eye_x + 7 and eye_y <= y < eye_y + 7:
            return True

    return False


def has_neighbor(modules, row, col, direction, modules_count):
    """
    Check if module at (row, col) has an active neighbor in given direction.
    
    Args:
        modules: 2D array of QR code modules
        row: Current module row
        col: Current module column
        direction: 'N', 'S', 'E', or 'W'
        modules_count: Total number of modules
    
    Returns:
        bool: True if neighbor exists and is active
    """
    if direction == 'N':
        neighbor_row, neighbor_col = row - 1, col
    elif direction == 'S':
        neighbor_row, neighbor_col = row + 1, col
    elif direction == 'E':
        neighbor_row, neighbor_col = row, col + 1
    elif direction == 'W':
        neighbor_row, neighbor_col = row, col - 1
    else:
        return False
    
    # Check bounds
    if neighbor_row < 0 or neighbor_row >= modules_count:
        return False
    if neighbor_col < 0 or neighbor_col >= modules_count:
        return False
    
    return bool(modules[neighbor_row][neighbor_col])


# Draw various styles of qrcode code designs

def svg_draw_square(x, y, size, color, modules=None, row=None, col=None, modules_count=None):
    """Simple square module (no neighbor awareness needed)"""
    return f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{color}"/>'


def svg_draw_gapped_square(x, y, size, color, gap_ratio=0.2, modules=None, row=None, col=None, modules_count=None):
    """Gapped square module (no neighbor awareness needed)"""
    gap = size * gap_ratio / 2
    inner_size = size * (1 - gap_ratio)
    return f'<rect x="{x + gap}" y="{y + gap}" width="{inner_size}" height="{inner_size}" fill="{color}"/>'

def svg_draw_circle(x, y, size, color, modules=None, row=None, col=None, modules_count=None):
    """Simple circle module (no neighbor awareness needed)"""
    radius = size / 2
    cx = x + radius
    cy = y + radius
    return f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}"/>'


def svg_draw_rounded(x, y, size, color, modules, row, col, modules_count, radius_ratio=1.0):
    """
    PIL-accurate rounded module drawer with neighbor-aware corner rounding.
    
    Matches RoundedModuleDrawer from qrcode library:
    - Divides module into 4 quadrants (NW, NE, SE, SW)
    - Rounds corners only where both adjacent sides have no neighbors
    - radius_ratio=1 means isolated modules become circles
    """
    # Check neighbors
    has_N = has_neighbor(modules, row, col, 'N', modules_count)
    has_S = has_neighbor(modules, row, col, 'S', modules_count)
    has_E = has_neighbor(modules, row, col, 'E', modules_count)
    has_W = has_neighbor(modules, row, col, 'W', modules_count)
    
    # Determine which corners should be rounded (PIL logic)
    nw_rounded = not has_W and not has_N
    ne_rounded = not has_N and not has_E
    se_rounded = not has_E and not has_S
    sw_rounded = not has_S and not has_W
    
    # Corner radius is half the module size (radius_ratio=1 means full quarter circle)
    corner_radius = (size / 2) * radius_ratio
    
    # Build SVG path with selective corner rounding
    path_parts = []
    
    # Start at top-left corner
    if nw_rounded:
        # Start at top edge, after the curve
        path_parts.append(f"M {x + corner_radius},{y}")
    else:
        # Start at exact corner
        path_parts.append(f"M {x},{y}")
    
    # Top edge to NE corner
    if ne_rounded:
        path_parts.append(f"L {x + size - corner_radius},{y}")
        # Quarter circle arc: sweep right and down
        path_parts.append(f"A {corner_radius},{corner_radius} 0 0 1 {x + size},{y + corner_radius}")
    else:
        path_parts.append(f"L {x + size},{y}")
    
    # Right edge to SE corner
    if se_rounded:
        path_parts.append(f"L {x + size},{y + size - corner_radius}")
        # Quarter circle arc: sweep down and left
        path_parts.append(f"A {corner_radius},{corner_radius} 0 0 1 {x + size - corner_radius},{y + size}")
    else:
        path_parts.append(f"L {x + size},{y + size}")
    
    # Bottom edge to SW corner
    if sw_rounded:
        path_parts.append(f"L {x + corner_radius},{y + size}")
        # Quarter circle arc: sweep left and up
        path_parts.append(f"A {corner_radius},{corner_radius} 0 0 1 {x},{y + size - corner_radius}")
    else:
        path_parts.append(f"L {x},{y + size}")
    
    # Left edge back to NW corner
    if nw_rounded:
        path_parts.append(f"L {x},{y + corner_radius}")
        # Quarter circle arc: sweep up and right
        path_parts.append(f"A {corner_radius},{corner_radius} 0 0 1 {x + corner_radius},{y}")
    else:
        path_parts.append(f"L {x},{y}")
    
    path_parts.append("Z")  # Close path
    
    path_d = " ".join(path_parts)
    return f'<path d="{path_d}" fill="{color}"/>'


def svg_draw_vertical_bars(x, y, size, color, modules, row, col, modules_count, horizontal_shrink=0.8):
    """
    PIL-accurate vertical bars drawer with neighbor-aware rounding.
    
    Matches VerticalBarsDrawer from qrcode library:
    - Draws each module as 2 halves (top and bottom)
    - Horizontally shrunk by 80% (creates vertical gaps between columns)
    - Top half rounded if no North neighbor
    - Bottom half rounded if no South neighbor
    """
    # Check neighbors
    has_N = has_neighbor(modules, row, col, 'N', modules_count)
    has_S = has_neighbor(modules, row, col, 'S', modules_count)
    
    # Calculate dimensions
    half_height = size / 2
    shrunken_width = size * horizontal_shrink
    delta = (size - shrunken_width) / 2  # Center horizontally
    
    # Adjusted x position (centered with shrinking)
    x_adjusted = x + delta
    
    elements = []
    
    # Top half
    if has_N:
        # Square top (connects to neighbor above)
        elements.append(f'<rect x="{x_adjusted}" y="{y}" width="{shrunken_width}" height="{half_height}" fill="{color}"/>')
    else:
        # Rounded top (semi-ellipse on top edge)
        # Draw a rectangle with rounded top: use path with arc
        rx = shrunken_width / 2
        ry = half_height
        path_parts = [
            f"M {x_adjusted},{y + half_height}",  # Bottom-left
            f"L {x_adjusted},{y + ry}",  # Up to where arc starts
            f"A {rx},{ry} 0 0 1 {x_adjusted + shrunken_width},{y + ry}",  # Arc across top
            f"L {x_adjusted + shrunken_width},{y + half_height}",  # Down to bottom-right
            "Z"
        ]
        elements.append(f'<path d="{" ".join(path_parts)}" fill="{color}"/>')
    
    # Bottom half
    if has_S:
        # Square bottom (connects to neighbor below)
        elements.append(f'<rect x="{x_adjusted}" y="{y + half_height}" width="{shrunken_width}" height="{half_height}" fill="{color}"/>')
    else:
        # Rounded bottom (semi-ellipse on bottom edge)
        rx = shrunken_width / 2
        ry = half_height
        path_parts = [
            f"M {x_adjusted},{y + half_height}",  # Top-left
            f"L {x_adjusted},{y + size - ry}",  # Down to where arc starts
            f"A {rx},{ry} 0 0 0 {x_adjusted + shrunken_width},{y + size - ry}",  # Arc across bottom
            f"L {x_adjusted + shrunken_width},{y + half_height}",  # Up to top-right
            "Z"
        ]
        elements.append(f'<path d="{" ".join(path_parts)}" fill="{color}"/>')
    
    return "\n".join(elements) if elements else None


def svg_draw_horizontal_bars(x, y, size, color, modules, row, col, modules_count, vertical_shrink=0.8):
    """
    PIL-accurate horizontal bars drawer with neighbor-aware rounding.
    
    Matches HorizontalBarsDrawer from qrcode library:
    - Draws each module as 2 halves (left and right)
    - Vertically shrunk by 80% (creates horizontal gaps between rows)
    - Left half rounded if no West neighbor (left semi-ellipse)
    - Right half rounded if no East neighbor (right semi-ellipse)
    
    PIL draws an ellipse (width*2, height) and takes left/right halves.
    """
    # Check neighbors
    has_W = has_neighbor(modules, row, col, 'W', modules_count)
    has_E = has_neighbor(modules, row, col, 'E', modules_count)
    
    # Calculate dimensions
    half_width = size / 2
    shrunken_height = size * vertical_shrink
    delta = (size - shrunken_height) / 2  # Center vertically
    
    # Adjusted y position (centered with shrinking)
    y_adjusted = y + delta
    
    elements = []
    
    # Left half
    if has_W:
        # Square left (connects to neighbor on left)
        elements.append(f'<rect x="{x}" y="{y_adjusted}" width="{half_width}" height="{shrunken_height}" fill="{color}"/>')
    else:
        # Rounded left - left half of an ellipse
        # The ellipse has rx=half_width (horizontal radius) and ry=shrunken_height/2 (vertical radius)
        # We want the left semi-ellipse from center-top to center-bottom
        center_x = x + half_width
        center_y = y_adjusted + shrunken_height / 2
        rx = half_width
        ry = shrunken_height / 2
        
        # Path: Start at center-top, arc left to center-bottom, line back to center-top
        path_parts = [
            f"M {center_x},{y_adjusted}",  # Start at center-top
            f"A {rx},{ry} 0 0 0 {center_x},{y_adjusted + shrunken_height}",  # Arc to center-bottom (counter-clockwise, sweep=0)
            f"L {center_x},{y_adjusted}",  # Line back to center-top
            "Z"
        ]
        elements.append(f'<path d="{" ".join(path_parts)}" fill="{color}"/>')
    
    # Right half
    if has_E:
        # Square right (connects to neighbor on right)
        elements.append(f'<rect x="{x + half_width}" y="{y_adjusted}" width="{half_width}" height="{shrunken_height}" fill="{color}"/>')
    else:
        # Rounded right - right half of an ellipse
        center_x = x + half_width
        center_y = y_adjusted + shrunken_height / 2
        rx = half_width
        ry = shrunken_height / 2
        
        # Path: Start at center-top, arc right to center-bottom, line back to center-top
        path_parts = [
            f"M {center_x},{y_adjusted}",  # Start at center-top
            f"A {rx},{ry} 0 0 1 {center_x},{y_adjusted + shrunken_height}",  # Arc to center-bottom (clockwise, sweep=1)
            f"L {center_x},{y_adjusted}",  # Line back to center-top
            "Z"
        ]
        elements.append(f'<path d="{" ".join(path_parts)}" fill="{color}"/>')
    
    return "\n".join(elements) if elements else None      


def get_svg_module_drawer(style):
    style_map = {
        "square": svg_draw_square,
        "gapped-square": svg_draw_gapped_square,
        "circle": svg_draw_circle,
        "round": svg_draw_rounded,
        "vertical-bars": svg_draw_vertical_bars,
        "horizontal-bars": svg_draw_horizontal_bars,
    }
    return style_map.get(style, svg_draw_square)

def draw_modules(svg_parts, modules, modules_count, border, box_size, base_color, style, drawer_func):
    """Draw all QR code modules using the specified drawer function."""
    for row in range(modules_count):
        for col in range(modules_count):
            if modules[row][col] and not should_skip_module(col, row, modules_count):
                px = (border + col) * box_size
                py = (border + row) * box_size
                
                # All drawer functions now accept the same signature
                element = drawer_func(
                    px, py, box_size, base_color,
                    modules=modules,
                    row=row,
                    col=col,
                    modules_count=modules_count
                )
                
                if element:
                    svg_parts.append(element)


def embed_logo(svg_parts, input_image, svg_size, box_size, border):
    if input_image and input_image not in ["blank", None]:
        if input_image == "defaultl":
            logo_path = find_default_image()
        else:
            logo_path = os.path.expanduser(input_image)
            if not os.path.isabs(logo_path) and not os.path.isfile(logo_path):
                logo_path = os.path.join("./assets/", logo_path)

        if os.path.isfile(logo_path):
            logo_element = create_logo_element(logo_path, svg_size, box_size, border)
            if logo_element:
                svg_parts.append(logo_element)


def get_style_name(drawer_instance):
    if drawer_instance is None:
        return None

    drawer_class_name = drawer_instance.__class__.__name__
    return STYLE_MAPPING.get(drawer_class_name, "round")

def create_svg_eye_elements(
    box_size,
    border,
    modules_count,
    inner_eye_color,
    outer_eye_color,
    inner_style="square",
    outer_style="square"
):
    eye_positions = get_eye_positions(modules_count)
    elements = []
    inner_drawer_func = get_svg_module_drawer(inner_style)
    outer_drawer_func = get_svg_module_drawer(outer_style)

    for eye_x_mod, eye_y_mod in eye_positions:
        x_base = (border + eye_x_mod) * box_size
        y_base = (border + eye_y_mod) * box_size
        
        # Create a 7x7 matrix representing the eye pattern
        # Outer frame: edges only (skip the 5x5 interior for the moat)
        # Inner square: 3x3 solid at center
        eye_matrix = [[False] * 7 for _ in range(7)]
        
        # Build outer frame (7x7 edge only)
        for deltaY in range(7):
            for deltaX in range(7):
                # Outer frame: only the edges, skip the 5x5 interior (moat)
                if not (1 <= deltaX <= 5 and 1 <= deltaY <= 5):
                    eye_matrix[deltaY][deltaX] = True
        
        # Draw outer frame with neighbor awareness
        for deltaY in range(7):
            for deltaX in range(7):
                if eye_matrix[deltaY][deltaX]:
                    px = x_base + deltaX * box_size
                    py = y_base + deltaY * box_size
                    
                    element = outer_drawer_func(
                        px, py, box_size, outer_eye_color,
                        modules=eye_matrix,
                        row=deltaY,
                        col=deltaX,
                        modules_count=7
                    )
                    if element:
                        elements.append(element)
        
        # Create a 3x3 matrix for inner square
        inner_matrix = [[True] * 3 for _ in range(3)]
        
        # Draw inner 3x3 square with neighbor awareness
        for deltaY in range(3):
            for deltaX in range(3):
                px = x_base + (2 + deltaX) * box_size
                py = y_base + (2 + deltaY) * box_size
                
                element = inner_drawer_func(
                    px, py, box_size, inner_eye_color,
                    modules=inner_matrix,
                    row=deltaY,
                    col=deltaX,
                    modules_count=3
                )
                if element:
                    elements.append(element)

    return elements

def create_logo_element(logo_path, svg_size, box_size, border):
    try:
        base64_img = image_to_base64(logo_path)

        logo_size = int(svg_size * 0.25)
        logo_x = logo_y = (svg_size - logo_size) // 2

        bg_padding = box_size
        bg_size = logo_size + 2 * bg_padding
        bg_x = logo_x - bg_padding
        bg_y = logo_y - bg_padding

        bg_rectangle = f'<rect x="{bg_x}" y="{bg_y}" width="{bg_size}" height="{bg_size}" fill="white" opacity="0.9"/>'
        img_element = f'<image x="{logo_x}" y="{logo_y}" width="{logo_size}" height="{logo_size}" href="{base64_img}"/>'

        return bg_rectangle + '\n' + img_element
    except Exception as e:
        print(f"Warning: Could not embed logo: {e}")
        return None

def get_svg_output_path(output_dir):
    output_dir = os.path.expanduser(output_dir)

    if os.path.isdir(output_dir) or not os.path.splitext(output_dir)[1]:
        return os.path.join(output_dir, "qrcode.svg")

    base = os.path.splitext(output_dir)[0]
    return base + ".svg"
