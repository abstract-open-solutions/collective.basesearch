# -*- coding: utf-8 -*-

try:
    from collection import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from zope.component import getUtility
from zope.component import getMultiAdapter

try:
    from zope.app.schema.vocabulary import IVocabularyFactory
except:
    from zope.schema.interfaces import IVocabularyFactory
try:
    from Products.ATVocabularyManager.namedvocabulary import NamedVocabulary
    HAS_ATVOCAB_MANAGER = True
except ImportError:
    HAS_ATVOCAB_MANAGER = False

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from plone.i18n.normalizer import idnormalizer
from plone.memoize import view

from collective.basesearch.utils import is_collection
from collective.basesearch.utils import get_collection_query


class LazyList(list):
    """Lazy list with custom formatting for items.
    Initialize it w/ a set of items and a method
    that will be used to format returned items.
    """

    def __init__(self, items, format_method):
        super(LazyList, self).__init__(items)
        self.format_method = format_method

    def __getslice__(self, start, stop):
        """ deprecated but used in python2.7
        """
        elements = super(LazyList, self).__getslice__(start, stop)
        for i in elements:
            yield self.format_item(i)

    def __getitem__(self, index):
        elements = super(LazyList, self).__getitem__(index)
        return self.format_item(elements)

    def __iter__(self):
        elements = super(LazyList, self).__iter__()
        for i in elements:
            yield self.format_item(i)

    def format_item(self, item):
        return self.format_method(item)


class ViewMixin(BrowserView):

    @property
    def tools(self):
        return self.context.restrictedTraverse('@@plone_tools')

    @property
    def ps(self):
        return self.context.restrictedTraverse('@@plone_portal_state')

    @property
    def wftool(self):
        return self.tools.workflow()

    def get_state_display(self, value, _type=None):
        _type = _type or getattr(self, 'ptype', None)
        return self.wftool.getTitleForStateOnType(value, _type)

    def get_named_vocab(self, name):
        vocab = NamedVocabulary(name)
        vocab = vocab.getVocabulary(self.context)
        vocab = dict(vocab.getDisplayList(self.context).items())
        return vocab

    def get_vocab(self, name):
        util = getUtility(IVocabularyFactory, name=name)
        return util(self.context)

    def formatter(self, ftype):
        locale = self.ps.locale()
        formatter = locale.numbers.getFormatter(ftype)
        return formatter


class BaseSearchView(ViewMixin):

    ptype = ''
    search_fields = {}
    results = None
    show_result_with_no_query = False
    show_search_fields_for_collections = False
    export_csv_enabled = False
    custom_export_view = None

    @property
    def form_action_url(self):
        url = self.context.absolute_url()
        return url + '/' + self.__name__

    @property
    def wrapper_id(self):
        value = self.ptype
        if isinstance(self.ptype, (list, tuple)):
            value = '-'.join(self.ptype)
        return idnormalizer.normalize(value)

    def is_default_view(self):
        return self.context.getLayout() == self.__name__

    @property
    def display_fields(self):
        """ fields showed in results listing
        """
        return self.search_fields

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.form = request.form

    def __call__(self):
        if self.form.get('search') or self.show_result_with_no_query:
            self.handle_search()
        if self.form.get('export_csv'):
            return self.handle_export()
        return super(BaseSearchView, self).__call__()

    @property
    def catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    def is_collection(self):
        return is_collection(self.context)

    @property
    def show_search_form(self):
        if self.is_collection():
            return self.show_search_fields_for_collections
        return True

    def _get_search_data(self):
        data = {}
        for k in self.search_fields.iterkeys():
            if self.form.get(k):
                data[k] = self.form.get(k)
        return data

    def handle_search(self):
        data = self._get_search_data()
        self.results = self._get_results(data=data)

    def handle_export(self):
        def get_exporter(name):
            return getMultiAdapter((self.context, self.request),
                                   name=name)

        if self.custom_export_view:
            # custom export
            exporter = get_exporter(self.custom_export_view)
            return exporter.export()
        else:
            # export table as it is in search view
            header, lines = self._get_export_results()
            exporter = get_exporter('base-csv-export')
            return exporter.export(lines,
                                   header=header)

    def _get_export_results(self):
        self.handle_search()
        header = self.display_fields.values()
        lines = []
        for item in self.results:
            line = [item[k] for k in self.display_fields.iterkeys()]
            lines.append(line)
        return header, lines

    @property
    def base_query(self):
        query = {
            'portal_type': self.ptype
        }
        if self.is_collection():
            query.update(get_collection_query(self.context))
        return query

    def _get_results(self, data=None):
        if data is None:
            return None
        query = self.base_query.copy()
        query.update(data)
        return LazyList(
            self.catalog.searchResults(query),
            self.get_display_values
        )

    @property
    def _display_converters(self):
        plone_view = self.context.restrictedTraverse('@@plone')
        get_date = lambda x, **kw: plone_view.toLocalizedTime(x)
        # get_state_display comes from ViewMixin
        get_state = lambda x, **kw: self.get_state_display(x)
        return {
            # klass converters
            'datetime': get_date,
            'DateTime': get_date,
            'review_state': get_state,
        }

    def get_display_values(self, brain):
        # defaults to brain attributes
        data = {}
        default_converter = lambda x: x
        for k in self.display_fields.iterkeys():
            if hasattr(brain, k):
                value = getattr(brain, k, None)
                converter = self._display_converters.get(k)
                if converter is None:
                    # look for klass converter
                    klass_name = value.__class__.__name__
                    converter = self._display_converters.get(klass_name,
                                                             default_converter)
                data[k] = converter(value)
        # insert always title and url
        data['title'] = brain.Title
        data['url'] = brain.getURL()
        return data

    @property
    def _states_blacklist(self):
        """ blacklist states for review_state filter
        """
        if self.ps.anonymous():
            return ('private', )
        return ()

    @view.memoize_contextless
    def states(self):
        states_blacklist = self._states_blacklist
        wftool = getToolByName(self.context, 'portal_workflow')
        wf_id = wftool.getChainForPortalType(self.ptype)[0]
        wf = wftool[wf_id]
        return [(x.id, x.title)
                for x in wf.states.objectValues()
                if x.id not in states_blacklist]


