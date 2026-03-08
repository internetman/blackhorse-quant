#!/usr/bin/env python3
"""
涨停板预测分析
"""

import sys
import os

# 添加项目路径
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_path)

from src.services.limit_up_predictor import LimitUpPredictor

def main():
    """涨停板预测"""
    print("🔥 涨停板预测")
    print("-" * 60)

    module = LimitUpPredictor()
    result = module.run()

    print(result)

if __name__ == "__main__":
    main()
