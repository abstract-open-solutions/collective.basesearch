# -*- coding: utf-8 -*-

try:
    from collection import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


from collective.basesearch.views import BaseSearchView


class MySearch(BaseSearchView):
    """ a browser view for searching
    """
    ptype = 'MyContentType'
    show_result_with_no_query = True

    search_fields = OrderedDict([
        ('foo', u'Foo'),
        ('bar', u'Bar'),
        ('review_state', u'State'),
    ])

    display_fields = OrderedDict([
        ('foo', u'Foo'),
        ('bar', u'Bar'),
        ('review_state', u'State'),
        ('baz', u'Baz'),
    ])

    @property
    def _display_converters(self):
        converters = super(MySearch, self)._display_converters
        baz_vocab = self.get_vocab('my_vocab')
        converters.update({
            'baz': lambda x, **kw: baz_vocab.getTermByToken(x).title
        })
        return converters
