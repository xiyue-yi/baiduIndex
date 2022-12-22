import config as cg
import json

def getCitycode(cities):
    cityCode = {}
    for city in cities:
        cityCode.update({city: cg.CITY_CODES[city]})
    return cityCode

def strCookie(cookie):
    return '; '.join([item['name'] + '=' + item['value'] for item in cookie])

def getHeaderparams(area, words, days=30):
    params = {
        'area': str(area),
        'word': json.dumps([[{"name": word, "wordType": 1}] for word in words]),
        'days': str(days)
    }
    return params
