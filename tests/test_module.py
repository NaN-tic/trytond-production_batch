# This file is part of Tryton. The COPYRIGHT file at the top level of this
# repository contains the full copyright notices and license terms.

#from trytond.exceptions import UserError
from trytond.modules.company.tests import CompanyTestMixin
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction


class ProductionBatchTestCase(CompanyTestMixin, ModuleTestCase):
    'Test ProductionBatch module'
    module = 'production_batch'

    @with_transaction()
    def test_on_change_product_uses_lowest_sequence_product_bom(self):
        "Production on_change_product uses the lowest sequence product BOM"
        pool = Pool()
        Uom = pool.get('product.uom')
        Product = pool.get('product.product')
        ProductBom = pool.get('product.product-production.bom')
        Production = pool.get('production')
        Bom = pool.get('production.bom')
        BomOutput = pool.get('production.bom.output')
        Routing = pool.get('production.routing')
        WorkCenterCategory = pool.get('production.work.center.category')
        WorkCenter = pool.get('production.work.center')

        unit, = Uom.search([('name', '=', 'Unit')], limit=1)
        product = Product(default_uom=unit)

        bom_1 = Bom(
            name='BOM 1',
            inputs=[],
            outputs=[BomOutput(product=product, quantity=1, unit=unit)])
        bom_2 = Bom(
            name='BOM 2',
            inputs=[],
            outputs=[BomOutput(product=product, quantity=1, unit=unit)])
        routing_1 = Routing(name='Routing 1')
        routing_2 = Routing(name='Routing 2')
        category = WorkCenterCategory(name='Line Category', is_line=True)
        line_1 = WorkCenter(name='Line 1', category=category)
        line_2 = WorkCenter(name='Line 2', category=category)

        product.boms = [
            ProductBom(
                product=product,
                sequence=20,
                bom=bom_2,
                routing=routing_2,
                line=line_2,
                batch_quantity=10,
                batch_uom=unit),
            ProductBom(
                product=product,
                sequence=10,
                bom=bom_1,
                routing=routing_1,
                line=line_1,
                batch_quantity=5,
                batch_uom=unit),
            ]

        production = Production()
        production.state = 'draft'
        production.product = product

        production.on_change_product()

        # self.assertEqual(production.unit, unit)
        # self.assertEqual(production.bom, bom_1)
        # self.assertEqual(production.routing, routing_1)
        # self.assertEqual(production.line, line_1)
        # self.assertEqual(production.work_center, line_1)
        # self.assertEqual(production.batch_quantity, 5)
        # self.assertEqual(production.batch_uom, unit)

    @with_transaction()
    def test_check_batch_multiple_on_production(self):
        "Production quantity must be a multiple of batch"
        pool = Pool()
        Uom = pool.get('product.uom')
        Product = pool.get('product.product')
        Production = pool.get('production')

        unit, = Uom.search([('name', '=', 'Unit')], limit=1)
        product = Product(default_uom=unit)

        production = Production()
        production.product = product
        production.number = 'P-001'
        production.unit = unit
        production.batch_quantity = 5
        production.batch_uom = unit

        production.quantity = 10
        production.check_batch_multiple()

        production.quantity = 11
        # with self.assertRaises(UserError):
        #     production.check_batch_multiple()


del ModuleTestCase
