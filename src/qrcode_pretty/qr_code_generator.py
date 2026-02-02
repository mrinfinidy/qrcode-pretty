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
import sys


# Custom function for eye styling. These create the eye masks
class Qr_image_parts:
    def __init__(
        self,
        embeded_image_name,
        inner_eyes_image,
        inner_eye_mask,
        outer_eyes_image,
        outer_eye_mask,
        qr_image,
        qr_image_simple,
    ) -> None:
        self.embeded_image_name = embeded_image_name
        self.inner_eyes_image = inner_eyes_image
        self.inner_eye_mask = inner_eye_mask
        self.outer_eyes_image = outer_eyes_image
        self.outer_eye_mask = outer_eye_mask
        self.qr_image = qr_image
        self.qr_image_simple = qr_image_simple


def find_default_image():
    """Find the default image in standard locations.
    
    Searches for the default image in the following order:
    1. Environment variable DEFAULT_IMAGE (highest priority)
    2. System-wide install: /usr/share/qrcode-pretty/assets/default.png
    3. Python prefix install: {sys.prefix}/share/qrcode-pretty/assets/default.png
    4. Local development: ./assets/default.png
    5. Package relative: ../../assets/default.png (from module directory)
    
    Returns:
        str: Path to the default image, or fallback to ./assets/default.png
    """
    search_paths = [
        os.environ.get("DEFAULT_IMAGE"),
        "/usr/share/qrcode-pretty/assets/default.png",
        os.path.join(sys.prefix, "share/qrcode-pretty/assets/default.png"),
        "./assets/default.png",
        os.path.join(os.path.dirname(__file__), "..", "..", "assets", "default.png"),
    ]
    
    for path in search_paths:
        if path and os.path.isfile(path):
            return path
    
    return "./assets/default.png"


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
):
    inner_eyes_image = qr.make_image(
        image_factory=StyledPilImage,
        eye_drawer=drawer_instance_inner,
        color_mask=SolidFillColorMask(front_color=hex_to_rgb(inner_eye_color)),
    )

    outer_eyes_image = qr.make_image(
        image_factory=StyledPilImage,
        eye_drawer=drawer_instance_outer,
        color_mask=SolidFillColorMask(front_color=hex_to_rgb(outer_eye_color)),
    )

    embeded_image_name = input_image

    if embeded_image_name == "default":
        embeded_image_path = find_default_image()
    elif embeded_image_name:
        path_expanded = os.path.expanduser(embeded_image_name)
        if os.path.isfile(path_expanded):
            embeded_image_path = path_expanded
        else:
            embeded_image_path = None
    else:
        embeded_image_path = None

    kwargs = {
        "image_factory": StyledPilImage,
        "module_drawer": drawer_instance,
        "color_mask": SolidFillColorMask(front_color=hex_to_rgb(base_color)),
    }
    if embeded_image_path:
        kwargs["embeded_image_path"] = embeded_image_path

    qr_image = qr.make_image(**kwargs)

    qr_image_simple = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer_instance,
        color_mask=SolidFillColorMask(front_color=hex_to_rgb(base_color)),
    )

    inner_eye_mask = style_inner_eyes(qr_image, box_size, border, qr.modules_count)
    outer_eye_mask = style_outer_eyes(qr_image, box_size, border, qr.modules_count)
    return Qr_image_parts(
        embeded_image_name,
        inner_eyes_image,
        inner_eye_mask,
        outer_eyes_image,
        outer_eye_mask,
        qr_image,
        qr_image_simple,
    )


# Generate qr code based on image input
def generate_qr_code(qr, qr_image_parts, drawer_instance):
    qr_image_parts.inner_eyes_image = qr_image_parts.inner_eyes_image.convert("RGBA")
    qr_image_parts.outer_eyes_image = qr_image_parts.outer_eyes_image.convert("RGBA")
    qr_image_parts.qr_image = qr_image_parts.qr_image.convert("RGBA")
    qr_image_parts.inner_eye_mask = qr_image_parts.inner_eye_mask.convert("L")
    qr_image_parts.outer_eye_mask = qr_image_parts.outer_eye_mask.convert("L")

    if (
        not qr_image_parts.embeded_image_name
        or qr_image_parts.embeded_image_name == "blank"
    ):
        intermediate_image = Image.composite(
            qr_image_parts.inner_eyes_image,
            qr_image_parts.qr_image_simple,
            qr_image_parts.inner_eye_mask,
        )
    elif qr_image_parts.embeded_image_name == "default":
        intermediate_image = Image.composite(
            qr_image_parts.inner_eyes_image,
            qr_image_parts.qr_image,
            qr_image_parts.inner_eye_mask,
        )
    else:
        embeded_image_path = os.path.expanduser(qr_image_parts.embeded_image_name)
        if not os.path.isabs(embeded_image_path) and not os.path.isfile(
            embeded_image_path
        ):
            embeded_image_path = os.path.join("./assets/", embeded_image_path)

        qr_image = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=drawer_instance,
            embeded_image_path=embeded_image_path,
        )
        intermediate_image = Image.composite(
            qr_image_parts.inner_eyes_image, qr_image, qr_image_parts.inner_eye_mask
        )

    return Image.composite(
        qr_image_parts.outer_eyes_image,
        intermediate_image,
        qr_image_parts.outer_eye_mask,
    )


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
    )
    final_image = generate_qr_code(qr, qr_image_parts, drawer_instance)
    save_image(final_image, output_dir)


# Additionaly to the png qrcode an svg is created as well
def make_qrcode_svg(input_data, output_dir="~/Pictures/qrcode-pretty/"):
    output_dir = os.path.expanduser(output_dir)  # Expand tilde
    qr = create_qrcode_instance()
    add_data(qr, input_data)
    qr_svg = qr.make_image(
        image_factory=qrcode.image.svg.SvgImage,
        module_drawer=SvgSquareDrawer(),
    )
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    result_path = os.path.join(output_dir, "qrcode.svg")
    print("Saving qr-code (svg) to: ", result_path)
    qr_svg.save(result_path)
