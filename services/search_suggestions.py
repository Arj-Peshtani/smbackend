import requests
import json
import re
import pprint


ELASTIC = 'http://localhost:9200/servicemap-fi/'

BASE_QUERY_SCORE = """
{
  "_source": ["suggest"],
  "size": 200,
  "highlight": {
    "fields": {
      "suggest": {},
      "suggest.part": {}
    }
  },
  "aggs" : {
    "name" : {
      "terms" : { "field" : "suggest.name.raw", "size": 500, "order": {"avg_score": "desc"} },
      "aggs": { "avg_score": { "avg": {"script": "_score"}}}
    },
    "location" : {
      "terms" : { "field" : "suggest.location.raw", "size": 10, "order": {"avg_score": "desc"}  },
      "aggs": { "avg_score": { "avg": {"script": "_score"}}}
    },
    "keyword" : {
      "terms" : { "field" : "suggest.keyword.raw", "size": 10, "order": {"avg_score": "desc"}  },
      "aggs": { "avg_score": { "avg": {"script": "_score"}}}
    },
    "service" : {
      "terms" : { "field" : "suggest.service.raw", "size": 50, "order": {"avg_score": "desc"}   },
      "aggs": { "avg_score": { "avg": {"script": "_score"}}}
    },
    "complete_matches" : {
      "filter" : {
        "and": [
          {
            "query": {
              "query_string": {
                "default_field":"text",
                "default_operator": "AND",
                "query": "(text:() OR extra_searchwords:())"
              }
            }
          },
          {
            "terms": {
              "public": [true]
            }
          }
        ]
      }
    }
  },
  "query": {
    "filtered": {
      "query": { },
      "filter": {
        "and": [
          {
            "terms": {
              "django_ct": ["services.unit"]
            }
          },
          {
            "query": {
              "bool": {
                "must": [
                  {
                    "match": {
                      "text": {
                        "query": "insert and text and here",
                        "operator": "and"
                      }
                    }
                  },
                  { }
                ]
              }
            }
          },
          {
            "terms": {
              "public": [true]
            }
          }
        ]
      }
    }
  }
}
"""


BASE_QUERY_UNIT_COUNT = """
{
  "_source": ["suggest"],
  "size": 200,
  "highlight": {
    "fields": {
      "suggest": {},
      "suggest.part": {}
    }
  },
  "aggs" : {
    "name" : {
      "terms" : { "field" : "suggest.name.raw", "size": 500, "order": {"max_score": "desc"} },
      "aggs": { "max_score": { "max": {"script": "_score"}}}
    },
    "location" : {
      "terms" : { "field" : "suggest.location.raw", "size": 10},
      "aggs": { "max_score": { "max": {"script": "_score"}}}
    },
    "keyword" : {
      "terms" : { "field" : "suggest.keyword.raw", "size": 10},
      "aggs": { "max_score": { "max": {"script": "_score"}}}
    },
    "service" : {
      "terms" : { "field" : "suggest.service.raw", "size": 50},
      "aggs": { "max_score": { "max": {"script": "_score"}}}
    },
    "complete_matches" : {
      "filter" : {
        "and": [
          {
            "query": {
              "query_string": {
                "default_field":"text",
                "default_operator": "AND",
                "query": "(text:() OR extra_searchwords:())"
              }
            }
          },
          {
            "terms": {
              "public": [true]
            }
          }
        ]
      }
    }
  },
  "query": {
    "filtered": {
      "query": { },
      "filter": {
        "and": [
          {
            "terms": {
              "django_ct": ["services.unit"]
            }
          },
          {
            "query": {
              "bool": {
                "must": [
                  {
                    "match": {
                      "text": {
                        "query": "insert and text and here",
                        "operator": "and"
                      }
                    }
                  },
                  { }
                ]
              }
            }
          },
          {
            "terms": {
              "public": [true]
            }
          }
        ]
      }
    }
  }
}

"""

# sorting by unit count is required to enable
# intelligent extra searchword -> service
# suggestions
BASE_QUERY = BASE_QUERY_UNIT_COUNT

# BASE_QUERY_SCORE breaks down with "lastentarha"
# BASE_QUERY = BASE_QUERY_SCORE

# TODO! don't show minimal completions which are laready included in other suggestions?
# especially with unit sets identical


def unit_results(search_query):
    _next = 'http://localhost:8000/v2/search/?type=unit&q={}'.format(search_query)
    results = []
    while _next is not None:
        data = requests.get(_next).json()
        _next = data['next']
        results += data['results']
    return results


