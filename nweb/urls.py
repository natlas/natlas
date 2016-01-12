from django.conf.urls import patterns, include, url
from django.contrib import admin

from scan_manager import views as sm

urlpatterns = (
    url(r'^$', sm.search),
    url(r'getwork$', sm.getwork),
    url(r'submit$' , sm.submit),
    #url(r'^admin/', include(admin.site.urls)),
)
