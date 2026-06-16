from elasticsearch.dsl import analysis, analyzer, tokenizer


# Documentation about analysers:
# https://www.elastic.co/docs/reference/text-analysis/analyzer-reference
# https://www.elastic.co/docs/reference/text-analysis/tokenizer-reference

def id_analyzer():
    ''' Analyser for the different IDs in the OmicsPred indexes '''
    return analyzer(
        'id_analyzer',
        tokenizer="keyword",
        filter=["lowercase", "remove_duplicates"]
    )


def ngram_analyzer():
    ''' N-gram analyser for the OmicsPred indexes '''
    return analyzer(
        'ngram',
        tokenizer=tokenizer('ngram', 'ngram', min_gram=3, max_gram=10),
        filter=['lowercase', 'stop', 'asciifolding', 'remove_duplicates']
    )


def word_delimiter_analyzer():
    ''' Standard analyser for the OmicsPred indexes '''
    length_from_2_char = analysis.token_filter(
        'length_from_2_char',
        type="length",
        min=3
    )
    return analyzer(
        'word_delimiter',
        tokenizer="whitespace",
        filter=[length_from_2_char, "lowercase", "stop", "snowball", "asciifolding", "remove_duplicates"]
    )


def name_delimiter_analyzer():
    ''' Analyzer for the fields with composed parts (dash, underscore, ...) '''
    # Split sentence in words at non-alphanumeric characters
    word_delimiter_graph_preserve_original = analysis.token_filter(
        'word_delimiter_graph_preserve_original',
        type="word_delimiter_graph",
        preserve_original=True
    )
    length_from_2_char = analysis.token_filter(
        'length_from_2_char',
        type="length",
        min=2
    )
    return analyzer(
        'name_delimiter',
        tokenizer="keyword",
        filter=[length_from_2_char, word_delimiter_graph_preserve_original, "flatten_graph", "lowercase", "stop", "snowball", "asciifolding", "remove_duplicates"]
    )
