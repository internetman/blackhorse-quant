#!/usr/bin/env python3
"""
买入信号分析
"""

import sys
import os

# 添加项目路径
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_path)

from src.services.buy_signal import BuySignal

def main():
    """买入信号分析"""
    print("📈 买入信号分析")
    print("-" * 60)

    module = BuySignal()

    # 如果有命令行参数，分析指定股票
    if len(sys.argv) > 1:
        symbols = sys.argv[1:]
        print(f"分析股票: {', '.join(symbols)}")
        print()
        result = module.run(symbols)
    else:
        # 分析市场热门股
        result = module.run()

    print(result)

if __name__ == "__main__":
    main()
