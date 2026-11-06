import re
from .common import *

class RestListPublications(generics.ListAPIView):
    """
    Retrieve the OmicsPred Publications
    Endpoint: /api/publication/all
    """
    serializer_class = PublicationExtendedSerializer

    def get_queryset(self):
        # Fetch all the Publications
        queryset = Publication.objects.defer(*defer_dict['publication_defer']).all().prefetch_related(related_dict['publication_datasets']).order_by('id')
        # Filter by list of Publications IDs
        opp_ids_list = get_ids_list(self.request)
        if opp_ids_list:
            queryset = queryset.filter(id__in=opp_ids_list)

        return queryset


class RestPublication(generics.RetrieveAPIView):
    """
    Retrieve one Publication
    Endpoint: /api/publication/<opp_id>
    """

    def get(self, request, opp_id):
        opp_id = opp_id.upper()
        try:
            if re.match(r'^\d+$',opp_id):
                queryset = Publication.objects.defer(*defer_dict['publication_defer']).prefetch_related(related_dict['publication_datasets']).get(pmid=opp_id)
            else:
                queryset = Publication.objects.defer(*defer_dict['publication_defer']).prefetch_related(related_dict['publication_datasets']).get(id=opp_id)
        except Publication.DoesNotExist:
            queryset = None
        serializer = PublicationExtendedSerializer(queryset,many=False)
        return Response(serializer.data)


class RestPublicationSearch(generics.ListAPIView):
    """
    Retrieve the Publication(s) using query
    Endpoint: /api/publication/search
    """
    serializer_class = PublicationExtendedSerializer

    def get_queryset(self):
        # queryset = Publication.objects.defer(*defer_dict['publication_defer']).all().order_by('id')
        queryset = Publication.objects.defer(*defer_dict['publication_defer']).all().prefetch_related(related_dict['publication_datasets']).order_by('id')

        params = 0

        # Search by Score ID
        opgs_id = normalize_query_param(self.request,'opgs_id')
        if opgs_id and opgs_id is not None:
            opgs_id = opgs_id.upper()
            if opgs_id.startswith(OPGS_PREFIX):
                try:
                    score = Score.objects.only('id','dataset__publication__id').select_related('dataset','dataset__publication').get(id=opgs_id)
                    queryset = queryset.filter(id=score.dataset.publication.id)
                    params += 1
                except Score.DoesNotExist:
                    queryset = []

        # Search by Author
        author = normalize_query_param(self.request,'author')
        if author and author is not None:
            queryset = queryset.filter(authors__icontains=author)
            params += 1

        # Search by Pubmed ID
        pmid = normalize_query_param(self.request,'pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(pmid=pmid)
            params += 1

        if params == 0:
            queryset = []
        return queryset
