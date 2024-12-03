from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.serializers import ValidationError
from elasticsearch_dsl import Search


# No need to redeclare "custom_exception_handler" as it is already used in rest_api.views

result_size = 25

def query_fields():
    return ['id^3','name^3','platform_name','omics_type',
            'category','full_name','synonyms_list^2','description',
            'genes.external_id^2','genes.name^2','genes.synonyms_list^2','genes.description',
            'proteins.external_id^2','proteins.names^2','proteins.synonyms_list^2','proteins.description',
            'metabolites.external_id^2','metabolites.name^2','metabolites.synonyms_list^2','metabolites.description']


def get_search(query):
    s = Search(index="*").extra(size=result_size).query("multi_match", query=query, fields=query_fields())
    response = s.execute()

    data = []
    if response:
        for hit in response:
            hit_data = hit._d_
            use_hit = True
            # Filter out the hits without associated score
            if 'scores_count' in hit_data.keys():
                if hit_data['scores_count'] == 0:
                    use_hit = False

            if use_hit:
                new_entry = {
                    '_source': hit_data,
                    '_index': hit.meta.index,
                    '_score': hit.meta.score
                }
                data.append(new_entry)

    return data


class ESSearch(generics.RetrieveAPIView):
    """
    Send Elasticsearch query and return the result as JSON
    """

    def get(self,request):
        response = []
        self.queryset = []
        search_query = self.request.query_params.get('q')
        print(f'search_query: {search_query}')
        if search_query and search_query is not None:
            response = get_search(search_query)

        return Response(response)