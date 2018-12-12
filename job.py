# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'Yang'
__mtime__ = '2018/11/30'
# code is far away from bugs with the god animal protecting
    I love animals. They taste delicious.
              ┏┓      ┏┓
            ┏┛┻━━━┛┻┓
            ┃      ☃      ┃
            ┃  ┳┛  ┗┳  ┃
            ┃      ┻      ┃
            ┗━┓      ┏━┛
                ┃      ┗━━━┓
                ┃  神兽保佑    ┣┓
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""
import re
import requests
from bs4 import BeautifulSoup
import time
import urllib.request
import pymysql

url = 'https://book.douban.com/tag/%E7%BC%96%E7%A8%8B?start={0}&type=T'


def provide_url():
    # 以http的get方式请求豆瓣页面（豆瓣的分类标签页面）
    responds = requests.get("https://book.douban.com/tag/?icn=index-nav")
    # html为获得响应的页面内容
    html = responds.text
    # 解析页面
    soup = BeautifulSoup(html, "lxml")
    # 选取页面中的需要的a标签，从而提取出其中的所有链接
    book_table = soup.select("#content > div > .article > div > div > .tagCol > tbody > tr > td > a")
    # 新建一个列表来存放爬取到的所有链接
    book_url_list = []
    for book in book_table:
        book_url_list.append(str(book.string))
    return book_url_list


def get_soup(url):
    page = requests.get(url.format(0)).text.replace('\n', '')
    page = BeautifulSoup(page, 'lxml')
    return page


def parse_html(soup, book_type, db, cursor):
    book_name = soup.select('.subject-list > .subject-item > .info > h2 > a')
    book_info = soup.select('.subject-list > .subject-item > .info > .pub')
    book_image = soup.select('.subject-list > .subject-item > .pic > a > img')
    book_url = soup.select('.subject-list > .subject-item > .pic > a')

    for i in range(len(book_name)):
        insert_into_mysql = []
        insert_into_mysql.append(book_url[i].get('href'))
        insert_into_mysql.append(book_name[i].text)
        insert_into_mysql.append(book_type)

        book_info_list = book_info[i].text.split('/')
        if len(book_info_list) == 5:
            insert_into_mysql.append(book_info_list[0])
            insert_into_mysql.append(book_info_list[2])
            insert_into_mysql.append(book_info_list[4])
        elif len(book_info_list) == 4:
            insert_into_mysql.append(book_info_list[0])
            insert_into_mysql.append(book_info_list[1])
            insert_into_mysql.append(book_info_list[3])
        else:
            continue

        try:
            print(insert_into_mysql[0], insert_into_mysql[1])
        except Exception:
            print('Error page Exception')
            continue

        try:
            image_url = book_image[i].get('src')
            time_samp = '%s.jpg' % (int(round(time.time() * 1000)))
            insert_into_mysql.append(time_samp)
            urllib.request.urlretrieve(image_url, 'image/' + time_samp)
        except Exception:
            print('Error image not found')
            continue

        time.sleep(1)
        so = get_soup(book_url[i].get('href'))
        try:
            try:
                insert_into_mysql.append(so.select('.related_info > .indent > div > .intro')[0].text)
            except IndexError:
                insert_into_mysql.append(so.select('.related_info > .indent > span > .intro')[0].text)
        except Exception:
            with open('error_page.txt') as f:
                f.write(insert_into_mysql[1])
            continue

        sql = ''
        insert_into_mysql = [i.strip().replace('\'', '’') for i in insert_into_mysql]
        insert_into_mysql[1] = insert_into_mysql[1].replace(' ', '')

        try:
            insert_into_mysql[5] = insert_into_mysql[5][0:insert_into_mysql[5].index('.') + 3]
        except ValueError:
            print('Error', insert_into_mysql[5])

        if len(insert_into_mysql) != 8:
            continue

        try:
            sql = "insert into douban_book_info values(null,'{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}')" \
                .format(insert_into_mysql[0], insert_into_mysql[1], insert_into_mysql[2], insert_into_mysql[3],
                        insert_into_mysql[4], insert_into_mysql[5], insert_into_mysql[6], insert_into_mysql[7])
            cursor.execute(sql)
        except Exception:
            print('Sql Exception', sql)
    db.commit()
    db.close()


if __name__ == '__main__':
    book_type_list = provide_url()
    for book_type in book_type_list:
        print('类别：', book_type)
        url = 'https://book.douban.com/tag/' + book_type + '?start={0}&type=T'
        for i in range(0, 40, 20):
            db = pymysql.connect(host='localhost', port=3306, user='root', passwd='root', db='pc')
            cursor = db.cursor()
            soup = get_soup(url.format(i))
            print(url.format(i))
            parse_html(soup, book_type, db, cursor)
            time.sleep(2)
