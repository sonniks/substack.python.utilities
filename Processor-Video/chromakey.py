# chromakey.py
from PIL import Image
import numpy as np
import os
import glob
from logger import log


def hex_to_rgb(hexcolor):
    """
    Convert a hex color string to an RGB tuple. (duplicated from negative.py - fix?
    :param hexcolor:
    :return:
    """
    hexcolor = hexcolor.lstrip('#')
    return tuple(int(hexcolor[i:i+2], 16) for i in (0, 2, 4))


def resize_to_match(img1, img2):
    """
    Resize two images to match each other's dimensions while maintaining aspect ratio.
    :param img1:
    :param img2:
    :return:
    """
    if img1.size == img2.size:
        return img1, img2
    if img1.size[0] * img1.size[1] > img2.size[0] * img2.size[1]:
        img2 = img2.resize(img1.size, Image.BILINEAR)
    else:
        img1 = img1.resize(img2.size, Image.BILINEAR)
    return img1, img2


def chroma_key(fg, bg, keycolor, tolerance, white_protect=180):
    """
    Apply chroma key effect to the foreground image using the specified key color and background image.
    :param fg:
    :param bg:
    :param keycolor:
    :param tolerance:
    :param white_protect:
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
    key_rgb = np.array([r, g, b])
    dominant_channel = np.argmax(key_rgb)
    other_channels = [i for i in range(3) if i != dominant_channel]
    pixel_dominant = (
        (fg_data[:, :, dominant_channel] > fg_data[:, :, other_channels[0]] + 10) &
        (fg_data[:, :, dominant_channel] > fg_data[:, :, other_channels[1]] + 10)
    )
    luma = fg_data[:, :, :3].mean(axis=2)
    is_bright = luma > white_protect
    mask = (diff < tolerance) & pixel_dominant & (~is_bright)
    output = np.where(mask[:, :, None], bg_data, fg_data)
    return Image.fromarray(output, 'RGBA')


def process(inputfile, outputfile, keycolor, workdir, sequence_prefix, tolerance=30, background_sequence=None):
    """
Process a single image or a sequence of images for chroma keying.
    :param inputfile:
    :param outputfile:
    :param keycolor:
    :param workdir:
    :param sequence_prefix:
    :param tolerance:
    :param background_sequence:
    :return:
    """
    key_rgb = hex_to_rgb(keycolor)
    if os.path.isfile(inputfile):
        if not background_sequence or not os.path.isfile(background_sequence):
            print("Error: Background file required for single image input.")
            return
        try:
            fg = Image.open(inputfile)
            bg = Image.open(background_sequence)
            fg, bg = resize_to_match(fg, bg)
            result = chroma_key(fg, bg, key_rgb, tolerance)
            result.save(outputfile)
        except Exception as e:
            print(f"Error processing single image: {e}")
    else:
        fg_frames = sorted(glob.glob(os.path.join(inputfile, f"{sequence_prefix}_*.png")))
        if not fg_frames:
            print(f"Error: No foreground frames found in {inputfile}")
            return
        use_static = False
        static_bg = None
        bg_frames = []
        if background_sequence:
            if os.path.isfile(background_sequence):
                try:
                    static_bg = Image.open(background_sequence)
                    use_static = True
                    log(f"Using static background image: {background_sequence}")
                except Exception as e:
                    print(f"Error loading static background: {e}")
                    return
            elif os.path.isdir(background_sequence):
                bg_frames = sorted(glob.glob(os.path.join(background_sequence, f"{sequence_prefix}_*.png")))
                if not bg_frames:
                    print(f"Error: No background sequence found in {background_sequence}")
                    return
                log(f"Using background frame sequence from: {background_sequence}")
            else:
                print(f"Error: Invalid background path: {background_sequence}")
                return
        else:
            print("Error: No background sequence or static background provided.")
            return
        frame_count = len(fg_frames) if use_static else min(len(fg_frames), len(bg_frames))
        for i in range(frame_count):
            try:
                if i % 30 == 0 or i == frame_count - 1:
                    log(f"Processing frame {i + 1} of {frame_count}")
                fg = Image.open(fg_frames[i])
                bg = static_bg.copy() if use_static else Image.open(bg_frames[i])
                fg, bg = resize_to_match(fg, bg)
                result = chroma_key(fg, bg, key_rgb, tolerance)
                out_path = os.path.join(workdir, f"{sequence_prefix}_{i:04}.png")
                result.save(out_path)
            except Exception as e:
                print(f"Frame {i} failed: {e}")
