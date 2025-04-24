# videotoimage.py
import cv2
import os
import glob

def extract_frames(video_path, output_dir, prefix):
    if not os.path.exists(video_path):
        print(f"Error: Video not found: {video_path}")
        return False
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video: {video_path}")
        return False
    os.makedirs(output_dir, exist_ok=True)
    frame_index = 0
    success = True
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        filename = os.path.join(output_dir, f"{prefix}_{frame_index:04}.png")
        if not cv2.imwrite(filename, frame):
            print(f"Error: Failed to write frame {frame_index}")
            success = False
        frame_index += 1
    cap.release()
    return success

def frames_to_video(input_dir, prefix, output_path, fps=30):
    pattern = os.path.join(input_dir, f"{prefix}_*.png")
    images = sorted(glob.glob(pattern))
    if not images:
        print(f"Error: No images found with prefix {prefix}")
        return False
    first_frame = cv2.imread(images[0])
    height, width, layers = first_frame.shape
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
