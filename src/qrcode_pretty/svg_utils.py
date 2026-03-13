import os
import base64
import io

from qrcode_pretty.qr_code_generator import find_default_image
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


# Draw various styles of qrcode code designs

def svg_draw_square(x, y, size, color):
    return f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{color}"/>'


def svg_draw_gapped_square(x, y, size, color, gap_ratio=0.2):
    gap = size * gap_ratio / 2
    inner_size = size * (1 - gap_ratio)
    return f'<rect x="{x + gap}" y="{y + gap}" width="{inner_size}" height="{inner_size}" fill="{color}"/>'

def svg_draw_circle(x, y, size, color):
    radius = size / 2
    cx = x + radius
    cy = y + radius
    return f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}"/>'


def svg_draw_rounded(x, y, size, color, corner_radius_ratio=0.3):
    corner_radius = size * corner_radius_ratio
    return f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{corner_radius}" ry="{corner_radius}" fill="{color}"/>'


def svg_draw_vertical_bars(x, y, size, color, modules, row, col, modules_count):
    if row > 0 and modules[row - 1][col]:
        return None

    bar_height = size
    check_row = row + 1
    while check_row < modules_count and modules[check_row][col]:
        bar_height += size
        check_row += 1

    return f'<rect x="{x}" y="{y}" width="{size}" height="{bar_height}" fill="{color}"/>'


def svg_draw_horizontal_bars(x, y, size, color, modules, row, col, modules_count):
    if col > 0 and modules[row][col - 1]:
        return None

    bar_width = size
    check_col = col + 1
    while check_col < modules_count and modules[row][check_col]:
        bar_width += size
        check_col += 1

    return f'<rect x="{x}" y="{y}" width="{bar_width}" height="{size}" fill="{color}"/>'      


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

def draw_modules(svg_parts, modules, modules_count, border, box_size, base_color, style, drawer_func,):
    for y in range(modules_count):
        for x in range(modules_count):
            if modules[y][x] and not should_skip_module(x, y, modules_count):
                px = (border + x) * box_size
                py = (border + y) * box_size

                if style in ["vertical-bars", "horizontal-bars"]:
                    element = drawer_func(px, py, box_size, base_color, modules, y, x, modules_count)
                else:
                    element = drawer_func(px, py, box_size, base_color)

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

    for x_mod, y_mod in eye_positions:
        x = (border + x_mod) * box_size
        y = (border + y_mod) * box_size

        for deltaY in range(7):
            for deltaX in range(7):
                # Skip 3x3 hole in the middle
                if 2 <= deltaX <= 4 and 2 <= deltaY <= 4:
                    continue

                px = x + deltaX * box_size
                py = y + deltaY * box_size

                element = outer_drawer_func(px, py, box_size, outer_eye_color)
                if element:
                    elements.append(element)

        for deltaY in range(3):
            for deltaX in range(3):
                px = x + (2 + deltaX) * box_size
                py = y + (2 + deltaY) * box_size

                element = inner_drawer_func(px, py, box_size, inner_eye_color)
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
