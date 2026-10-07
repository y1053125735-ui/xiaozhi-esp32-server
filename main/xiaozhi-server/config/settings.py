# import os
# import asyncio
# from config.config_loader import read_config, get_project_dir, load_config
#
#
# default_config_file = "config.yaml"
# config_file_valid = False
#
#
# def check_config_file():
#     global config_file_valid
#     if config_file_valid:
#         return
#     """
#     简化的配置检查，仅提示用户配置文件的使用情况
#     """
#     custom_config_file = get_project_dir() + "data/." + default_config_file
#     if not os.path.exists(custom_config_file):
#         raise FileNotFoundError(
#             "找不到data/.config.yaml文件，请按教程确认该配置文件是否存在"
#         )
#
#     # 检查是否从API读取配置
#     config = asyncio.run(load_config())
#     if config.get("read_config_from_api", False):
#         print("从API读取配置")
#         old_config_origin = read_config(custom_config_file)
#         if old_config_origin.get("selected_module") is not None:
#             error_msg = "您的配置文件好像既包含智控台的配置又包含本地配置：\n"
#             error_msg += "\n建议您：\n"
#             error_msg += "1、将根目录的config_from_api.yaml文件复制到data下，重命名为.config.yaml\n"
#             error_msg += "2、按教程配置好接口地址和密钥\n"
#             raise ValueError(error_msg)
#     config_file_valid = True

import os
import asyncio
from config.config_loader import read_config, get_project_dir, load_config


default_config_file = "config.yaml"
config_file_valid = False


def _load_config_sync():
    """同步加载配置，兼容已存在事件循环的场景"""
    try:
        asyncio.get_running_loop()
        has_running_loop = True
    except RuntimeError:
        has_running_loop = False

    if has_running_loop:
        from config.config_loader import merge_configs, ensure_directories
        from core.utils.cache.manager import cache_manager, CacheType

        cached = cache_manager.get(CacheType.CONFIG, "main_config")
        if cached is not None:
            return cached

        default_config_path = get_project_dir() + "config.yaml"
        custom_config_path = get_project_dir() + "data/.config.yaml"
        default_config = read_config(default_config_path)
        custom_config = read_config(custom_config_path)
        config = merge_configs(default_config, custom_config)
        ensure_directories(config)
        cache_manager.set(CacheType.CONFIG, "main_config", config)
        return config
    else:
        return asyncio.run(load_config())


def check_config_file():
    global config_file_valid
    if config_file_valid:
        return
    """
    简化的配置检查，仅提示用户配置文件的使用情况
    """
    custom_config_file = get_project_dir() + "data/." + default_config_file
    if not os.path.exists(custom_config_file):
        raise FileNotFoundError(
            "找不到data/.config.yaml文件，请按教程确认该配置文件是否存在"
        )

    # 检查是否从API读取配置
    config = _load_config_sync()
    if config.get("read_config_from_api", False):
        print("从API读取配置")
        old_config_origin = read_config(custom_config_file)
        if old_config_origin.get("selected_module") is not None:
            error_msg = "您的配置文件好像既包含智控台的配置又包含本地配置：\n"
            error_msg += "建议您：\n"
            error_msg += "1、将根目录的config_from_api.yaml文件复制到data下，重命名为.config.yaml\n"
            error_msg += "2、按教程配置好接口地址和密钥\n"
            raise ValueError(error_msg)
    config_file_valid = True