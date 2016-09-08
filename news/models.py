# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import datetime
import json

from django.db import models

from news.fetcher import ZhihuDailyFetcher, CBFetcher


class SectionManager(models.Manager):

    def update_with_section_dict(self, section_dict, source):
        section_id = section_dict['id']
        section_qs = self.filter(section_id=section_id)
        if section_qs:
            section = section_qs[0]
        else:
            section = self.create(thumbnail=section_dict['thumbnail'],
                                  section_id=section_dict['id'],
                                  name=section_dict['name'],
                                  source=source,
                                  )
        return section


class Section(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=20)
    section_id = models.IntegerField()
    thumbnail = models.CharField(max_length=100, blank=True, null=True)

    objects = SectionManager()


class DailyDateManager(models.Manager):

    def update_daily_date_with_date(self, date, source):
        daily_date_qs = self.filter(date=date, source=source)
        if daily_date_qs:
            daily_date = daily_date_qs[0]
        else:
            daily_date = self.create(date=date, source=source)
        return daily_date


class DailyDate(models.Model):
    date = models.DateField()
    is_blank = models.BooleanField(default=True)
    is_finished = models.BooleanField(default=False)
    resend_request = models.IntegerField(default=0)
    source = models.CharField(max_length=20)

    objects = DailyDateManager()

    zdf = ZhihuDailyFetcher()
    cbf = CBFetcher()

    @property
    def is_valid(self):
        if self.resend_request > 1:
            return False
        else:
            return True

    def _fetch_and_create_story_zhihu(self):

        if self.date == datetime.datetime.now().date():
            response_json = self.zdf.get_latest_news()
            self.is_finished = False
        else:
            next_day = self.date + datetime.timedelta(days=1)
            response_json = self.zdf.get_before_news(next_day.strftime('%Y%m%d'))
            self.is_finished = True

        if response_json:
            self.is_blank = False
            stories = response_json['stories']
            date_str = response_json['date']
            for story in stories:
                Story.objects.update_with_story_dict(
                    story, date_str, self.source)
        else:
            self.is_blank = True
            self.resend_request += 1
        self.save()

    def _fetch_and_create_story_cb(self):

        if self.date == datetime.datetime.now().date():
            response_json = self.cbf.get_latest_news()
            self.is_finished = False
        else:
            next_day = self.date + datetime.timedelta(days=1)

            response_json = self.zdf.get_before_news(next_day.strftime('%Y%m%d'))
            self.is_finished = True

        if response_json:
            self.is_blank = False
            stories = response_json['stories']
            date_str = response_json['date']
            for story in stories:
                Story.objects.update_with_story_dict(
                    story, date_str, self.source)
        else:
            self.is_blank = True
            self.resend_request += 1
        self.save()

    def _fetch(self):

        if self.date > datetime.datetime.now().date():
            return self
        if self.is_finished:
            return self
        if not self.is_valid:
            return self
        else:
            if self.source == 'zhihudaily':
                self._fetch_and_create_story_zhihu()
            elif self.source == 'cnbeta':
                self._fetch_and_create_story_cb()
            else:
                pass
            return self

    def get_daily_stories(self):
        self._fetch()
        story_qs = Story.objects.filter(date=self.date, source=self.source)
        return story_qs


class StoryManager(models.Manager):

    def update_with_story_dict(self, story_dict, date_str, source):
        story_id = story_dict['id']
        story_qs = self.filter(story_id=story_id)
        date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
        DailyDate.objects.update_daily_date_with_date(date, source)

        if not story_qs:
            story = self.create(source=source, date=date, story_id=story_id)
            story.init_with_news_dict(story_dict)

        else:
            story = story_qs[0]
        return story


class Story(models.Model):
    title = models.CharField(max_length=100, blank=True, null=True)
    image_source = models.CharField(max_length=100, blank=True, null=True)
    image = models.CharField(max_length=100, blank=True, null=True)
    share_url = models.CharField(max_length=100, blank=True, null=True)
    ga_prefix = models.CharField(max_length=36, blank=True, null=True)

    date = models.DateField()

    datetime = models.DateTimeField(blank=True, null=True)  # 还没用

    type = models.IntegerField(default=0)
    story_id = models.IntegerField()

    section = models.ForeignKey(Section, blank=True, null=True)

    cover_images = models.TextField(blank=True, null=True)
    js = models.TextField(blank=True, null=True)
    css = models.TextField(blank=True, null=True)
    recommenders = models.TextField(blank=True, null=True)

    body = models.TextField(blank=True, null=True)

    source = models.CharField(max_length=20)

    objects = StoryManager()

    zdf = ZhihuDailyFetcher()

    def __str__(self):
        return self.title or 'unnamed'

    @property
    def body_with_pic(self):
        # TODO:修改成正则的
        body = self.body.replace("\r\n", '')
        body_list = body.split('<img ')
        new_body_list = []
        count = 0

        for i in body_list:
            if count == 0:
                new_body_list.append(body_list[count])
            else:
                left = body_list[count].split('src="', 1)[1]
                line = left.split('>', 1)
                pic_url = line[0].split('"', 1)[0]
                new_body_list.append(
                    '<div id="hotlinking"><script type="text/javascript">showImg("' + pic_url + '");</script></div>')
                new_body_list.append(line[1])
                print(pic_url)
            count += 1
        body2 = ''.join(new_body_list)
        return body2

    @property
    def cover_picture_first(self):
        if self.cover_images:
            cover_images = json.loads(self.cover_images)
            if cover_images:
                return cover_images[0]
        return ''

    def is_updated(self):
        return bool(self.share_url)

    def _init_with_news_dict_zhihu(self, story_dict):
        self.title = story_dict['title']
        self.ga_prefix = story_dict['ga_prefix']
        self.type = story_dict['type']
        self.cover_images = json.dumps(story_dict['images'])
        self.save()

    def init_with_news_dict(self, story_dict):
        if self.source == 'zhihudaily':
            self._init_with_news_dict_zhihu(story_dict)

    def update_with_news_dict(self, news_dict):
        section_dict = news_dict.get('section')
        if section_dict:
            section = Section.objects.update_with_section_dict(
                section_dict, source=self.source)
        else:
            section = None
        self.image_source = news_dict['image_source']
        self.image = news_dict['image']
        self.share_url = news_dict['share_url']

        self.section = section

        self.js = json.dumps(news_dict['js'])
        self.css = json.dumps(news_dict['css'])
        self.recommenders = json.dumps(news_dict.get('recommenders'))

        self.body = news_dict['body']
        self.save()

    def update(self):
        if not self.is_updated():
            news_dict = self.zdf.get_story_detail(self.story_id)
            self.update_with_news_dict(news_dict)
        return self
