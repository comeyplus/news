# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from bs4 import BeautifulSoup

from django.shortcuts import render_to_response
from django.http.response import HttpResponse, HttpResponseRedirect
from django.views.decorators.gzip import gzip_page
from django.core.urlresolvers import reverse
from django.views.generic.base import View, TemplateView
from django.utils.decorators import method_decorator
from django.template.context import RequestContext

from news.models import Story, DailyDate
from news.fetcher import CBFetcher, PageNotFoundError


def news_home(request):
    return HttpResponseRedirect(reverse('news:story_list', kwargs={'source': 'zhihudaily'}))


@gzip_page
def about(request):
    return render_to_response('about.html', {'nav_item': 'about'})


class NewsViewBase(TemplateView):

    @method_decorator(gzip_page)
    def get(self, request, *args, **kwargs):
        return TemplateView.get(self, request, *args, **kwargs)

    def media_display(self):
        image_show = self.request.GET.get("image", None)
        if image_show:
            self.request.session['image'] = image_show
        else:
            image_show = self.request.session.get('image', 'hide')
        if image_show == 'show':
            return True
        else:
            return False

    def get_date(self):
        date_str = self.request.GET.get("date", None)
        if date_str:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = datetime.datetime.now().date()
        date_str = date.strftime('%Y-%m-%d')
        last_date = date - datetime.timedelta(days=1)
        last_date_str = last_date.strftime('%Y-%m-%d')
        next_date = date + datetime.timedelta(days=1)
        next_date_str = next_date.strftime('%Y-%m-%d')
        if date == datetime.datetime.now().date():
            next_date_str = ''
        return date, last_date_str, date_str, next_date_str

    def hide_media(self, raw_html):
        soup = BeautifulSoup(raw_html, "html.parser")
        for img in soup.find_all('img'):
            tag = soup.new_tag("a")
            tag['href'] = img['src']
            tag.string = img.get('title', '图片')
            img.insert_before(tag)
            img.decompose()

        for embed in soup.find_all('embed'):
            tag = soup.new_tag("a")
            tag['href'] = embed['src']
            tag.string = '视频' + embed['src']
            embed.insert_before(tag)
            embed.decompose()

        for script in soup.find_all('script'):
            script.decompose()

        return str(soup)

    def get_context_data(self, request, *args, **kwargs):
        context = {}
        return context


class NewsList(NewsViewBase):
    template_name = 'newslist.html'

    def get_context_data(self, source, **kwargs):
        if not self.media_display():
            self.template_name = 'newslist_no_pic.html'

        date, last_date_str, date_str, next_date_str = self.get_date()
        dailydate = DailyDate.objects.update_daily_date_with_date(
            date, source=source)
        story_qs = dailydate.get_daily_stories()
        context = {}
        context['date_str'] = date_str
        context['story_qs'] = story_qs
        context['last_date_str'] = last_date_str
        context['next_date_str'] = next_date_str
        context['nav_item'] = 'zhihu'
        return context


class StoryDetail(NewsViewBase):
    template_name = 'story_detail.html'

    def get_context_data(self, story_id, **kwargs):
        story = Story.objects.get(story_id=story_id)
        story.update()

        if not self.media_display():
            story.body = self.hide_media(story.body)
        context = {}
        context['story'] = story
        context['nav_item'] = 'zhihu'
        return context


class ConvertList(NewsViewBase):
    template_name = 'convert_list.html'

    def get_context_data(self, source, **kwargs):
        page_number = int(self.request.GET.get('page', 1))
        if source == 'cb':
            result = CBFetcher().get_news_list(page_number)
            news_list = result['news_list']
            context = {}
            context['page_number'] = page_number
            if page_number > 1:
                context['previous_page'] = page_number - 1
            context['next_page'] = page_number + 1

            context['news_list'] = news_list
            context['nav_item'] = 'cnbeta'
            return context
        else:
            raise Exception('wrong source name')


class ConvertDetail(NewsViewBase):
    template_name = 'convert_detail.html'

    def get_context_data(self, source, id, **kwargs):
        try:
            result = CBFetcher().get_story_detail(id, update_comment=True)
        except PageNotFoundError:
            raise Exception('page not found')
        body = str(result['body'])
        if not self.media_display():
            body = self.hide_media(body)

        soup = BeautifulSoup(body, "html.parser")
        last_p = soup.find_all('p')[-2:]
        for p in last_p:
            p.decompose()
        body = str(soup)

        context = {}
        context['body'] = body
        context['share_url'] = result['share_url']
        context['section_name'] = result['section']['name']
        context['title'] = result['title']
        context['author'] = result['author']
        context['time'] = result['time']
        context['summary'] = str(result['summary'])
        context['comments'] = str(result['comments'])
        context['comment_count_all'] = result['comment_count_all']
        context['comment_count_show'] = result['comment_count_show']
        context['nav_item'] = 'cnbeta'
        return context