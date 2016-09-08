# -*- coding: utf-8 -*-

from django.http.response import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse


def home(request):
    return HttpResponseRedirect(reverse('news:news_home'))
