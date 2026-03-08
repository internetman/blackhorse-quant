#!/usr/bin/env python3
"""
A股武器库 - 依赖安装脚本
"""

import subprocess
import sys

def install_dependencies():
    """安装核心依赖"""

    print("=" * 60)
    print("📦 A股武器库 - 依赖安装")
    print("=" * 60)
    print()

    # 核心依赖
    packages = [
        "efinance",    # 东方财富数据（推荐）
        "rich",        # 终端美化
        "pyyaml",      # 配置管理
        "loguru",      # 日志
        "pandas",      # 数据分析
    ]

    # 可选依赖
    optional_packages = [
        "akshare",     # 金融数据接口
        "baostock",    # 证券数据
    ]

    print("🔧 安装核心依赖...")
    print()

    for package in packages:
        print(f"  安装 {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
            print(f"  ✅ {package} 安装成功")
        except subprocess.CalledProcessError:
            print(f"  ❌ {package} 安装失败")
            return False

    print()
    print("🔧 安装可选依赖（如果失败不影响核心功能）...")
    print()

    for package in optional_packages:
        print(f"  安装 {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
            print(f"  ✅ {package} 安装成功")
        except subprocess.CalledProcessError:
            print(f"  ⚠️  {package} 安装失败（可忽略）")

    print()
    print("=" * 60)
    print("✅ 依赖安装完成！")
    print("=" * 60)
    print()
    print("📝 下一步：")
    print("  1. 运行程序: python src/main.py")
    print("  2. 查看文档: README.md 或 QUICKSTART.md")
    print()

    return True

if __name__ == "__main__":
    install_dependencies()
