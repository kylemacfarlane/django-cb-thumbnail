from django.conf.urls.defaults import *
from django.contrib import admin
from cuddlybuddly import thumbnail


admin.autodiscover()
thumbnail.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
)
