# -*- coding: utf-8 -*-
from django.conf.urls import url
import news.views

urlpatterns = [
    url(r'^$', news.views.news_home, name='news_home'),
    url(r'^(?P<source>\w+)/$', news.views.news_list, name='story_list'),
    url(r'^detail/(?P<story_id>\d+)/$', news.views.story_detail, name="story_detail"),
    url(r'^convertlist/(?P<source>\w+)/$', news.views.convert_list, name='convert_list'),
    url(r'^convertdetail/(?P<source>\w+)/(?P<id>\d+)/$', news.views.convert_detail, name='convert_detail'),
    url(r'^about/$', news.views.about, name='about'),
]

