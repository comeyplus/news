# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from bs4 import BeautifulSoup

from django.shortcuts import render_to_response
from django.http.response import HttpResponse, HttpResponseRedirect
from django.views.decorators.gzip import gzip_page
from django.core.urlresolvers import reverse

from news.models import Story, DailyDate
from news.fetcher import CBFetcher, PageNotFoundError


def picture_display(request):
    image_show = request.GET.get("image", None)
    if image_show:
        request.session['image'] = image_show
    else:
        image_show = request.session.get('image', 'hide')
    if image_show == 'show':
        return True
    else:
        return False


def news_home(request):
    return HttpResponseRedirect(reverse('news:story_list', kwargs={'source': 'zhihudaily'}))


@gzip_page
def news_list(request, source):
    date_str = request.GET.get("date", None)
    if date_str:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        date = datetime.datetime.now().date()

    date_str = date.strftime('%Y-%m-%d')
    dailydate = DailyDate.objects.update_daily_date_with_date(
        date, source=source)
    story_qs = dailydate.get_daily_stories()
    last_date = date - datetime.timedelta(days=1)
    last_date_str = last_date.strftime('%Y-%m-%d')
    next_date = date + datetime.timedelta(days=1)
    next_date_str = next_date.strftime('%Y-%m-%d')
    if date == datetime.datetime.now().date():
        next_date_str = ''
    context = {}
    context['date_str'] = date_str
    context['story_qs'] = story_qs
    context['last_date_str'] = last_date_str
    context['next_date_str'] = next_date_str
    context['nav_item'] = 'zhihu'
    return render_to_response('newslist.html', context)


@gzip_page
def story_detail(request, story_id):
    story = Story.objects.get(story_id=story_id)
    story.update()

    image_show = picture_display(request)
    if not image_show:
        story.body = hide_media(story.body)
    return render_to_response('story_detail.html', {'story': story, 'nav_item': 'zhihu'})


@gzip_page
def convert_list(request, source):
    page_number = int(request.GET.get('page', 1))
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
        return render_to_response('convert_list.html', context)
    else:
        return HttpResponse('wrong source name')


@gzip_page
def convert_detail(request, source, id):

    try:
        result = CBFetcher().get_story_detail(id, update_comment=True)
    except PageNotFoundError:
        return HttpResponse('page not found')
    soup = BeautifulSoup()
    body = str(result['body'])
    image_show = picture_display(request)
    if not image_show:
        body = hide_media(body)


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
    return render_to_response('convert_detail.html', context)


@gzip_page
def about(request):
    return render_to_response('about.html', {'nav_item': 'about'})


def hide_media(raw_html):
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

