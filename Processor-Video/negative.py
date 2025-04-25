# negative.py
import re
import numpy as np
import os
import glob
from PIL import Image, ImageOps, UnidentifiedImageError
from logger import log


def hex_to_rgb(hex_color):
    """
    Convert a hex color string to an RGB tuple.
    :param hex_color:
    :return:
    """
    hex_color = hex_color.lstrip('#')
    if not re.match(r'^[0-9a-fA-F]{6}$', hex_color):
        raise ValueError("Invalid hex color format. Use RRGGBB or #RRGGBB.")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_negative(image_path):
    """
    Create a negative image from the given image path.
    :param image_path:
    :return:
    """
    try:
        log(f"Creating negative for image: '{image_path}'")
        img = Image.open(image_path)
        img.load()
        img_rgb = img.convert('RGB')
        inverted_rgb = ImageOps.invert(img_rgb)
        alpha_channel = img.convert('L')
        negative_rgba = inverted_rgb.convert('RGBA')
        negative_rgba.putalpha(alpha_channel)
        return negative_rgba
    except FileNotFoundError:
        print(f"Error: File not found: '{image_path}'")
    except UnidentifiedImageError:
        print(f"Error: Unrecognized image format: '{image_path}'")
    except Exception as e:
        print(f"Error during negative creation: {e}")
    return None


def apply_light(negative_image, light_color_rgb):
    """
    Apply a light color to the negative image and return the corrected RGB image.
    :param negative_image:
    :param light_color_rgb:
    :return:
    """
    try:
        if not isinstance(negative_image, Image.Image) or negative_image.mode != 'RGBA':
            print("Error: Input must be an RGBA image.")
            return None
        color_layer = Image.new('RGB', negative_image.size, light_color_rgb).convert('RGBA')
        intermediate_image = Image.alpha_composite(color_layer, negative_image)
        inverted_composite_rgb = ImageOps.invert(intermediate_image.convert('RGB'))
        alpha_channel = negative_image.getchannel('A')
        rgb_array = np.array(inverted_composite_rgb, dtype=np.float32)
        alpha_array = np.array(alpha_channel, dtype=np.float32)
        scale_factor = np.zeros_like(alpha_array)
        np.divide(255.0, alpha_array, out=scale_factor, where=alpha_array != 0)
        scale_factor_rgb = np.expand_dims(scale_factor, axis=-1)
        corrected_rgb_array = rgb_array * scale_factor_rgb
        corrected_rgb_array = np.clip(corrected_rgb_array, 0, 255).astype(np.uint8)
        return Image.fromarray(corrected_rgb_array, 'RGB')
    except Exception as e:
        print(f"Error during light application: {e}")
    return None

def save_image(image, filename):
    """
    Save the image to the specified filename.
    :param image:
    :param filename:
    :return:
    """
    if image is None or not filename:
        print("Error: Invalid image or filename.")
        return False
    try:
        if filename.lower().endswith(('.jpg', '.jpeg')) and image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(filename)
        return True
    except Exception as e:
        print(f"Error saving image '{filename}': {e}")
    return False


def process(inputfile, outputfile, operation, color, workdir, sequence_prefix):
    """
Process images or sequences to create negative images or apply light color.
    :param inputfile:
    :param outputfile:
    :param operation:
    :param color:
    :param workdir:
    :param sequence_prefix:
    :return:
    """
    if os.path.isdir(inputfile):
        frame_paths = sorted(glob.glob(os.path.join(inputfile, f"{sequence_prefix}_*.png")))
        if not frame_paths:
            log(f"No frames found in {inputfile} for prefix {sequence_prefix}")
            return
        if operation == 'negative':
            for i, frame_path in enumerate(frame_paths):
                img = create_negative(frame_path)
                if img:
                    out_path = os.path.join(workdir, f"{sequence_prefix}_{i:04}.png")
                    save_image(img, out_path)
        elif operation == 'negative-reimage':
            try:
                light_rgb = hex_to_rgb(color)
            except ValueError as e:
                log(f"Color Error: {e}")
                return
            for i, frame_path in enumerate(frame_paths):
                img = create_negative(frame_path)
                if img:
                    result = apply_light(img, light_rgb)
                    if result:
                        out_path = os.path.join(workdir, f"{sequence_prefix}_{i:04}.png")
                        save_image(result, out_path)
    else:
        if operation == 'negative':
            img = create_negative(inputfile)
            if img:
                save_image(img, outputfile)
        elif operation == 'negative-reimage':
            img = create_negative(inputfile)
            if img:
                try:
                    light_rgb = hex_to_rgb(color)
                except ValueError as e:
                    log(f"Color Error: {e}")
                    return
                final_img = apply_light(img, light_rgb)
                if final_img:
                    save_image(final_img, outputfile)