# video_upscale.py

import os
import cv2
import glob
import shutil
import argparse
import subprocess
import numpy as np
import time
from tqdm import tqdm
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
import torchvision.transforms.functional as TF
from torchvision.transforms.functional import to_tensor
import torch


# class PatchedRealESRGANer(RealESRGANer):
#     def enhance(self, img, outscale=None, alpha_upsampler='realesrgan'):
#         if not isinstance(img, np.ndarray):
#             raise TypeError("Input must be a NumPy array")
#         if img.dtype != np.float32:
#             img = img.astype(np.float32)
#         if np.max(img) > 1.0:
#             img /= 255.0  # normalize
#         return super().enhance(img, outscale, alpha_upsampler)


def extract_frames(input_video, orig_dir):
    """
    Extract frames from a video file and save them as images.
    :param input_video:
    :param orig_dir:
    :return:
    """
    os.makedirs(orig_dir, exist_ok=True)
    cap = cv2.VideoCapture(input_video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for i in tqdm(range(total), desc="Extracting frames"):
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imwrite(os.path.join(orig_dir, f"frame_{i:05d}.png"), frame)
    cap.release()
    return fps, total


def upscale_frames(orig_dir, upscale_dir, model_path):
    """
    Upscale images in a directory using Real-ESRGAN.
    :param orig_dir:
    :param upscale_dir:
    :param model_path:
    :return:
    """
    os.makedirs(upscale_dir, exist_ok=True)
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                    num_block=23, num_grow_ch=32, scale=4)
    # use_cuda = torch.cuda.is_available()
    upsampler = RealESRGANer(
        scale=4,
        model_path=model_path,
        model=model,
        tile=256,  # force tiling
        tile_pad=10,
        pre_pad=0,
        half=True if torch.cuda.is_available() else False,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    # print(f"[DEBUG] Using device: {torch.cuda.current_device()}")
    # print(f"[DEBUG] Device name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
    # print(f"[DEBUG] GPU memory allocated: {torch.cuda.memory_allocated()} bytes")
    # print(f"[DEBUG] GPU memory reserved: {torch.cuda.memory_reserved()} bytes")
    frame_files = sorted(f for f in os.listdir(orig_dir) if f.endswith(".png"))
    for i, fname in enumerate(tqdm(frame_files, desc="Upscaling frames")):
        img_path = os.path.join(orig_dir, fname)
        img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        # Normalize to float32 in [0, 1] — but keep it NumPy
        if img.dtype != np.float32:
            img = img.astype(np.float32) / 255.0
        start = time.time()
        output, _ = upsampler.enhance(img, outscale=1.5)
        end = time.time()
        # Debug output
        # print(f"[TIMING] Inference time: {end - start:.2f} sec")
        # print(f"[DEBUG] Frame: {fname}")
        # print(f"[DEBUG] Image dtype: {img.dtype}, shape: {img.shape}")
        # print(f"[DEBUG] CUDA is available: {torch.cuda.is_available()}")
        # print(f"[DEBUG] Current device: {torch.cuda.current_device()}")
        # print(f"[DEBUG] Device name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
        # print(f"[DEBUG] Memory allocated: {torch.cuda.memory_allocated()} bytes")
        # print(f"[DEBUG] Memory reserved: {torch.cuda.memory_reserved()} bytes")
        # print(f"[DEBUG] Model is on device: {next(model.parameters()).device}")
        cv2.imwrite(os.path.join(upscale_dir, fname), output)


def frames_to_video(input_dir, prefix, output_path, fps=30):
    """
    Convert a series of images to a video file using OpenCV.
    :param input_dir:
    :param prefix:
    :param output_path:
    :param fps:
    :return:
    """
    pattern = os.path.join(input_dir, f"{prefix}_*.png")
    images = sorted(glob.glob(pattern))
    if not images:
        print(f"Error: No images found with prefix {prefix}")
        return False
    first_frame = cv2.imread(images[0])
    height, width, _ = first_frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    for img_path in images:
        frame = cv2.imread(img_path)
        if frame is None:
            print(f"Warning: Skipping unreadable frame {img_path}")
            continue
        out.write(frame)
    out.release()
    return True


def reassemble_video_alt(upscale_dir, output_file, fps):
    """
    Old ffmpeg method — kept for fallback or alternate use.
    """
    if not os.path.exists(upscale_dir):
        print(f"[ERROR] Upscale directory '{upscale_dir}' not found.")
        return

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(upscale_dir, "frame_%05d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_file
    ]
    subprocess.run(cmd, check=True)


def cleanup_dirs(*dirs):
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)

def main():
    """
    Main function to handle command line arguments and orchestrate the video upscaling process.
    :return:
    """
    parser = argparse.ArgumentParser(description="Video Upscaler with Real-ESRGAN")
    parser.add_argument("--inputfile", required=True, help="Input source video file")
    parser.add_argument("--outputfile", required=True, help="Output 1080p video file")
    parser.add_argument("--workdir", required=True, help="Temporary work directory")
    parser.add_argument("--cleanup", action="store_true", help="Delete work directories after processing")
    args = parser.parse_args()
    orig_dir = os.path.join(args.workdir, "origframes")
    upscale_dir = os.path.join(args.workdir, "upscaledframes")
    model_path = "Real-ESRGAN/weights/RealESRGAN_x4plus.pth"
    print(">>> Step 1: Extracting frames...")
    fps, total = extract_frames(args.inputfile, orig_dir)
    print(">>> Step 2: Upscaling frames...")
    upscale_frames(orig_dir, upscale_dir, model_path)
    print(">>> Step 3: Reassembling video (OpenCV)...")
    success = frames_to_video(upscale_dir, prefix="frame", output_path=args.outputfile, fps=fps)
    if not success:
        print("[FAIL] Video assembly failed.")
        return
    if args.cleanup:
        print(">>> Cleaning up temporary directories...")
        cleanup_dirs(orig_dir, upscale_dir)
    print(f"\nDONE. Upscaled video saved as: {args.outputfile}")


if __name__ == "__main__":
    main()
