#!/usr/bin/env python

import qrcode
from qrcode.constants import ERROR_CORRECT_H
import qrcode.image.svg
from qrcode.image.styles.moduledrawers.svg import SvgSquareDrawer
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask, SolidFillColorMask
from PIL import Image, ImageDraw
import os

from qrcode_pretty.input_image_utils import find_default_image
from qrcode_pretty.svg_utils import draw_modules, embed_logo, get_style_name, create_svg_eye_elements, get_svg_module_drawer, get_svg_output_path


def get_logo_path(input_image):
    if not input_image or input_image == "blank":
        return None

    if input_image == "default":
        return find_default_image()

    path_expanded = os.path.expanduser(input_image)
    if os.path.isfile(path_expanded):
        return path_expanded

    assets_path = os.path.join("./assets/", input_image)
    if os.path.isfile(assets_path):
        return assets_path

    return None


def overlay_logo_png(qr_image, logo_path, logo_ratio=0.25):
    if not logo_path or not os.path.isfile(logo_path):
        return qr_image

    try:
        logo = Image.open(logo_path)

        qr_width, qr_height = qr_image.size
        logo_orig_width, logo_orig_height = logo.size

        target_size = int(qr_width * logo_ratio)

        scale = min(target_size / logo_orig_width, target_size / logo_orig_height)
        scaled_width = int(logo_orig_width * scale)
        scaled_height = int(logo_orig_height * scale)

        logo_resized = logo.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        logo_x = (qr_width - scaled_width) // 2
        logo_y = (qr_height - scaled_height) // 2

        if logo_resized.mode != "RGBA":
            logo_resized = logo_resized.convert("RGBA")

        result = qr_image.copy()

        if "A" in logo_resized.getbands():
            result.alpha_composite(logo_resized, (logo_x, logo_y))
        else:
            result.paste(logo_resized, (logo_x, logo_y))

        return result
    except Exception as e:
        print(f"Warning: Could not overlay logo: {e}")
        return qr_image

class Qr_image_parts:
    def __init__(
        self,
        logo_path,
        inner_eyes_image,
        inner_eye_mask,
        outer_eyes_image,
        outer_eye_mask,
        qr_image,
    ) -> None:
        self.logo_path = logo_path
        self.inner_eyes_image = inner_eyes_image
        self.inner_eye_mask = inner_eye_mask
        self.outer_eyes_image = outer_eyes_image
        self.outer_eye_mask = outer_eye_mask
        self.qr_image = qr_image

def hex_to_rgb(hex):
    hex = hex.lstrip("#")
    return (
        int(hex[0:2], 16),
        int(hex[2:4], 16),
        int(hex[4:6], 16),
    )


def style_inner_eyes(image, box_size=10, border=4, modules_count=37):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)

    def draw_eye(x_mod, y_mod):
        # Offset by 2 modules to land in center of 7x7 eye
        x = (border + x_mod + 2) * box_size
        y = (border + y_mod + 2) * box_size
        draw.rectangle((x, y, x + 3 * box_size, y + 3 * box_size), fill=255)

    draw_eye(0, 0)  # top-left
    draw_eye(modules_count - 7, 0)  # top-right
    draw_eye(0, modules_count - 7)  # bottom-left

    return mask


def style_outer_eyes(image, box_size=10, border=4, modules_count=37):
    img_size = image.size[0]
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)

    def draw_eye(x_mod, y_mod):
        x = border * box_size + x_mod * box_size
        y = border * box_size + y_mod * box_size
        draw.rectangle((x, y, x + 7 * box_size, y + 7 * box_size), fill=255)
        draw.rectangle(
            (x + 2 * box_size, y + 2 * box_size, x + 5 * box_size, y + 5 * box_size),
            fill=0,
        )

    draw_eye(0, 0)  # top-left
    draw_eye(modules_count - 7, 0)  # top-right
    draw_eye(0, modules_count - 7)  # bottom-left

    return mask


# Create a QR code instance
def create_qrcode_instance(
    version=5, error_correction=ERROR_CORRECT_H, box_size=10, border=4
):
    return qrcode.QRCode(
        version=version,
        error_correction=error_correction,
        box_size=box_size,
        border=border,
    )


# Add data to the QR code
def add_data(qr, input_data):
    qr.add_data(input_data)
    qr.make(fit=True)


# Create an image from the QR code instance
def create_image(
    qr,
    input_image,
    drawer_instance,
    drawer_instance_inner,
    drawer_instance_outer,
    base_color,
    inner_eye_color,
    outer_eye_color,
    version,
    error_correction,
    box_size,
    border,
    transparent=False,
):
    def get_colors(hex_color):
        """Return front and back colors with matching tuple lengths."""
        rgb = hex_to_rgb(hex_color)
        if transparent:
            return rgb + (255,), (255, 255, 255, 0)  # RGBA front, RGBA back
        return rgb, (255, 255, 255)  # RGB front, RGB back

    inner_front, inner_back = get_colors(inner_eye_color)
    inner_eyes_image = qr.make_image(
        image_factory=StyledPilImage,
        eye_drawer=drawer_instance_inner,
        color_mask=SolidFillColorMask(
            front_color=inner_front,
            back_color=inner_back,
        ),
    )

    outer_front, outer_back = get_colors(outer_eye_color)
    outer_eyes_image = qr.make_image(
        image_factory=StyledPilImage,
        eye_drawer=drawer_instance_outer,
        color_mask=SolidFillColorMask(
            front_color=outer_front,
            back_color=outer_back,
        ),
    )

    logo_path = get_logo_path(input_image)

    base_front, base_back = get_colors(base_color)
    qr_image = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer_instance,
        color_mask=SolidFillColorMask(
            front_color=base_front,
            back_color=base_back,
        ),
    )

    inner_eye_mask = style_inner_eyes(qr_image, box_size, border, qr.modules_count)
    outer_eye_mask = style_outer_eyes(qr_image, box_size, border, qr.modules_count)
    return Qr_image_parts(
        logo_path,
        inner_eyes_image,
        inner_eye_mask,
        outer_eyes_image,
        outer_eye_mask,
        qr_image,
    )


