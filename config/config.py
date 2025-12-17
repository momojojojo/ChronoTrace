import os
from dotenv import load_dotenv
import yaml

# 1. Load environment variables from .env

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# 2. Load YAML configuration (non-secret settings)

CONFIG_PATH = os.path.join("config", "config.yaml")

with open(CONFIG_PATH, "r") as f:
    yaml_config = yaml.safe_load(f)

# Project info
PROJECT_NAME = yaml_config["project"]["name"]
PROJECT_VERSION = yaml_config["project"]["version"]

# Paths
PATHS = yaml_config["paths"]

# LoRA training config
LORA_CONFIG = yaml_config["lora"]

# Classifier config
CLASSIFIER_CONFIG = yaml_config["classifier"]

# Graph thresholds
GRAPH_CONFIG = yaml_config["graph"]
