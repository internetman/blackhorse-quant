#!/usr/bin/env python3
"""
游资席位跟踪
"""

import sys
import os

# 添加项目路径
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_path)

from src.services.hot_money_tracker import HotMoneyTracker

def main():
    """游资跟踪"""
    print("💸 游资席位跟踪")
    print("-" * 60)

    module = HotMoneyTracker()
    result = module.run()

    print(result)

if __name__ == "__main__":
    main()
