from django.views.generic import *
from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models.functions import Trunc, Lag
from django.db.models import DateTimeField, ExpressionWrapper, fields, Window, F, Q
from resources.models import *
from datetime import timedelta


class Timetable(TemplateView):
    template_name = 'resources/timetable.html'

    def view_event(self, event, exclude):
        flatten = lambda l: [item for sublist in l for item in sublist]

        related = flatten([d.descendants() for d in event.dependencies.exclude(id__in=exclude)])
        roles = set(r.role for r in related)

        dependencies = [{
            'role' : role.label,
            'resources' : [r for r in related if r.role.id == role.id],
        } for role in sorted(roles, key=lambda x: x.weight)]

        return {
            'start' : event.start,
            'end' : event.end,
            'label' : event.label,
            'dependencies' : dependencies,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # global flag: whether to display events with is_global==true
        show_globals = bool(int(self.request.GET.get('show_globals', 1)))
        from_date = self.request.GET.get('start', None)
        to_date = self.request.GET.get('end', None)

        # case 1: single resource
        if ('resource' in self.kwargs):
            resources = [ get_object_or_404(Resource, pk=self.kwargs['resource']) ]

        # case 2: all resources for specific role
        elif ('role' in self.kwargs):
            role = get_object_or_404(Role, pk=self.kwargs['role']);
            resources = list( Resource.objects.filter(role=role) )

        else:
            # TODO throw 404
            resources = []


        context['timetables'] = []

        for resource in resources:
            related_resources = resource.ancestors()
            descendants = resource.descendants()

            events = self.get_events(
                related_resources, 
                show_globals=show_globals, 
                from_date=from_date, 
                to_date=to_date)
            dates = set( map( lambda x: x.start.date(), events ))

            events_by_day = []
            for date in sorted(dates):
                events_by_day.append({
                    'date' : date,
                    'events' : [self.view_event(event, exclude=[r.id for r in descendants]) for event in events if event.start.date()==date]
                })

            timetable = {
                'resource' : resource,
                'descendants' : descendants,
                'events_by_day' : events_by_day,
            }

            context['timetables'].append(timetable)

        return context


    def get_events(self, resources, show_globals, from_date, to_date):
        query = Event.objects
        if show_globals:
            query = query.filter(
                Q(is_global=True) | Q(dependencies__in=resources)
            )
        else:
            query = query.filter(dependencies__in=resources)
        if (from_date): query = query.filter(end__gt=from_date)
        if (to_date):   query = query.filter(start__lt=to_date)
        
        return list( query.order_by('start') )
