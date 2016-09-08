from django.contrib import admin
from news.models import DailyDate, Story, Section

# Register your models here.
admin.site.register(Story)
admin.site.register(DailyDate)
admin.site.register(Section)

