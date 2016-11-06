from django.conf.urls import patterns, include, url
from services.api import all_views as services_views
from services.api import AccessibilityRuleView
from observations.api import views as observations_views
from rest_framework import routers
from munigeo.api import all_views as munigeo_views

# from django.contrib import admin
# admin.autodiscover()

router = routers.DefaultRouter()

registered_api_views = set()

for view in services_views + munigeo_views + observations_views:
    kwargs = {}
    if view['name'] in registered_api_views:
        continue
    else:
        registered_api_views.add(view['name'])

    if 'base_name' in view:
        kwargs['base_name'] = view['base_name']
    router.register(view['name'], view['class'], **kwargs)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'smbackend.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # url(r'^', include(v1_api.urls)),
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^open311/', 'services.views.post_service_request', name='services'),
    url(r'^v1/', include(router.urls))
)
