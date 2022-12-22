from baiduIndex import baiduIndex
import pandas as pd

import config as cg
from utils import getCitycode

if __name__ == "__main__":
    keywords = ['布洛芬', '发烧']
    city_names = ['北京', '石家庄', '上海']

    # baidu_index = baiduIndex(keywords, getCitycode(city_names))
    baidu_index = baiduIndex(keywords, days=30, savemode=1)
    baidu_index.search()
