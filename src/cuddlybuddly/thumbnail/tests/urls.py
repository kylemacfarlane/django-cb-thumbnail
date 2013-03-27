from django.conf.urls import include, patterns
from django.contrib import admin
from cuddlybuddly import thumbnail


admin.autodiscover()
thumbnail.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
)