def _matches_complete_word_tokens(result):
    return result.get('aggregations', {}).get('complete_matches', {}).get('doc_count', 1) > 0


def generate_suggestions(query):
    query_lower = query.lower()
    result = suggestion_response(query)

    last_word = query.split()[-1]

    last_word_lower = last_word.lower()
    last_word_re = re.compile(last_word_lower + r'[-\w]*', flags=re.IGNORECASE)

    suggestions_by_type = {}
    minimal_completions = {}

    match_id = -1
    for _type, value in result['aggregations'].items():
        if _type == 'location' and len(value['buckets']) == 1 or _type == 'complete_matches':
            continue
        for term in value.get('buckets', []):
            text = term['key']
            text_lower = text.lower()
            match_type = 'indirect'
            boundaries = None

            full_match = query_lower.find(text_lower)
            if full_match == 0:
                boundaries = [0, len(text_lower)]
                match_type = 'full_query'
            else:
                partial_match = text_lower.find(last_word_lower)
                if partial_match != -1:
                    match_type = 'substring'
                if partial_match == 0:
                    boundaries = [partial_match, partial_match + len(last_word_lower) + 1]
                    match_type = 'prefix'
                    query_before_last_word = query.split()[:-1]
                    if ' '.join(query_before_last_word).lower() not in text_lower:
                        text = last_word_re.sub(text, query)

            match_id += 1
            match = {
                'id': match_id,
                'text': text,
                'score': term.get('avg_score', {}).get('value', None),
                'doc_count': term['doc_count'],
                'field': _type,
                'match_type': match_type,
                'match_boundaries': boundaries
            }
            if match_type == 'prefix':
                matching_part = last_word_re.search(text)
                if matching_part:
                    matching_text = matching_part.group(0)
                    if matching_text.lower() != query_lower:
                        match_copy = match.copy()
                        match_copy['original'] = text
                        match_copy['text'] = matching_text
                        existing_completion = minimal_completions.get(match_copy['text'].lower())
                        if existing_completion:
                            count = existing_completion['doc_count']
                        else:
                            count = 0
                        match_copy['doc_count'] = count + term['doc_count']  # todo still don't work
                        match_copy['category'] = 'minimal_completion'
                        minimal_completions[match_copy['text'].lower()] = match_copy

            if _type == 'name' and match_type == 'indirect':
                continue
            # if _type == 'service' and match_type == 'full_query':
            #     continue
            if match_type == 'indirect':
                key = _type
            else:
                key = 'completions'
            match['category'] = match['field']
            suggestions_by_type.setdefault(key, []).append(match)

    # TODO: originally filtered out single-document minimals
    suggestions_by_type['minimal_completions'] = [v for v in minimal_completions.values()]

    return {
        'query': query,
        'query_word_count': len(query.split()),
        'ambiguous_last_word': len(minimal_completions) > 1 and query.lower() in [s['text'].lower() for s in minimal_completions.values()],
        'incomplete_query': not _matches_complete_word_tokens(result),
        'suggestions': suggestions_by_type
    }


LIMITS = {
    'minimal_completions': 10,
    'completions': 10,
    'service': 10,
    'name': 10,
    'location': 5,
    'keyword': 5}


def output_suggestion(match, query, keyword_match=False):
    if match['match_type'] == 'indirect' and not keyword_match:
        suggestion = '{} + {}'.format(match['text'], query)
    else:
        suggestion = match['text']
    return {
        'suggestion': suggestion,
        'count': match.get('doc_count') if match.get('category') != 'minimal_completion' else None
    }

# problem arabia päiväkoti islamilainen päiväkoti


def query_found_as_keyword(suggestions, query):
    query_lower = query.lower()

    def exact_keyword_match(match):
        return (
            match['field'] == 'keyword'
            and match['match_type'] == 'full_query'
            and match['text'].lower() == query_lower
        )

    def partial_service_match(match):
        return (
            match['field'] == 'service'
            and match['match_type'] != 'indirect'
            and query_lower in match['text'].lower()
        )
    completions = suggestions.get('suggestions', {}).get('completions', [])
    return (next((c for c in completions if exact_keyword_match(c)), None) is not None
            and next((c for c in completions if partial_service_match(c)), None) is None)


