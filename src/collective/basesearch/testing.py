from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting

from plone.testing import z2

from zope.configuration import xmlconfig


class CollectivebasesearchLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import collective.basesearch
        xmlconfig.file(
            'configure.zcml',
            collective.basesearch,
            context=configurationContext
        )

        # Install products that use an old-style initialize() function
        #z2.installProduct(app, 'Products.PloneFormGen')

#    def tearDownZope(self, app):
#        # Uninstall products installed above
#        z2.uninstallProduct(app, 'Products.PloneFormGen')


COLLECTIVE_BASESEARCH_FIXTURE = CollectivebasesearchLayer()
COLLECTIVE_BASESEARCH_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_BASESEARCH_FIXTURE,),
    name="CollectivebasesearchLayer:Integration"
)
