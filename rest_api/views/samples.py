from .common import *

class RestListSamples(generics.ListAPIView):
    """
    Retrieve all the Samples
    Endpoint: /api/sample/all
    """
    serializer_class = SampleSerializer
    queryset = Sample.objects.all().prefetch_related('cohorts').order_by('id')


class RestSampleSearch(generics.ListAPIView):
    """
    Search the Sample(s) using parameters as query
    Endpoint: /api/sample/search
    """
    serializer_class = SampleSerializer

    def get_queryset(self):
        queryset = Sample.objects.all().prefetch_related('cohorts').order_by('id')

        params = 0
        # Cohort
        cohort = normalize_query_param(self.request,'cohort')
        if cohort and cohort is not None:
            queryset = queryset.filter(Q(cohorts__name_short__iexact=cohort) | Q(cohorts__name_full__iexact=cohort))
            params += 1

        if params == 0:
            queryset = []
        return queryset