def choose_suggestions(suggestions, limits=LIMITS):
    # rule 2: show most restrictive + least restrictive?
    #  (except can't differentiate between multiple most restrictives)
    # rule 3: if there are only one results, period, just show the name of the unit?
    #   no: show whatever matches best

    # TODO ! Must prefer "phrase substring" matches: kallion kir -> kallion kirjasto/kirkko
    # to kauklahden kir -- this is reflected in the score currently, but must make better
    query = suggestions['query']
    keyword_match = query_found_as_keyword(suggestions, query)
    if suggestions['incomplete_query']:
        active_match_types = ['completions']
    else:
        if keyword_match:
            active_match_types = ['service', 'completions', 'service', 'name']
        else:
            active_match_types = ['completions', 'service', 'name', 'location', 'keyword']
    suggestions_by_type = suggestions['suggestions']
    # results_per_type = math.floor(limit / len(suggestions_by_type.keys()))

    results = []
    seen = set()
    minimal_results = []
    if suggestions['query_word_count'] == 1:
        for index, match in enumerate(suggestions_by_type.get('minimal_completions', [])[0:limits['minimal_completions']]):
            suggestion = output_suggestion(match, query, keyword_match=keyword_match)
            if suggestion['suggestion'].lower() not in seen:
                seen.add(suggestion['suggestion'])
                minimal_results.append(suggestion)

    for _type in active_match_types:
        for match in suggestions_by_type.get(_type, [])[0:limits[_type]]:
            if suggestions['ambiguous_last_word'] and match['match_type'] == 'indirect':
                continue
            if match['match_type'] == 'indirect' and _type == 'keyword':
                continue
            if keyword_match and match['match_type'] == 'full_query' and match['field'] == 'keyword':
                continue
            suggestion = output_suggestion(match, query, keyword_match=keyword_match)
            if suggestion['suggestion'].lower() not in seen:
                seen.add(suggestion['suggestion'])
                results.append(suggestion)

    results = minimal_results + results

    return {
        'suggestions': results,
        'requires_completion': suggestions['incomplete_query']
    }
    # ordering
    # 1. minimal completions with doc_count == 1
    #    ordered by score
    # 2. minimal completions with more docs
    #    ordered by score
    # 3. other remaining completions ordered by score ?
    # full queries: add locations (randomly?)
    # rule 1: remove buckets with only one possibility (redundant) DONE
    # rule 2: show most restrictive + least restrictive?
    #  (except can't differentiate between multiple most restrictives)
    # rule 3: if there are only one results, period, just show the name of the unit?

    #   NOTE: actually, the tarkennus won't show up in the ui for already single-matching queries


def suggestion_response(query):
    response = requests.get(
        '{}/_search/?search_type=count'.format(ELASTIC),
        data=json.dumps(suggestion_query(query)))
    return response.json()


def suggestion_query(search_query):
    search_query = search_query.strip()
    query = json.loads(BASE_QUERY)

    if len(search_query) == 0:
        return None

    last_word = None
    first_words = None
    split = search_query.split()
    if len(split) > 0:
        last_word = split[-1]
        first_words = " ".join(split[:-1])

    query['aggs']['complete_matches']['filter']['and'][0]['query']['query_string']['query'] = (
        "(text:({0}) OR extra_searchwords:({0}))".format(search_query))

    query['query']['filtered']['query'] = {
        'match': {'suggest.combined': {'query': search_query}}}
    # del query['query']['filtered']['filter']['and'][1]
    filter_query_must = query['query']['filtered']['filter']['and'][1]['query']['bool']['must']

    if first_words:
        filter_query_must[0]['match']['text']['query'] = first_words
        filter_query_must[1] = {
            'match': {'suggest.combined': {'query': last_word}}}
    else:
        del query['query']['filtered']['filter']['and'][1]
    return query


def get_suggestions(query):
    return choose_suggestions(generate_suggestions(query))


def p(val):
    if val:
        pprint.pprint(val, width=100)


def f(q):
    # p(suggestion_query(q))
    # p(suggestion_response(q))
    suggestions = generate_suggestions(q)
    chosen_suggestions = choose_suggestions(suggestions)
    # pprint.pprint(suggestions)
    # pprint.pprint(chosen_suggestions)
    for s in chosen_suggestions['suggestions']:
        if s['count']:
            print('{} ({} toimipistettä)'.format(s['suggestion'], s['count']))
        else:
            print(s['suggestion'])


def loop():
    while True:
        q = input("\nsearch: ")
        if q == '' or q == '.':
            break
        elif q[-1] == '?':
            try:
                results = unit_results(q[:-1])
                for r in results:
                    print(r['name']['fi'],
                          'https://palvelukartta.hel.fi/unit/{}'.format(r['id']),
                          r['score'])
                print(len(results))
            except requests.exceptions.ConnectionError:
                print('Error connecting to smbackend api')
        else:
            f(q)
