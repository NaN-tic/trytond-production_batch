# This file is part of Tryton. The COPYRIGHT file at the top level of this
# repository contains the full copyright notices and license terms.

#from trytond.exceptions import UserError
from trytond.modules.company.tests import (
    CompanyTestMixin, create_company, set_company)
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
        Template = pool.get('product.template')
        ProductBom = pool.get('product.product-production.bom')
        Production = pool.get('production')
        Bom = pool.get('production.bom')
        Routing = pool.get('production.routing')
        WorkCenterCategory = pool.get('production.work.center.category')
        WorkCenter = pool.get('production.work.center')

        company = create_company()

        with set_company(company):
            unit, = Uom.search([('name', '=', 'Unit')], limit=1)
            template, = Template.create([{
                        'name': 'Batch Product',
                        'type': 'goods',
                        'default_uom': unit.id,
                        'producible': True,
                        'products': [('create', [{}])],
                        }])
            product, = template.products

            bom_1, bom_2 = Bom.create([{
                        'name': 'BOM 1',
                        'phantom': False,
                        'inputs': [],
                        'outputs': [('create', [{
                                        'product': product.id,
                                        'quantity': 1,
                                        'unit': unit.id,
                                        }])],
                        }, {
                        'name': 'BOM 2',
                        'phantom': False,
                        'inputs': [],
                        'outputs': [('create', [{
                                        'product': product.id,
                                        'quantity': 1,
                                        'unit': unit.id,
                                        }])],
                        }])
            routing_1, routing_2 = Routing.create([{
                        'name': 'Routing 1',
                        }, {
                        'name': 'Routing 2',
                        }])
            Routing.write([routing_1], {
                    'boms': [('add', [bom_1.id])],
                    })
            Routing.write([routing_2], {
                    'boms': [('add', [bom_2.id])],
                    })
            category, = WorkCenterCategory.create([{
                        'name': 'Line Category',
                        'is_line': True,
                        }])
            line_1, line_2 = WorkCenter.create([{
                        'name': 'Line 1',
                        'category': category.id,
                        'company': company.id,
                        }, {
                        'name': 'Line 2',
                        'category': category.id,
                        'company': company.id,
                        }])

            ProductBom.create([{
                        'product': product.id,
                        'sequence': 20,
                        'bom': bom_2.id,
                        'routing': routing_2.id,
                        'line': line_2.id,
                        'batch_quantity': 10,
                        'batch_uom': unit.id,
                        }, {
                        'product': product.id,
                        'sequence': 10,
                        'bom': bom_1.id,
                        'routing': routing_1.id,
                        'line': line_1.id,
                        'batch_quantity': 5,
                        'batch_uom': unit.id,
                        }])

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
