from django.views.generic import *
from django.http import HttpResponse
from resources.models import *



class ResourceDependenciesView(DetailView):
    model = Resource
    http_method_names = ["get", "post", "delete"]

    def get(self, request, *args, **kwargs):
        return HttpResponse()

    def post(self, request, *args, **kwargs):
        # add dependency
        return HttpResponse()

    def delete(self, request, *args, **kwargs):
        parent = super().get_object()
        child = kwargs['dependency']
        parent.removeDependency(child)
        return HttpResponse()
