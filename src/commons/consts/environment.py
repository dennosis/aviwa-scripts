import os


class PathConsts:
    DATA_PATH = os.environ.get("DATA_PATH")
    BRONZE_DATA_PATH = f"{DATA_PATH}/bronze"
    SILVER_DATA_PATH = f"{DATA_PATH}/silver"
    GOLD_DATA_PATH = f"{DATA_PATH}/gold"
    MODELS_PATH = os.environ.get("MODELS_PATH")


class GbsConsts:
    GBS_USER = os.environ.get("GBS_USER")
    GBS_PASSWORD = os.environ.get("GBS_PASSWORD")
