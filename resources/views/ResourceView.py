from django.views.generic import *
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from resources.models import *



class ResourceView(DetailView):
    template_name = "resources/resource.html"
    model = Resource

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editable'] = True
        resource = context['object']
        
        if(resource):
            context['parents'] = Resource.objects.filter(dependencies=resource.id)

        return context
