import requests
from lxml import etree
import redis
import time
from app.config import REDISHOST, HOT_EVENT_URL, HOT_NEWS_URL, REDISPWD, REDISDB, REDISPORT

user_agents = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60',
    'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
    'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
]
headers = {
    "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'}


class GetNews:
    def __init__(self):
        pass

    def gethtml(self):
        html = requests.get(HOT_NEWS_URL, headers=headers)
        # html.encoding="utf-8"
        html = html.text
        parseHtml = etree.HTML(html)
        return parseHtml

    def getHotevevtHtml(self):
        html = requests.get(HOT_EVENT_URL, headers=headers)
        html.encoding = "GB18030"
        html = html.text
        parseHtml = etree.HTML(html)
        return parseHtml

    def getbanner(self):
        while True:
            parseHtml = self.gethtml()
            title = parseHtml.xpath(
                "//div[contains(@class,'topnews_main')]/h2/a/text()")
            imgUrl = parseHtml.xpath(
                "//div[contains(@class,'topnews_main')]/a/img/@data-original")
            newsUrl = parseHtml.xpath(
                "//div[contains(@class,'topnews_main')]/a/@href")
            bannerdata = zip(title, imgUrl, newsUrl)
            r = redis.StrictRedis(
                host=REDISHOST, port=REDISPORT, db=REDISDB, password=REDISPWD)
            for key in r.keys("banner*"):
                r.delete(key)
            for index, (title, imgUrl, newsUrl) in enumerate(bannerdata, 1):
                r.rpush("banner" + str(index), title, imgUrl, newsUrl)
            time.sleep(60 * 60 * 12)

    def getsideimg(self):
        while True:
            parseHtml = self.gethtml()
            sidetitle = parseHtml.xpath(
                "//div[contains(@class,'topnews_img')]/a/img/@alt")
            sideImgUrl = parseHtml.xpath(
                "//div[contains(@class,'topnews_img')]/a/img/@data-original")
            sideUrl = parseHtml.xpath(
                "//div[contains(@class,'topnews_img')]/h3/a/@href")
            sideimgdata = zip(sidetitle, sideImgUrl, sideUrl)
            r = redis.StrictRedis(
                host=REDISHOST, port=REDISPORT, db=REDISDB, password=REDISPWD)
            for key in r.keys("sideimg*"):
                r.delete(key)
            for index, (sidetitle, sideImgUrl, sideUrl) in enumerate(sideimgdata, 1):
                r.rpush("sideimg" + str(index), sidetitle, sideImgUrl, sideUrl)
            time.sleep(60 * 60 * 12)

    def getHotevent(self):
        while True:
            parseHtml = self.getHotevevtHtml()
            title = parseHtml.xpath(
                "//table[contains(@class,'list-table')]/tr/td[contains(@class,'keyword')]/a[1]/text()")
            link = parseHtml.xpath(
                "//table[contains(@class,'list-table')]/tr/td[contains(@class,'keyword')]/a[1]/@href")
            if len(title) == len(link):
                Hoteventdata = zip(title, link)
                r = redis.StrictRedis(
                    host=REDISHOST, port=REDISPORT, db=REDISDB, password=REDISPWD)
                for key in r.keys("Hotevent*"):
                    r.delete(key)
                for index, (title, link) in enumerate(Hoteventdata, 1):
                    r.rpush("Hotevent" + str(index), title, link)
                time.sleep(60 * 60 * 12)
            else:
                raise Exception("数据错误")
