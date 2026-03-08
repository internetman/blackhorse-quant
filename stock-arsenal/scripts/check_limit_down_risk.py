#!/usr/bin/env python3
"""
跌停板预警
"""

import sys
import os

# 添加项目路径
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_path)

from src.services.limit_down_predictor import LimitDownPredictor

def main():
    """跌停预警"""
    print("⚠️  跌停板预警")
    print("-" * 60)

    module = LimitDownPredictor()
    result = module.run()

    print(result)

if __name__ == "__main__":
    main()
