from .common import *

class RestListCohorts(generics.ListAPIView):
    """
    Retrieve all the Cohorts
    Endpoint: /api/cohort/all
    """
    serializer_class = CohortSerializerExtended

    def get_queryset(self):
        return Cohort.objects.all().prefetch_related('cohorts_sample').order_by('name_short')

class RestCohort(generics.RetrieveAPIView):
    """
    Retrieve a Cohort
    Endpoint: /api/cohort/<cohort>
    """
    def get(self, request, cohort):
        try:
            queryset = Cohort.objects.prefetch_related('cohorts_sample').get(Q(name_short__iexact=cohort) | Q(name_full__iexact=cohort) | Q(name_others__iexact=cohort))
        except Cohort.DoesNotExist:
            queryset = None
        serializer = CohortSerializerExtended(queryset,many=False)
        return Response(serializer.data)
