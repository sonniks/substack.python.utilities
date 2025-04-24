import argparse
import os
import re
import numpy as np # Import NumPy
from PIL import Image, ImageOps, UnidentifiedImageError
# import traceback # Uncomment for detailed error trace


def hex_to_rgb(hex_color):
    """
    Converts a hex color string to an RGB tuple.
    :param hex_color:
    :return:
    """
    hex_color = hex_color.lstrip('#')
    if not re.match(r'^[0-9a-fA-F]{6}$', hex_color):
        raise ValueError("Invalid hex color format. Use RRGGBB or #RRGGBB.")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_yes_no(prompt):
    """
    Prompts the user for a yes/no response.
    :param prompt:
    :return:
    """
    while True:
        try:
            response = input(f"{prompt} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        except EOFError:
            print("\nInput stream ended. Assuming 'no'.")
            return False


def get_filename(prompt, default_ext=".png"):
    """
    Prompts the user for a filename, ensuring it is valid and has a proper extension.
    :param prompt:
    :param default_ext:
    :return:
    """
    while True:
        try:
            filename = input(f"{prompt}: ").strip()
            if not filename:
                print("Filename cannot be empty.")
                continue
            # Basic validation (can be expanded)
            if os.path.sep in filename or any(c in filename for c in '<>:"/\\|?*'):
                 print("Filename contains invalid characters.")
                 continue
            # Ensure it has a common image extension
            root, ext = os.path.splitext(filename)
            if not ext:
                filename += default_ext
                print(f"No extension provided, appending '{default_ext}'. Saved as: {filename}")
            # Check if directory exists (if path includes directories)
            dirname = os.path.dirname(filename)
            if dirname and not os.path.isdir(dirname):
                print(f"Error: Directory '{dirname}' does not exist.")
                continue
            return filename
        except EOFError:
            print("\nInput stream ended. Cannot get filename.")
            return None
        except Exception as e:
            print(f"An error occurred getting the filename: {e}")
            # traceback.print_exc() # Uncomment for detailed error trace
            return None


def get_hex_color(prompt):
    """
    Prompts the user for a hex color code and converts it to an RGB tuple.
    :param prompt:
    :return:
    """
    while True:
        try:
            hex_input = input(f"{prompt} (e.g., #FF0000 or FF0000): ").strip()
            if not hex_input:
                print("Hex code cannot be empty.")
                continue
            rgb_color = hex_to_rgb(hex_input)
            return rgb_color # Return the RGB tuple
        except ValueError as e:
            print(f"Error: {e}")
        except EOFError:
            print("\nInput stream ended. Cannot get hex code.")
            return None


def create_negative(image_path):
    """
    Creates a photo negative of the given image.
    :param image_path:
    :return:
    """
    try:
        print(f"Loading image: {image_path}...")
        img = Image.open(image_path)
        # Ensure image is loaded correctly
        img.load()
        # 1. Create the color inverted version (traditional negative part)
        # Ensure image is in RGB mode for inversion
        img_rgb = img.convert('RGB')
        inverted_rgb = ImageOps.invert(img_rgb)
        # 2. Create the alpha channel based on original brightness
        # Convert original image to grayscale ('L' mode)
        # Brighter original pixels will have higher values (closer to 255) = denser negative
        alpha_channel = img.convert('L')
        # 3. Combine inverted color with the brightness-based alpha
        # Convert the inverted color image to RGBA
        negative_rgba = inverted_rgb.convert('RGBA')
        # Apply the grayscale brightness map as the alpha channel
        negative_rgba.putalpha(alpha_channel)
        print("Negative created successfully.")
        return negative_rgba
    except FileNotFoundError:
        print(f"Error: Input file not found at '{image_path}'")
        return None
    except UnidentifiedImageError:
        print(f"Error: Cannot identify image file. Is '{image_path}' a valid image?")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during negative creation: {e}")
        # traceback.print_exc() # Uncomment for detailed error trace
        return None


def apply_light(negative_image, light_color_rgb):
    """
    Applies a colored light effect to the negative image.
    :param negative_image:
    :param light_color_rgb:
    :return:
    """
    try:
        print(f"Applying light with color RGB: {light_color_rgb}...")
        if not isinstance(negative_image, Image.Image) or negative_image.mode != 'RGBA':
             print("Error: apply_light requires a valid RGBA negative image.")
             return None
        # 1. Create a solid background layer of the light color
        color_layer = Image.new('RGB', negative_image.size, light_color_rgb)
        color_layer_rgba = color_layer.convert('RGBA')
        # 2. Composite the negative onto the color layer
        intermediate_image = Image.alpha_composite(color_layer_rgba, negative_image)
        # 3. Invert the composite result (gives OriginalColor * Alpha/255)
        inverted_composite_rgb = ImageOps.invert(intermediate_image.convert('RGB'))
        # --- Brightness Correction using NumPy ---
        print("Applying brightness correction...")
        # Get the original brightness map (alpha channel)
        alpha_channel = negative_image.getchannel('A')
        # Convert images to NumPy arrays for calculation (use float for precision)
        rgb_array = np.array(inverted_composite_rgb, dtype=np.float32)
        alpha_array = np.array(alpha_channel, dtype=np.float32)
        # Avoid division by zero: where alpha is 0, the rgb is already 0 (black),
        # so scaling factor doesn't matter. We'll use np.divide's 'where' clause.
        # Create scale factor: 255.0 / alpha. Add a dimension for broadcasting over RGB channels.
        # Use a small epsilon to prevent true zero division if needed, though 'where' is better.
        scale_factor = np.zeros_like(alpha_array)
        np.divide(255.0, alpha_array, out=scale_factor, where=alpha_array != 0)
        scale_factor_rgb = np.expand_dims(scale_factor, axis=-1) # Shape (H, W, 1)
        # Apply scaling: Corrected RGB = (OriginalColor * Alpha/255) * (255 / Alpha)
        corrected_rgb_array = rgb_array * scale_factor_rgb
        # Clamp values to the valid 0-255 range and convert back to uint8
        corrected_rgb_array = np.clip(corrected_rgb_array, 0, 255)
        final_rgb_array = corrected_rgb_array.astype(np.uint8)
        # Convert NumPy array back to PIL Image
        final_image = Image.fromarray(final_rgb_array, 'RGB')
        print("Brightness correction applied.")
        return final_image
    except ImportError:
        print("Error: NumPy is required for brightness correction. Please install it (`pip install numpy`).")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during light application: {e}")
        # traceback.print_exc() # Uncomment for detailed error trace
        return None


def save_image(image, filename):
    """
    Saves the given image to the specified filename.
    :param image:
    :param filename:
    :return:
    """
    if image is None or not filename:
        print("Error: Cannot save None image or with empty filename.")
        return False
    try:
        print(f"Saving image to '{filename}'...")
        # Ensure the image is in a savable mode (e.g., RGB for JPG, RGBA for PNG)
        save_mode = image.mode
        if os.path.splitext(filename)[1].lower() in ['.jpg', '.jpeg'] and image.mode == 'RGBA':
            print("Info: Saving as JPG, converting RGBA to RGB (alpha channel lost).")
            image = image.convert('RGB')
            save_mode = 'RGB' # Update mode for message

        image.save(filename)
        print(f"Image ({save_mode}) saved successfully.")
        return True
    except IOError as e:
        print(f"Error: Could not save image to '{filename}'. Check permissions or path. Reason: {e}")
    except ValueError as e: # Handle issues like unknown extension
         print(f"Error: Could not save image to '{filename}'. Is the extension supported? Reason: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during saving: {e}")
        # traceback.print_exc() # Uncomment for detailed error trace
    return False


def main():
    """
    Main function to create a photo negative and simulate projecting light through it.
    :return:
    """
    parser = argparse.ArgumentParser(
        description="Create a photo negative and simulate projecting light through it.",
        epilog="Example: python negative_light.py my_photo.jpg"
    )
    parser.add_argument("image_file", help="Path to the input image file.")
    args = parser.parse_args()
    # --- Create Negative ---
    negative_img = create_negative(args.image_file)
    if negative_img is None:
        return # Exit if negative creation failed
    # --- Save Negative (Optional) ---
    if get_yes_no("Save the created negative image (RGBA format recommended)?"):
        neg_filename = get_filename("Enter filename for the negative image", default_ext=".png")
        if neg_filename:
            # Save the RGBA negative directly
            save_image(negative_img, neg_filename)
    # --- Simulate Light (Optional) ---
    if get_yes_no("Simulate projecting colored light through the negative?"):
        light_rgb = get_hex_color("Enter the hex code for the light color (e.g., FFFFFF for white)")
        if light_rgb:
            # --- Apply Light ---
            final_img = apply_light(negative_img, light_rgb) # Use the brightness corrected function
            if final_img:
                # --- Save Final Image ---
                final_filename = get_filename("Enter filename for the final projected image", default_ext=".jpg")
                if final_filename:
                    save_image(final_img, final_filename) # Save the final RGB image
    print("\nProcessing complete.")


if __name__ == "__main__":
    main()
