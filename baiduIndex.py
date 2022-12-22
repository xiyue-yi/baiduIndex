import json
import time
import requests
from selenium import webdriver
import pandas as pd

import config as cg
from utils import strCookie, getHeaderparams

class baiduIndex:
    """
    百度指数
    """
    def __init__(
            self,
            keywords,
            cities = cg.CITY_CODES,
            days = 30,
            savemode=1,
    ):
        self.keywords = keywords
        self.cities = cities
        self.headers = cg.HEADERS
        self.cookie_path = cg.COOKIEPATH
        self.days = days
        self.savemode = savemode
        self.keywords_data = {}

    def search(self):
        """
        逐个城市 搜索话题指数
        :return:
        """
        self._check_cookie()

        i = 0
        for city, code in self.cities.items():
            index = self._get_index(city, code)
            if not index:
                print('Fail to fetch %s data\n' % city)
            else:
                print('%s data fetched' % city)
            i += 1
            if i % 20 == 0:
                time.sleep(2)

        if self.savemode & 1 == 1:
            self._save_excel()
        if self.savemode & 2 > 0:
            self._save_json()

    def _check_cookie(self):
        """
        测试cookie可用性并更新
        :return:
        """

        try:
            with open(cg.COOKIEPATH, 'r') as f:
                cookie = json.load(f)
            f.close()
            self.headers['Cookie'] = strCookie(cookie)
        except:
            print('Cookie不存在，手动添加...')
            self._update_cookie()
            print('Cookie已添加')

        response = requests.get('https://www.baidu.com/', headers=self.headers)
        if response.status_code != 200:
            raise requests.Timeout
        if cg.EXITFLAG in response.text:
            print("Cookie有效，无需更新\n")
        else:
            self._update_cookie()
            print('Cookie已更新')

    def _update_cookie(self):
        """
            手动登录获取新cookie
        :return:
        """
        browser = webdriver.Chrome()
        browser.get(cg.INDEX_URL)
        browser.find_element_by_css_selector("span.username-text").click()
        print("等待登录...")
        while True:
            if browser.find_element_by_css_selector("span.username-text").text != "登录":
                break
            else:
                time.sleep(3)
        print("登录成功，更新Cookie中...")
        with open(cg.COOKIEPATH, 'w') as f:
            json.dump(browser.get_cookies(), f)
        f.close()

        self.headers['Cookie'] = strCookie(browser.get_cookies())
        browser.close()


    def _get_index(self, city, code):
        """
            每个网页的单独爬取过程
        :param city: city name, str
        :param code: city code, int
        :return:
        """
        encrypt_data, uniqid = self._get_uniqid(self.keywords, code)
        if len(encrypt_data) == 0 or uniqid is None:
            return False

        key = self._get_key(uniqid)
        if key is None:
            return False

        for data in encrypt_data:
            keyword = data['word'][0]['name']
            decrypt_data = self._decrypt_func(key, data['all']['data'])
            if keyword in self.keywords_data:
                self.keywords_data[keyword].append(decrypt_data)
            else:
                self.keywords_data[keyword] = [decrypt_data]
        return True

    def _get_uniqid(self, words, area):
        """
            访问Search网页得到密文和uniqid
        :param words:
        :param area:
        :return:
        """
        header = self.headers.copy()
        header['Cipher-Text'] = cg.CIPHERTEXT

        response = requests.get(url=cg.SEARCH_URL, headers=header, params=getHeaderparams(area, words, self.days))

        try:
            if response.status_code != 200:
                raise requests.Timeout
            else:
                response = response.json()
                assert response['status'] == 0
            return (response['data']['userIndexes'], response['data']['uniqid'])

        except Exception as e:
            print('Response Get Failed.\nError from _get_uniqid:", ', Exception, e)
            return [], None


    def _get_key(self, uniqid):
        """
            访问ptbk网页得到密钥key
        :param uniqid:
        :return:
        """
        response = requests.get(url=cg.PTBK_URL_PREFIX + uniqid, headers=self.headers)
        try:
            if response.status_code != 200:
                raise requests.Timeout
            else:
                response = response.json()
                assert response['status'] == 0
            return response['data']

        except Exception as e:
            print('ptbk Response Get Failed\nError from _get_key:", ', Exception, e)
            return None

    def _decrypt_func(self, key, data):
        """
        decrypt data using key
        """

        n = len(key) // 2
        a = dict(zip(key[:n], key[n:]))
        index = ''.join(a[d] for d in data)
        index = [int(i) if i else 0 for i in index.split(',')]
        return index

    def _save_excel(self):
        with pd.ExcelWriter("result.xlsx", engine='xlsxwriter') as writer:
            for word, index in self.keywords_data.items():
                df = pd.DataFrame(index, index=self.cities.keys())
                df.to_excel(writer, sheet_name=word)

    def _save_json(self):
        cities = self.cities.keys()
        f = open("result.json", 'w')
        for word, indexes in self.keywords_data.items():
            for city, index in zip(cities, indexes):
                for date, i in zip(range(self.days), index):
                    cur_data = {
                        'key_word': word,
                        'city': city,
                        'date': date,
                        'index': i
                    }
                    f.write(json.dumps(cur_data, ensure_ascii=False))
                    f.write("\n")
        f.close()
        '''
        with open("result.json", 'w') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        f.close()
        '''









