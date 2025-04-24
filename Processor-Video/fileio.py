# fileio.py
import os
import glob
from logger import log


def ensure_working_directory(path):
    """
    Ensure that the working directory exists. If it does not, create it.
    :param path:
    :return:
    """
    if not os.path.exists(path):
        os.makedirs(path)


def get_sequence_files(directory, prefix):
    """
    Get a sorted list of files in the specified directory that match the given prefix.
    :param directory:
    :param prefix:
    :return:
    """
    pattern = os.path.join(directory, f"{prefix}_*.png")
    return sorted(glob.glob(pattern))


def cleanup_sequence(root_dir, prefix):
    """
    Clean up temporary files and directories created during processing.
    :param root_dir:
    :param prefix:
    :return:
    """
    paths_to_check = [root_dir,
                      os.path.join(root_dir, "inputframes"),
                      os.path.join(root_dir, "backgroundframes")]
    for path in paths_to_check:
        if not os.path.exists(path):
            continue
        files = get_sequence_files(path, prefix)
        if not files:
            log(f"No files found for prefix '{prefix}' in {path}")
        for f in files:
            try:
                os.remove(f)
                # log(f"Deleted file: {f}")
            except Exception as e:
                log(f"Failed to delete file: {f} — {e}")
        if os.path.isdir(path) and not os.listdir(path):
            try:
                os.rmdir(path)
                log(f"Deleted empty directory: {path}")
            except Exception as e:
                log(f"Failed to delete directory: {path} — {e}")
    if os.path.isdir(root_dir) and not os.listdir(root_dir):
        try:
            os.rmdir(root_dir)
            log(f"Deleted empty working directory: {root_dir}")
        except Exception as e:
            log(f"Failed to delete working directory: {root_dir} — {e}")
