#!/usr/bin/env python3
"""
智能选股器
"""

import sys
import os

# 添加项目路径
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_path)

from src.services.stock_screener import StockScreener

def main():
    """智能选股"""
    print("🎯 智能选股器")
    print("-" * 60)

    module = StockScreener()
    result = module.run()

    print(result)

if __name__ == "__main__":
    main()
