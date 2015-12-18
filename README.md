# Flask-Search
Flask-Search is a Flask extension that adds powerful search capability(powered by Elasticsearch) to Flask-SQLAlchemy models.

## Install
```
pip install FlaskSearch
```

## Quickstart
*A full-fledged example app along with filler data is also available in the `example` directory.*

To get up and running with Flask-Search, here's what you need to do. 
### Intitialize extension and setup Models

```python
from flask.ext.search import FlaskSearch, FlaskSearchQueryMixin
app.config['ELASTICSEARCH_INDEX'] = "MyFlaskApp" # Defaults to FlaskSearch
app.config['ELASTICSEARCH_URL'] = {"host": "localhost", "port": 9200}) # Defaults to {"host": "localhost", "port": 9200}

class Post(db.Model):
	query_class = FlaskSearchQueryMixin # This adds the .elasticsearch() method to Post.query
	# Any fields you want to have indexed should be included in this list. 
	# The strings should match exactly to the field names. 
	# You can also boost certain fields using the '^(number)' syntax. 
	# The default boost value is 1, so a boost value of 2 will make a field twice as relevant while searching as a field with a boost value of 1
	# You can also use boost values between 0 and 1 to reduce the relevance of a field
	__indexed_fields__ = ['title^2', 'body']
	 id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    user = db.Column(db.Integer)

    def __init__(self, title, body):
        self.title = title
        self.body = body

    def __repr__(self):
        return '<Title %r>' % self.title

fsearch = FlaskSearch(app, Post) # You need to add any models you want to have indexed as arguments. This will also create the index mappings if they don't already exist.
```
1. Set the `ELASTICSEARCH_INDEX` config value to what you want your index to be named.
2. Set the `ELASTICSEARCH_URL` config value to a dictionary containing a `host` and a `port` value.
3. Add a `query_class` attribute to your model pointing to `FlaskSearchQueryMixin`.
4. Add an `__indexed_fields__` attribute to your model listing the fields you want to have indexed, optionally including a boost value for specific fields. Only text fields are supported.

---
Now whenever a new row is added/updated, it will be indexed to Elasticsearch. Similarly, whenever a row is deleted, it will be removed from the Elasticsearch index.

## Searching
This is where all the magic happens. To execute a search against the Elasticsearch index, use the `Model.query.elasticsearch` method. For instance:

```python
results = Post.query.elasticsearch("example")
```
This returns all Post instances where at least one of the indexed fields is matched. The results will be ordered according to their Elasticsearch score, unless the query includes an `order_by` call. 

You can also chain other operations to the query. For example:

```python
results = Post.query.elasticsearch("example").filter_by(user=1)
```
By default, a search will be performed on all the fields specified in `__indexed_fields__`, and a result will be returned if any field has a match(`OR` conjunction). To specify a particular field to search against, use the following syntax:

```python
results = Post.query.elasticsearch("title:example")
```
Where `title` is the field you want to search against, and `example` is your query. You can also use multiple fields, like `"title:example AND body:test"`.

The `elasticsearch` method supports the complete Lucene query string syntax, as specified [here](https://www.elastic.co/guide/en/elasticsearch/reference/2.1/query-dsl-query-string-query.html#query-string-syntax). Check out the link to find out all the awesome ways in which you can search through your data.

## Todo
- [ ] code comments
- [ ] unit tests

---
This extension is licensed under the MIT license (see `LICENSE`). The extension is inspired by and borrows code from [Flask-WhooshAlchemy](https://github.com/gyllstromk/Flask-WhooshAlchemy), which is licensed under the BSD license.