"""
FastAPI 服务启动脚本

用法:
    # 基础启动
    conda activate xiaozhi-server
    cd D:/Programming/Python/PythonProjects/xiaozhi-esp32-server/main/xiaozhi-server
    python app_fastapi.py

    # 指定端口
    python app_fastapi.py --port 8005

    # 生产模式（无热重载，多 worker）
    python app_fastapi.py --no-reload --workers 4

    # 指定 host
    python app_fastapi.py --host 127.0.0.1
"""
import argparse
import os
import sys
from pathlib import Path

import uvicorn


def parse_args():
    parser = argparse.ArgumentParser(description="小智 AI FastAPI 服务")
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("XIAOZHI_HOST", "0.0.0.0"),
        help="监听地址 (默认: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("XIAOZHI_PORT", "8004")),
        help="监听端口 (默认: 8004)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.getenv("XIAOZHI_RELOAD", "true").lower() == "true",
        help="启用热重载 (开发模式)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_false",
        dest="reload",
        help="禁用热重载 (生产模式)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("XIAOZHI_WORKERS", "1")),
        help="Worker 数量 (生产模式建议 2-4)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("XIAOZHI_LOG_LEVEL", "info"),
        choices=["debug", "info", "warning", "error", "critical"],
        help="日志级别 (默认: info)",
    )
    return parser.parse_args()


def check_prerequisites():
    """检查启动前置条件"""
    server_dir = Path(__file__).parent
    config_file = server_dir / "config.yaml"

    if not config_file.exists():
        print(f"⚠️  警告: 配置文件不存在: {config_file}")
        print("   首次启动会自动生成默认配置")

    python_version = sys.version_info
    if python_version < (3, 10):
        print(f"❌ 错误: 需要 Python 3.10+，当前版本: {python_version.major}.{python_version.minor}")
        sys.exit(1)


def print_banner(host: str, port: int, reload: bool, workers: int):
    """打印启动信息"""
    mode = "🔧 开发模式" if reload else "🚀 生产模式"
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                    小智 AI FastAPI 服务                       ║
╠═══════════════════════════════════════════════════════════════╣
║  模式: {mode:<54} ║
║  地址: http://{host}:{port:<40} ║
║  文档: http://{'localhost' if host == '0.0.0.0' else host}:{port}/docs{' ' * 35} ║
║  Workers: {workers:<51} ║
╚═══════════════════════════════════════════════════════════════╝
""")


def main():
    args = parse_args()

    check_prerequisites()
    print_banner(args.host, args.port, args.reload, args.workers)

    uvicorn.run(
        "api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level,
        access_log=True,
    )


if __name__ == "__main__":
    main()