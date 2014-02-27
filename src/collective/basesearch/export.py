#-*- coding: utf-8 -*-

import csv
import datetime
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    from collection import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from Products.Five import BrowserView
from Products.CMFPlone.utils import safe_unicode
# from plone.memoize import view


from .views import BaseSearchView


class ExportCSV(BrowserView):

    ext = 'csv'
    content_type = 'text/csv'
    delimiter = ';'

    def __call__(self,
                 lines,
                 header=None,
                 filename=None,
                 filename_prefix=None):
        return self.export(lines,
                           header=header,
                           filename=None,
                           filename_prefix=None)

    def export(self, lines, header=None,
               filename=None, filename_prefix=None):
        data = self._create_csv(lines, header=header)
        now = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        prefix = filename_prefix or 'export_'
        if filename is None:
            filename = "%s_%s.%s" % (prefix, now, self.ext)
        self._prepare_response(data, filename)
        return data

    def _create_csv(self, lines, header=None):
        """ Write header + lines within the CSV file """
        datafile = StringIO()
        writer = csv.writer(datafile, delimiter=self.delimiter)
        if header is None:
            header, lines = lines[0], lines[1:]
        writer.writerow(header)
        writer.writerows(lines)
        # map(writer.writerow, lines)
        data = datafile.getvalue()
        datafile.close()
        return data

    def _prepare_response(self, data, filename):
        """ prepare response headers
        """
        self.request.response.addHeader('Content-Disposition',
                                        'attachment; filename=%s' % filename)
        self.request.response.addHeader('Content-Type',
                                        '%s; charset=utf-8' % self.content_type
                                        )
        self.request.response.addHeader('Content-Length', "%d" % len(data))
        self.request.response.addHeader('Pragma', "no-cache")
        self.request.response.addHeader('Cache-Control',
                                        'must-revalidate, \
                                        post-check=0, \
                                        pre-check=0, \
                                        public')
        self.request.response.addHeader('Expires', "0")


class BaseSearchExport(BaseSearchView):

    def __call__(self):
        return self.export()

    def export(self):
        header, lines = self._get_export_results()
        exporter = self.context.restrictedTraverse('@@base-csv-export')
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

    def get_display_values(self, brain):
        # override this in order to access full object
        data = {}
        default_converter = lambda v, obj=None: v
        obj = brain.getObject()
        for k in self.display_fields.iterkeys():
            value = ''  # default to empty string for CSV col
            if hasattr(brain, k):
                value = getattr(brain, k, None)
            else:
                try:
                    value = getattr(obj, k)
                except AttributeError:
                    field = obj.getField(k)
                    value = field and field.get(obj) or ''
            converter = self._display_converters.get(k)
            if converter is None:
                # look for klass converter
                klass_name = value.__class__.__name__
                converter = self._display_converters.get(klass_name,
                                                         default_converter)
            converted = converter(value, obj=obj)
            value = safe_unicode(converted)
            if isinstance(value, basestring):
                value = value.encode('utf-8')
            data[k] = value
        # insert always title and url
        data['title'] = brain.Title
        data['url'] = brain.getURL()
        return data
