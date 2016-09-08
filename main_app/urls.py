# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib import admin
from .views import home

urlpatterns = [
    url('^$', home),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^news/', include('news.urls', namespace='news')),
]
