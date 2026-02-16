"""Load config.yaml from the same directory as the calling script."""

import os
import yaml

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def load():
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)
