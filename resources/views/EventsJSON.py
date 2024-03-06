from django.views.generic import *
from django.db.models import Aggregate, CharField
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import JsonResponse

from resources.models import *

DEFAULT_ROLE = 1

def edit_url(id, role):
    if role is None:
        role = DEFAULT_ROLE

    return "%s?source=calendar&role=%s" % (
            reverse('admin:resources_event_change', args=(id,)),
            role )

def delete_url(id):
    return reverse('admin:resources_event_delete', args=(id,))


class GroupConcat(Aggregate):
    function = 'GROUP_CONCAT'
    template = '%(function)s(%(distinct)s%(expressions)s%(ordering)s%(separator)s)'

    def __init__(self, expression, distinct=False, ordering=None, separator=',', **extra):
        super(GroupConcat, self).__init__(
            expression,
            distinct='DISTINCT ' if distinct else '',
            ordering=' ORDER BY %s' % ordering if ordering is not None else '',
            separator=',"%s"' % separator,
            output_field=CharField(),
            **extra
        )

"""
List of Events (fullcalendar JSON interface)
"""
class EventsJSON(ListView):
    context_object_name = 'events'

    def get_queryset(self):
        # self.resource = get_object_or_404(Resource, pk=self.kwargs['resource'])
        # related_resources = self.resource.ancestors();
        query = Event.objects

        if ('start' in self.kwargs):
            query = query.filter(end__gt=self.kwargs['start'])

        if ('end' in self.kwargs):
            query = query.filter(start__lt=self.kwargs['end'])

        return query.order_by('start') \
            .annotate(dependencies_ids=GroupConcat('dependencies', separator=','))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # resource = get_object_or_404(Resource, pk=self.kwargs['resource'])
        # context['resource'] = resource
        return context

    def get(self, request, *args, **kwargs):
        if ('role' in kwargs):
            primary_role = get_object_or_404(Role, pk=kwargs['role'])
            primary_resources = [r.id for r in Resource.objects.filter(role=primary_role.id)]
        else:
            primary_role = Role()
            primary_resources = []
        resource_labels = { r.id : r.label for r in Resource.objects.all() }
        label_fn = lambda res : resource_labels[res.id] # TODO fail-safe

        json = []
        for event in self.get_queryset():

            cal_event = {
                'id' : event.id,
                'start' : event.start,
                'end' : event.end,
            }

            dependencies = []
            if event.is_global:
                dependencies = primary_resources
                cal_event['color'] = '#472'
            elif event.dependencies_ids:
                dependencies = list(map(int, str(event.dependencies_ids).split(',')))

            cal_event['resourceIds'] = dependencies

            conflicts = event.find_conflicts()
            if conflicts:
                cal_event['color'] = '#f22'
                cal_event['conflicts'] = '\n'.join(map(label_fn, conflicts))

            if event.label:
                cal_event['title'] = event.label
            else:
                secondary_resources = filter(lambda id: id not in primary_resources, dependencies)
                cal_event['title'] = ', '.join(map(lambda id: resource_labels[id], secondary_resources))

            cal_event['edit_url'] = edit_url(event.id, primary_role.id)
            cal_event['delete_url'] = delete_url(event.id)

            json.append(cal_event)

        return JsonResponse(json, safe=False)
