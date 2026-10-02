import unittest

from proteus import Model
from trytond.modules.company.tests.tools import create_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class TestBatchConversions(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        activate_modules('production_batch')
        create_company()
        Template = Model.get('product.template')
        Uom = Model.get('product.uom')
        Bom = Model.get('production.bom')
        ProductBom = Model.get('product.product-production.bom')
        unit, = Uom.find([('name', '=', 'Unit')])
        template = Template(name='Bread', type='goods', default_uom=unit,
            producible=True)
        template.save()
        product, = template.products
        bom = Bom(name='Bread recipe')
        output = bom.outputs.new()
        output.product = product
        output.unit = unit
        output.quantity = 1
        bom.save()
        link = ProductBom(product=product, bom=bom)
        link.units_per_pallet = 256
        link.units_per_mass = 128
        link.batch_quantity = 512
        self.assertEqual(link.batch_pallets, 2)
        self.assertEqual(link.batch_masses, 4)
        link.batch_pallets = 3
        self.assertEqual(link.batch_quantity, 768)
        self.assertEqual(link.batch_masses, 6)
        link.batch_masses = 5
        self.assertEqual(link.batch_quantity, 640)
        self.assertEqual(link.batch_pallets, 2.5)
        link.masses_per_hour = 4
        link.units_per_hour = 512
        link.pallets_per_hour = 2
        link.save()
        link.reload()
        self.assertEqual(link.batch_quantity, 640)
        self.assertEqual(link.batch_masses, 5)
        self.assertEqual(link.batch_pallets, 2.5)
        self.assertEqual(link.masses_per_hour, 4)
        self.assertEqual(link.units_per_hour, 512)
        self.assertEqual(link.pallets_per_hour, 2)
        link.units_per_mass = 116
        link.batch_quantity = 3840
        self.assertEqual(link.batch_masses, round(3840 / 116, 6))
        link.save()
        link.reload()
        self.assertEqual(link.batch_quantity, 3840)
        self.assertEqual(link.batch_pallets, 15)
        link.units_per_mass = 0
        self.assertIsNone(link.batch_masses)
        link.batch_pallets = 0
        self.assertEqual(link.batch_quantity, 0)
        self.assertIsNone(link.batch_masses)
        link.units_per_mass = 128
        self.assertEqual(link.batch_masses, 0)
        link.batch_pallets = None
        self.assertIsNone(link.batch_quantity)
        self.assertIsNone(link.batch_masses)

        # Different batch UoM must convert through the product default UoM.
        dozen = Uom(name='Dozen', symbol='doz', category=unit.category,
            factor=12, rate=round(1 / 12, 12), rounding=0.000001, digits=6)
        dozen.save()
        link.batch_uom = dozen
        link.batch_quantity = 64
        self.assertEqual(link.batch_pallets, 3)
        self.assertEqual(link.batch_masses, 6)
        link.batch_masses = 3
        self.assertEqual(link.batch_quantity, 32)
        self.assertEqual(link.batch_pallets, 1.5)
        link.save()
        link.reload()
        self.assertEqual(link.batch_quantity, 32)
        self.assertEqual(link.batch_pallets, 1.5)
        self.assertEqual(link.batch_masses, 3)
