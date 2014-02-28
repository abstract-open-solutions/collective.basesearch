#-*- coding: utf-8 -*-

from plone.app.collection.interfaces import ICollection
from plone.app.querystring import queryparser

from Products.ATContentTypes.interfaces import IATTopic


def is_collection(obj):
    return IATTopic.providedBy(obj) or ICollection.providedBy(obj)


def parse_new_collection_query(context):
    """ given a new collection item returns its catalgo query
    """
    parse = queryparser.parseFormquery
    return parse(context, context.getRawQuery())


def get_collection_query(obj):
    """ return collection's query params
    """

    if IATTopic.providedBy(obj):
        # old style collection
        return obj.buildQuery()

    if ICollection.providedBy(obj):
        # new style collection
        return parse_new_collection_query(obj)
