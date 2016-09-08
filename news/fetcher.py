# -*- coding: utf-8 -*-

import datetime
import math
import requests

from requests.exceptions import HTTPError

from bs4 import BeautifulSoup


class FetchError(Exception):

    def __init__(self, errtype=''):
        self.errtype = errtype

    def __str__(self, *args, **kwargs):
        return self.__class__.__name__ + ':' + self.errtype


class PageNotFoundError(FetchError):
    pass


class NewsFetcher():
    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;",
               "Accept-Encoding": "gzip",
               "Accept-Language": "zh-CN,zh;q=0.8",
               "Referer": "http://www.example.com/",
               "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
               }

    def fetch_json(self, url, method='get'):
        r = requests.request(
            method=method,
            url=url,
            headers=self.headers
        )
        try:

            r.raise_for_status()
            if r.encoding.lower() == 'iso-8859-1':
                r.encoding = 'utf-8'
            json = r.json()
        except HTTPError as e:
            raise FetchError('invalid_url')
        return json

    def fetch_html(self, url, method='get'):
        r = requests.request(
            method=method,
            url=url,
            headers=self.headers
        )
        try:
            r.raise_for_status()
            if r.encoding.lower() == 'iso-8859-1':
                r.encoding = 'utf-8'
            html = r.text
        except HTTPError as e:
            raise FetchError('invalid_url')
        return html


class ZhihuDailyFetcher(NewsFetcher):

    def get_latest_news(self):
        response_json = self.fetch_json(
            'http://news-at.zhihu.com/api/4/news/latest')
        return response_json

    def get_before_news(self, date_str):
        response_json = self.fetch_json(
            'http://news.at.zhihu.com/api/4/news/before/' + date_str)
        return response_json

    def get_story_detail(self, story_id):
        response_json = self.fetch_json(
            'http://news-at.zhihu.com/api/4/news/' + str(story_id))
        return response_json


class CBFetcher(NewsFetcher):

    def get_news_list(self, page_number=1):
        url = 'http://m.cnbeta.com/list_latest_' + str(page_number) + '.htm'
        html = self.fetch_html(url)

        soup = BeautifulSoup(html, "html.parser")
        news_list = []
        ul = soup.html.body.find('ul')
        if not ul:
            raise FetchError('parse_error')
        for li in ul.find_all('li'):
            a = li.div.a
            news_id = int(a.attrs['href'].split('.')[0].split('/')[2])
            news_list.append((news_id, a.text))
        if news_list:
            first_id = news_list[0][0]
            last_id = news_list[-1][0]
            return {'news_list': news_list, 'first_id': first_id, 'last_id': last_id}
        else:
            raise FetchError('parse_error')

    def get_story_comment(self, story_id):
        url = 'http://m.cnbeta.com/comments_' + str(story_id) + '.htm'
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        J_commt_list = soup.html.body.find('ul', id="J_commt_list")
        if not J_commt_list:
            return [], 0, 0
        comments = str(J_commt_list)
        comment_count_list = soup.html.body.find(
            'span', class_="morComment").find_all('b')
        comment_count_all = int(comment_count_list[0].string)
        comment_count_show = int(comment_count_list[1].string)
        return comments, comment_count_all, comment_count_show

    def get_story_detail(self, story_id, update_comment=True):
        url = 'http://www.cnbeta.com/articles/' + str(story_id) + '.htm'
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        introduction = soup.html.body.find('div', class_="introduction")
        if not introduction:
            raise PageNotFoundError()
        theme = introduction.find('img')
        theme_id = introduction.find('a')['href'].split('/')[2].split('.')[0]
        theme_text = theme['title']
        theme_img = theme['src']
        summary = introduction.p
        title = soup.html.body.find('h2', id="news_title").string
        title_bar = soup.html.body.find('div', class_="title_bar")
        time = datetime.datetime.strptime(
            title_bar.find('span', class_="date").string, "%Y-%m-%d %H:%M:%S")
        where = title_bar.find('span', class_="where").string
        body = soup.html.body.find('div', class_="content")
        author = soup.html.body.find('span', class_="author")
        # TODO not update if none comment
        if update_comment:
            comments, comment_count_all, comment_count_show = self.get_story_comment(
                story_id)
        else:
            comments, comment_count_all, comment_count_show = '', 0, 0
        result = {'body': str(body),
                  'share_url': url,
                  'image': str(theme_img),
                  'section': {'thumbnail': str(theme_img),
                              'id': str(theme_id),
                              'name': str(theme_text),
                              },
                  'title': str(title),
                  'id': story_id,

                  'author': str(author),
                  'summary': (summary),
                  'time': time,
                  'where': str(where),
                  'comments': comments,
                  'comment_count_all': comment_count_all,
                  'comment_count_show': comment_count_show,
                  }
        return result

    def get_before_news(self, date_str, ratio=3):

        # TODO today and is_fetched and the latest on fetched today
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        page_number = 1
        a_page = self.get_news_list(page_number)
        b_page = self.get_news_list(page_number * ratio)
        top_id = int(a_page['news_list'][0][0])
        bottom_id = int(b_page['news_list'][-1][0])
        top_time = self.get_story_detail(top_id, update_comment=False)['time']
        bottom_time = self.get_story_detail(
            bottom_id, update_comment=False)['time']
        print(top_time)
        print(bottom_time)
        while bottom_time.date() > date:
            page_number *= ratio
            a_page = b_page
            top_id = int(a_page['news_list'][0][0])
            top_time = self.get_story_detail(
                top_id, update_comment=False)['time']
            try:
                b_page = self.get_news_list(page_number * ratio)
            except FetchError:
                break

            bottom_id = int(b_page['news_list'][-1][0])
            bottom_time = self.get_story_detail(
                bottom_id, update_comment=False)['time']
            print(top_time)
            print(bottom_time)
        print('finish')
        a_number = page_number
        b_number = page_number * ratio
        while b_number - a_number > 1:
            print(str(a_number) + ' ' + str(b_number))
            mid_number = int(math.ceil((a_number + b_number) / 2))
            try:
                mid_page = self.get_news_list(mid_number)
            except FetchError:
                b_number = mid_number
                continue
            mid_page_top_id = int(mid_page['news_list'][0][0])
            mid_page_top_time = self.get_story_detail(
                mid_page_top_id, update_comment=False)['time']
            if mid_page_top_time.date() > date:
                a_number = mid_number
            else:
                b_number = mid_number
        while True:
            news_list = self.get_news_list(a_number)['news_list']
            for news in news_list:
                news_id = int(news[0])
                news_dict = self.get_story_detail(news_id, False)
                print(news_dict['title'])

            a_number += 1
