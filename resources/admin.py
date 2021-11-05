from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import reverse, path
from django.http import HttpResponseRedirect

from .models import *

class ResourceAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('lorem/', self.admin_site.admin_view(self.test_view))
        ]
        return my_urls + urls

    def test_view(self, request):
        context = dict(
           self.admin_site.each_context(request),
        )
        return TemplateResponse(request, "resources/lorem.html", context)

class EventAdmin(admin.ModelAdmin):
    def response_change(self, request, obj):
        """ if user clicked edit link in calendar, return back to calendar view """
        response = super(EventAdmin, self).response_change(request, obj)

        print ("response_change")
        if (isinstance(response, HttpResponseRedirect) and
#                response['location'] == '../' and
                request.GET.get('source') == 'calendar'):
            
            role = request.GET.get('role')
            response['location'] = reverse('calendar', args=(role,))

        return response

admin.site.register(Role)
admin.site.register(Resource, ResourceAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Project)
