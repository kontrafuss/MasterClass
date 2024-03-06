from django.views.generic import *
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models.functions import Trunc, Lag
from django.db.models import DateTimeField, ExpressionWrapper, fields, Window, F, Q
from resources.models import *
from datetime import timedelta



class CalendarView(ListView):
    template_name = 'resources/calendar.html'
    model = Resource
    context_object_name = 'resources'

    def get_queryset(self):
        primary_role = get_object_or_404(Role, pk=self.kwargs['role'])
        return Resource.objects.order_by('role').exclude(role=primary_role.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['primary_role'] = get_object_or_404(Role, pk=self.kwargs['role'])
        context['roles'] = Role.objects.all()
        context['project'] = Project.objects.get(pk=1)
        return context

    def post(self, request, *args, **kwargs):
        if (('id' in request.POST) and request.POST['id']):
            event = get_object_or_404(Event, pk=request.POST['id'])

            if ('start' in request.POST):
                event.start = request.POST['start']
            if ('end' in request.POST):
                event.end = request.POST['end']
        else:
            event = Event.objects.create(start=request.POST['start'], end=request.POST['end'])

        if ('is_global' in request.POST):
            event.is_global = request.POST['is_global']

        if ('removeResource' in request.POST):
            id = request.POST['removeResource']
            event.dependencies.remove(id)

        if ('resourceIds' in request.POST):
            dependencies = map(int, request.POST['resourceIds'].split(','))
            for id in dependencies: event.dependencies.add(id)

        # TODO allow changing primary resource

        event.save()
        return HttpResponse()
