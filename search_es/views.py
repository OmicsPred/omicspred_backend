from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.serializers import ValidationError
from elasticsearch_dsl import Search


# No need to redeclare "custom_exception_handler" as it is already used in rest_api.views

def query_fields():
    return ['id^3','name^2','platform_name','omics_type','category','full_name',
            'genes.id','genes.name','proteins.id','proteins.names','metabolites.id','metabolites.name']


def get_search(query):
    s = Search(index="*").extra(size=20).query("multi_match", query=query, fields=query_fields())
    response = s.execute()

    data = []
    if response:
        for hit in response:
            new_entry = {
                '_source': hit._d_,
                '_index': hit.meta.index,
                '_score': hit.meta.score
            }
            data.append(new_entry)

    return data


class ESSearch(generics.RetrieveAPIView):
    """
    Send ElasticSearch query and return the result as JSON
    """

    def get(self,request):
        response = []
        self.queryset = []
        search_query = self.request.query_params.get('q')
        print(f'search_query: {search_query}')
        if search_query and search_query is not None:
            response = get_search(search_query)

        return Response(response)