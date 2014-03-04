from views import *
from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                        url(r'^$', index),
                        url(r'^encrypt$', encrypt),
                        url(r'^decrypt$', decrypt),
                        url(r'^sessions_clear$', sessions_clear),
                        #url(r'^.*$', error404),
    # Examples:
    # url(r'^$', 'Cimage.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # url(r'^admin/', include(admin.site.urls)),
)
