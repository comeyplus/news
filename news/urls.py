# -*- coding: utf-8 -*-
from django.conf.urls import url
import news.views

urlpatterns = [
    url(r'^$', news.views.news_home, name='news_home'),
    url(r'^about/$', news.views.about, name='about'),
    url(r'^(?P<source>\w+)/$', news.views.NewsList.as_view(), name='story_list'),
    url(r'^detail/(?P<story_id>\d+)/$', news.views.StoryDetail.as_view(), name="story_detail"),
    url(r'^convertlist/(?P<source>\w+)/$', news.views.ConvertList.as_view(), name='convert_list'),
    url(r'^convertdetail/(?P<source>\w+)/(?P<id>\d+)/$', news.views.ConvertDetail.as_view(), name='convert_detail'),
    
]

