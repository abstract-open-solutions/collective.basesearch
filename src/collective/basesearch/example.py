# -*- coding: utf-8 -*-

try:
    from collection import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


from collective.basesearch.views import BaseSearchView
_ = lambda x: x


class MySearch(BaseSearchView):
    """ a browser view for searching
    """
    ptype = 'MyContentType'
    show_result_with_no_query = True

    search_fields = OrderedDict([
        ('foo', _(u'Foo')),
        ('bar', _(u'Bar')),
        ('review_state', _(u'State')),
    ])

    display_fields = OrderedDict([
        ('foo', _(u'Foo')),
        ('bar', _(u'Bar')),
        ('review_state', _(u'State')),
        ('baz', _(u'Baz')),
    ])

    @property
    def _display_converters(self):
        converters = super(MySearch, self)._display_converters
        baz_vocab = self.get_vocab('my_vocab')
        converters.update({
            'baz': lambda x, **kw: baz_vocab.getTermByToken(x).title
        })
        return converters
