from django.views.generic import *
from django.http import JsonResponse
from resources.models import *

# RESOURCE_ID EVENT_ID_1 EVENT_ID_2 OVERLAP_START OVERLAP_END

def find_conflicts():
    conflicts = []

    for resource in Resource.objects.all():
        related_resources = resource.ancestors()
        events = list( Event.objects.filter(dependencies__in=related_resources).order_by('start') )

        previous_event = None
        for event in events:
            if (previous_event):
                gap = event.start - previous_event.end
                
                if (gap < timedelta(0)):
                    conflicts.append({
                        'resource' : resource,
                        'first_event' : previous_event,
                        'second_event' : event,
                    })

            previous_event = event

    return conflicts


# TODO unused
class ConflictList(TemplateView):
    template_name = 'resources/conflict_list.html'

    def get_context_data(self, **kwargs):
        # gap = ExpressionWrapper(
        #     F('start') - Window(Lag(F('end'), default='start', order_by='start')), output_field=fields.DurationField() )

        context = super().get_context_data(**kwargs)
        context['conflicts'] = find_conflicts()

        return context

# TODO unused
class ConflictsJSON(View):
    def get(self, request, *args, **kwargs):
        conflicts = map(lambda c: {
            'resource': c['resource'].id,
            'first_event': c['first_event'].id,
            'second_event': c['second_event'].id}, find_conflicts() )
        return JsonResponse(list(conflicts), safe=False)
