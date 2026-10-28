#前面一开始创建项目的时候已经安装了这个依赖
from tqdm import tqdm
import time

# 在 for 循环外包裹 tqdm()
for i in tqdm(range(100)):
    time.sleep(0.1)  # 模拟耗时操作