#!/usr/bin/env python3
import os
print(f"FLASK_DEBUG env var: '{os.getenv('FLASK_DEBUG')}'")

from src.config import config
print(f"config.FLASK_DEBUG: {config.FLASK_DEBUG}")
print(f"Type: {type(config.FLASK_DEBUG)}")
