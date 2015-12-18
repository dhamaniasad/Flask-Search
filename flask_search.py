"""
flask search extension
----------------------
Powerful search functionality for Flask apps via ElasticSearch

:copyright: (c) 2015 by Asad Dhamani
:license: MIT (see LICENSE)
"""
from __future__ import absolute_import
from __future__ import with_statement

import elasticsearch

import flask.ext.sqlalchemy as flask_sqlalchemy
import heapq
from flask import _app_ctx_stack as stack
from flask import current_app

try:
    unicode
except NameError:
    unicode = str


class FlaskSearch(object):
    def __init__(self, app=None, *args):
        self.app = app
        if app is not None:
            self.init_app(app, args)

    def init_app(self, app, models):
        app.config.setdefault('ELASTICSEARCH_URL', {"host": "localhost", "port": 9200})
        app.config.setdefault('ELASTICSEARCH_INDEX', 'flasksearch')
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['flasksearch'] = self
        app.extensions['flasksearch_conn'] = self.connect(app)
        for model in models:
            _create_index(model, app.config['ELASTICSEARCH_INDEX'], app.extensions['flasksearch_conn'])
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def connect(self, app):
        settings = [{"host": app.config['ELASTICSEARCH_URL']['host'],
                     "port": app.config['ELASTICSEARCH_URL']['port']}]
        es = elasticsearch.Elasticsearch(settings)
        return es

    def teardown(self, exception):
        ctx = stack.top
        if ctx is not None:
            if hasattr(ctx, 'elasticsearch_cluster'):
                pass


class FlaskSearchQueryMixin(flask_sqlalchemy.BaseQuery):
    def __init__(self, entities, session=None):
        super(FlaskSearchQueryMixin, self).__init__(entities, session)
        self._elastic_rank = None

    def elasticsearch(self, search_query, sort=False):
        ctx = stack.top
        _modelclass = self._mapper_zero().class_
        _modelclassname = _modelclass.__name__
        index_name = current_app.config['ELASTICSEARCH_INDEX']
        if ctx is not None:
            if not hasattr(ctx, 'elasticsearch_cluster'):
                ctx.elasticsearch_cluster = current_app.extensions['flasksearch_conn']
        search_fields = getattr(_modelclass, '__indexed_fields__')
        elastic_query = {"query":
            {
                "query_string": {
                    "fields": search_fields,
                    "query": search_query
                }
            }
        }
        results = ctx.elasticsearch_cluster.search(index=index_name, doc_type=_modelclassname,
                                                   body=elastic_query, sort=["_score"])
        result_set = set()
        result_ranks = {}
        for rank, result in enumerate(results['hits']['hits']):
            pk = int(result['_id'])
            result_set.add(pk)
            result_ranks[pk] = rank
        f = self.filter(getattr(_modelclass,
                                'id').in_(result_set))
        f._elastic_rank = result_ranks
        return f

    def __iter__(self):
        super_iter = super(FlaskSearchQueryMixin, self).__iter__()
        if self._elastic_rank is None or self._order_by is not False:
            return super_iter
        super_rows = list(super_iter)
        ordered_by_whoosh_rank = []
        for row in super_rows:
            row._score = self._elastic_rank[getattr(row, 'id')]
            heapq.heappush(ordered_by_whoosh_rank,
                           (row._score, row))

        def _inner():
            while ordered_by_whoosh_rank:
                yield heapq.heappop(ordered_by_whoosh_rank)[1]

        return _inner()


def _after_flush(app, changes):
    ctx = stack.top
    if ctx is not None:
        if not hasattr(ctx, 'elasticsearch_cluster'):
            ctx.elasticsearch_cluster = app.extensions['flasksearch_conn']
    index_name = current_app.config['ELASTICSEARCH_INDEX']
    bytype = {}
    for change in changes:
        update = change[1] in ('update', 'insert')
        if hasattr(change[0].__class__, '__indexed_fields__'):
            bytype.setdefault(change[0].__class__.__name__, []).append(
                (update, change[0]))

    for model, values in bytype.items():
        primary_field = 'id'
        searchable = [x.split("^")[0] for x in values[0][1].__indexed_fields__]
        for update, v in values:
            if update:
                attrs = {}
                for key in searchable:
                    try:
                        attrs[key] = unicode(getattr(v, key))
                    except AttributeError:
                        raise AttributeError('{0} does not have {1} field {2}'
                                             .format(model, searchable, key))

                attrs[primary_field] = unicode(getattr(v, primary_field))
                body = {}
                for key, value in attrs.items():
                    if key in searchable:
                        body[key] = value
                ctx.elasticsearch_cluster.index(index=index_name,
                                                doc_type=model,
                                                id=attrs[primary_field],
                                                body=body)
            else:
                try:
                    ctx.elasticsearch_cluster.delete(index=index_name,
                                                     doc_type=model,
                                                     id=unicode(getattr(v,
                                                                        primary_field)))
                except elasticsearch.exceptions.NotFoundError:
                    pass


def _create_index(model, index, _elasticsearch):
    model_name = model.__name__
    prop_mapping = {}
    fields = [x.split("^")[0] for x in model.__indexed_fields__]
    for field in fields:
        prop_mapping[field] = {"type": "string"}
    body = {
        "mappings": {
            model_name: {
                "properties": prop_mapping
            }
        }
    }
    putmapping_body = body['mappings'][model_name]
    if _elasticsearch.indices.exists(index=index):
        if _elasticsearch.indices.exists_type(index=index,
                                              doc_type=model_name):
            pass
        else:
            _elasticsearch.indices.put_mapping(doc_type=model_name,
                                               index=index,
                                               body=putmapping_body)
    else:
        _elasticsearch.indices.create(index=index,
                                      body=body)
    return


flask_sqlalchemy.models_committed.connect(_after_flush)
