import yaml
from rich import print as rprint

from ...core.config import Settings


def load_configs(config_file_path: str) -> Settings:
    """載入設定檔

    Args:
        config_file_path (str): 設定檔檔案路徑

    Returns:
        Settings: 各項參數的設定
    """
    try:        
        with open(config_file_path, 'r', encoding='utf-8') as file:
            yaml_config = yaml.safe_load(file)
        settings = Settings(**yaml_config)
        if settings.flow_schema.system.verbose == True:
            rprint(settings.flow_schema)
        return settings
    except FileNotFoundError:
        print("\033[1;31m" + f"Configuration file not found: {config_file_path}" + "\033[0m")
        raise
    except yaml.YAMLError as e:
        print("\033[1;31m" + f"[blod red]Error parsing YAML file: {e}" + "\033[0m")
        raise