# Generate qr code based on image input
def generate_qr_code(qr, qr_image_parts, drawer_instance):
    qr_image_parts.inner_eyes_image = qr_image_parts.inner_eyes_image.convert("RGBA")
    qr_image_parts.outer_eyes_image = qr_image_parts.outer_eyes_image.convert("RGBA")
    qr_image_parts.qr_image = qr_image_parts.qr_image.convert("RGBA")
    qr_image_parts.inner_eye_mask = qr_image_parts.inner_eye_mask.convert("L")
    qr_image_parts.outer_eye_mask = qr_image_parts.outer_eye_mask.convert("L")

    intermediate_image = Image.composite(
        qr_image_parts.inner_eyes_image,
        qr_image_parts.qr_image,
        qr_image_parts.inner_eye_mask,
    )

    final_image = Image.composite(
        qr_image_parts.outer_eyes_image,
        intermediate_image,
        qr_image_parts.outer_eye_mask,
    )

    if qr_image_parts.logo_path:
        final_image = overlay_logo_png(final_image, qr_image_parts.logo_path)

    return final_image


# Save the image to a file
def save_image(final_image, output_dir):
    output_dir = os.path.expanduser(output_dir) 

    if os.path.isdir(output_dir) or not os.path.splitext(output_dir)[1]:
        if not os.path.exists(output_dir):
            print(f"Output directory '{output_dir}' does not exist. Creating it.")
            os.makedirs(output_dir)
        result_path = os.path.join(output_dir, "qrcode.png")
    else:
        output_parent_dir = os.path.dirname(output_dir)
        if output_parent_dir and not os.path.exists(output_parent_dir):
            print(f"Output directory '{output_parent_dir}' does not exist. Creating it.")
            os.makedirs(output_parent_dir)
        result_path = output_dir

    print("Saving qr-code (png) to: ", result_path)
    final_image.save(result_path)


# main function that calls all steps needed to make a qrcode
def make_qrcode(
    input_data,
    input_image=None,
    drawer_instance=RoundedModuleDrawer(),
    drawer_instance_inner=RoundedModuleDrawer(),
    drawer_instance_outer=RoundedModuleDrawer(),
    base_color="#000000",
    inner_eye_color="#000000",
    outer_eye_color="#000000",
    version=5,
    error_correction=ERROR_CORRECT_H,
    box_size=10,
    border=4,
    output_dir="~/Pictures/qrcode-pretty/",
    transparent=False,
):
    qr = create_qrcode_instance(
        version=version,
        error_correction=error_correction,
        box_size=box_size,
        border=border,
    )
    add_data(qr, input_data)
    qr_image_parts = create_image(
        qr,
        input_image,
        drawer_instance,
        drawer_instance_inner,
        drawer_instance_outer,
        base_color,
        inner_eye_color,
        outer_eye_color,
        version,
        error_correction,
        box_size,
        border,
        transparent,
    )
    final_image = generate_qr_code(qr, qr_image_parts, drawer_instance)
    save_image(final_image, output_dir)


def make_qrcode_svg(
    input_data,
    base_color="#000000",
    inner_eye_color="#000000",
    outer_eye_color="#000000",
    input_image=None,
    version=5,
    error_correction=ERROR_CORRECT_H,
    box_size=10,
    border=4,
    drawer_instance=None,
    drawer_instance_inner=None,
    drawer_instance_outer=None,
    output_dir="~/Pictures/qrcode-pretty/",
    transparent=False,
):
    output_dir = os.path.expanduser(output_dir)  # Expand tilde
    module_style = get_style_name(drawer_instance)
    inner_eye_style = get_style_name(drawer_instance_inner)
    outer_eye_style = get_style_name(drawer_instance_outer)

    if module_style is None:
        module_style = "round"

    if inner_eye_style is None:
        inner_eye_style = module_style

    if outer_eye_style is None:
        outer_eye_style = module_style

    qr = create_qrcode_instance(
        version=version,
        error_correction=error_correction,
        box_size=box_size,
        border=border
    )
    add_data(qr, input_data)

    modules = qr.modules
    modules_count = qr.modules_count
    svg_size = (modules_count + border * 2) * box_size

    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 {svg_size} {svg_size}">',
    ]
    if not transparent:
        svg_parts.append(f'<rect width="{svg_size}" height="{svg_size}" fill="white"/>')
    drawer_func = get_svg_module_drawer(module_style)
    draw_modules(
        svg_parts,
        modules,
        modules_count,
        border,
        box_size,
        base_color,
        module_style,
        drawer_func
    )
    eye_elements = create_svg_eye_elements(
        box_size,
        border,
        modules_count,
        inner_eye_color,
        outer_eye_color,
        inner_eye_style,
        outer_eye_style
    )
    svg_parts.extend(eye_elements)
    embed_logo(svg_parts, input_image, svg_size, box_size, border)
    svg_parts.append('</svg>')
    result_path = get_svg_output_path(output_dir)
    output_parent_dir = os.path.dirname(result_path)
    if output_parent_dir and not os.path.exists(output_parent_dir):
        print(f"Output directory '{output_parent_dir}' does not exist. Creating it.")
        os.makedirs(output_parent_dir)

    print("Saving qr-code (svg) to: ", result_path)
    with open(result_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_parts))
