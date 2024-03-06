from django.views.generic import ListView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import F

from resources.models import Resource, Role

class ResourcesJSON(ListView):
    def get_queryset(self):
        query = Resource.objects
        if ('role' in self.kwargs):
            self.role = get_object_or_404(Role, pk=self.kwargs['role'])
            query = query.filter(role=self.role)
        return query.values('id', title=F('label'))

    def get(self, request, *args, **kwargs):
        data = list(self.get_queryset().values())
        return JsonResponse(data, safe=False)
