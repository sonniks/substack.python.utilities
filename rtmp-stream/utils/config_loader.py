# stream_overlay/utils/config_loader.py


import yaml
import os


def load_config(path):
    """
    Load configuration from a YAML file.
    :param path:
    :return:
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
