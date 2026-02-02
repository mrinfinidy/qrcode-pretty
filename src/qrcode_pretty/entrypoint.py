#!/usr/bin/env python

import sys
import getopt
from .qr_code_generator import make_qrcode, make_qrcode_svg
from .const import DRAWER_CLASSES, ERROR_CORRECTION_LEVELS

def print_usage():
    print("""Usage: qrcode-pretty [options]

Options:
  -h, --help                              Show this help message and exit
  -d, --data <data>                       Data to encode in QR code (required)
  -i, --image <image>                     Input image file name (optional)
  -s, --style <style>                     Style for the QR code modules (optional)
      --style-inner <style>               Style for the inner eyes (optional)
      --style-outer <style>               Style for the outer eyes (optional)
  -b, --base <hex>                        Base color hex code (e.g. #000000)
  -n, --color-inner <hex>                 Inner eye color hex code
  -r, --color-outer <hex>                 Outer eye color hex code
  -o, --output <directory or filename>    Output directory path or filename (default: ~/Pictures/qrcode-pretty/qrcode.png)
      --svg                               Also generate SVG output (optional flag)
      --version <int>                     QR version (default: 5)
      --box-size <int>                    Box size in pixels (default: 10)
      --border <int>                      Border size in boxes (default: 4)
      --error-correction <L|M|Q|H>        Error correction level (default: H)

Available styles: square, gapped-square, circle, round, vertical-bars, horizontal-bars

Example:
  entrypoint.py -d "https://example.com" -i logo.png -b #000000 -n #000fff -r #fff000 -o ./output --style circle --style-inner square --style-outer circle --svg
""")

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    kwargs = {}
    include_svg = False

    try:
        opts, args = getopt.getopt(
            argv,
            "hi:o:d:b:n:r:s:",
            [
                "image=",
                "output=",
                "data=",
                "base=",
                "color-inner=",
                "color-outer=",
                "svg",
                "style=",
                "style-inner=",
                "style-outer=",
                "version=",
                "box-size=",
                "border=",
                "error-correction="
            ]
        )
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()

        elif opt in ("-d", "--data"):
            kwargs["input_data"] = arg

        elif opt in ("-i", "--image"):
            kwargs["input_image"] = arg

        elif opt in ("-s", "--style"):
            if arg not in DRAWER_CLASSES:
                print(f"Error: style '{arg}' not recognized. Choose one of: {', '.join(DRAWER_CLASSES.keys())}")
                sys.exit(1)
            kwargs["drawer_instance"] = DRAWER_CLASSES[arg]()

        elif opt == "--style-inner":
            if arg not in DRAWER_CLASSES:
                print(f"Error: style-inner '{arg}' not recognized. Choose one of: {', '.join(DRAWER_CLASSES.keys())}")
                sys.exit(1)
            kwargs["drawer_instance_inner"] = DRAWER_CLASSES[arg]()

        elif opt == "--style-outer":
            if arg not in DRAWER_CLASSES:
                print(f"Error: style-outer '{arg}' not recognized. Choose one of: {', '.join(DRAWER_CLASSES.keys())}")
                sys.exit(1)
            kwargs["drawer_instance_outer"] = DRAWER_CLASSES[arg]()

        elif opt in ("-b", "--base"):
            kwargs["base_color"] = arg

        elif opt in ("-n", "--color-inner"):
            kwargs["inner_eye_color"] = arg

        elif opt in ("-r", "--color-outer"):
            kwargs["outer_eye_color"] = arg

        elif opt == "--version":
            kwargs["version"] = int(arg)

        elif opt == "--box-size":
            kwargs["box_size"] = int(arg)

        elif opt == "--border":
            kwargs["border"] = int(arg)

        elif opt == "--error-correction":
            ec_levels = ERROR_CORRECTION_LEVELS
            arg_upper = arg.upper()
            if arg_upper in ec_levels:
                kwargs["error_correction"] = ec_levels[arg_upper]
            else:
                print("Invalid error correction level. Choose from: L, M, Q, H.")
                sys.exit(1)

        elif opt in ("-o", "--output"):
            kwargs["output_dir"] = arg

        elif opt == "--svg":
            include_svg = True

    if "input_data" not in kwargs:
        print("Error: Missing required option --data/-d")
        print_usage()
        sys.exit(1)

    make_qrcode(**kwargs)

    if include_svg:
        make_qrcode_svg(kwargs["input_data"], kwargs.get("output_dir", "~/Pictures/qrcode-pretty/"))

if __name__ == "__main__":
    main(sys.argv[1:])
