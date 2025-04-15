import argparse
from PIL import Image
import numpy as np
import os


def parse_args():
    """
    Parse command line arguments for the chroma key script.
    :return:
    """
    parser = argparse.ArgumentParser(description="Simple chroma key compositing script.")
    parser.add_argument('--foreground', required=True, help="Path to the foreground image (PNG/JPG)")
    parser.add_argument('--background', required=True, help="Path to the background image (PNG/JPG)")
    parser.add_argument('--keycolor', required=True, help="Target key color as hex (e.g., #00FF00 for green)")
    parser.add_argument('--tolerance', type=int, default=30, help="Tolerance for color similarity (default: 30)")
    parser.add_argument('--output', required=True, help="Path to save the output image")
    return parser.parse_args()


def hex_to_rgb(hexcolor):
    """
    Converts a hex color string to an RGB tuple.
    :param hexcolor:
    :return:
    """
    hexcolor = hexcolor.lstrip('#')
    return tuple(int(hexcolor[i:i+2], 16) for i in (0, 2, 4))


def resize_to_match(img1, img2):
    """
    Resize two images to match each other's dimensions.
    :param img1:
    :param img2:
    :return:
    """
    if img1.size == img2.size:
        return img1, img2
    # Resize smaller image to match larger one
    if img1.size[0] * img1.size[1] > img2.size[0] * img2.size[1]:
        img2 = img2.resize(img1.size, Image.BILINEAR)
    else:
        img1 = img1.resize(img2.size, Image.BILINEAR)
    return img1, img2


def chroma_key(fg, bg, keycolor, tolerance, white_protect=180):
    """
    Perform chroma key compositing on the foreground image using the specified key color and background image.
    :param fg: image with the "green" for masking
    :param bg: image that will be laid into the mask color area
    :param keycolor: target color to mask out (as RGB tuple)
    :param tolerance: tolerance figure for color similarity (default: 30)
    :param white_protect: threshould of "whitish" colors to mask out (lighting, glares) (255 = absolute white)
    :return:
    """
    fg_data = np.array(fg.convert("RGBA"))
    bg_data = np.array(bg.convert("RGBA"))
    r, g, b = keycolor
    diff = np.sqrt(
        (fg_data[:, :, 0] - r) ** 2 +
        (fg_data[:, :, 1] - g) ** 2 +
        (fg_data[:, :, 2] - b) ** 2
    )
    # Determine dominant channel in key color
    key_rgb = np.array([r, g, b])
    dominant_channel = np.argmax(key_rgb)
    other_channels = [i for i in range(3) if i != dominant_channel]
    # Color dominance check
    pixel_dominant = (
        (fg_data[:, :, dominant_channel] > fg_data[:, :, other_channels[0]] + 10) &
        (fg_data[:, :, dominant_channel] > fg_data[:, :, other_channels[1]] + 10)
    )
    # Luma (brightness) – using simple average, or you can do weighted: 0.299*R + 0.587*G + 0.114*B
    luma = fg_data[:, :, :3].mean(axis=2)
    is_bright = luma > white_protect
    # Final mask: pixel must be close to key color, dominantly that color, and NOT very bright
    mask = (diff < tolerance) & pixel_dominant & (~is_bright)
    print(f"Masked pixels: {np.sum(mask)}")
    output = np.where(mask[:, :, None], bg_data, fg_data)
    return Image.fromarray(output, 'RGBA')


def main():
    """
    Main function to run the chroma key compositing.
    :return:
    """
    args = parse_args()
    if not os.path.exists(args.foreground) or not os.path.exists(args.background):
        print("One or both input files not found.")
        return
    fg = Image.open(args.foreground)
    bg = Image.open(args.background)
    fg, bg = resize_to_match(fg, bg)
    keycolor = hex_to_rgb(args.keycolor)
    result = chroma_key(fg, bg, keycolor, args.tolerance)
    result.save(args.output)
    print(f"Chroma key output saved to {args.output}")


if __name__ == "__main__":
    main()
