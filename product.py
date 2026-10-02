# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval, If


class BatchMixin:
    __slots__ = ()

    batch_quantity = fields.Float(
        'Batch Quantity', digits=(16, Eval('batch_uom_digits', 2)),
        depends=['batch_uom_digits'])
    batch_uom = fields.Many2One(
        'product.uom', 'Batch UoM',
        domain=[
            If(Bool(Eval('batch_uom_category', 0)),
                ('category', '=', Eval('batch_uom_category')),
                ()),
            ],
        depends=['batch_uom_category'])
    batch_uom_digits = fields.Function(
        fields.Integer('Batch UoM Digits'),
        'on_change_with_batch_uom_digits')
    batch_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Batch UoM Category'),
        'on_change_with_batch_uom_category')

    @fields.depends('product', '_parent_product.default_uom', 'batch_uom')
    def on_change_product(self):
        if self.product and not self.batch_uom:
            self.batch_uom = self.product.default_uom

    @fields.depends('product', '_parent_product.default_uom_category')
    def on_change_with_batch_uom_category(self, name=None):
        if self.product and self.product.default_uom_category:
            return self.product.default_uom_category.id

    @fields.depends('batch_uom')
    def on_change_with_batch_uom_digits(self, name=None):
        if self.batch_uom:
            return self.batch_uom.digits
        return 2

class ProductBom(BatchMixin, metaclass=PoolMeta):
    __name__ = 'product.product-production.bom'

    units_per_pallet = fields.Float(
        'Units per Pallet', digits=(16, 6),
        domain=[('units_per_pallet', '>=', 0)],
        help='Quantity per pallet in the default unit of the product.')
    units_per_mass = fields.Float(
        'Units per Dough Batch', digits=(16, 6),
        domain=[('units_per_mass', '>=', 0)],
        help='Quantity per dough batch in the default unit of the product.')
    batch_pallets = fields.Function(fields.Float(
        'Batch (Pallets)', digits=(16, 6),
        domain=[('batch_pallets', '>=', 0)],
        states={'readonly': ~Bool(Eval('units_per_pallet'))},
        depends=['units_per_pallet']),
        'on_change_with_batch_pallets', setter='set_batch_equivalent')
    batch_masses = fields.Function(fields.Float(
        'Batch (Dough Batches)', digits=(16, 6),
        domain=[('batch_masses', '>=', 0)],
        states={'readonly': ~Bool(Eval('units_per_mass'))},
        depends=['units_per_mass']),
        'on_change_with_batch_masses', setter='set_batch_equivalent')
    masses_per_hour = fields.Float(
        'Dough Batches per Hour', digits=(16, 6),
        domain=[('masses_per_hour', '>=', 0)])
    units_per_hour = fields.Float(
        'Units per Hour', digits=(16, 6),
        domain=[('units_per_hour', '>=', 0)])
    pallets_per_hour = fields.Float(
        'Pallets per Hour', digits=(16, 6),
        domain=[('pallets_per_hour', '>=', 0)])

    @fields.depends('batch_quantity', 'batch_uom', 'units_per_pallet',
        'product', '_parent_product.default_uom')
    def on_change_with_batch_pallets(self, name=None):
        if (self.batch_quantity is not None and self.units_per_pallet
                and self.batch_uom and self.product):
            Uom = Pool().get('product.uom')
            return round(Uom.compute_qty(self.batch_uom, self.batch_quantity,
                self.product.default_uom, round=False) / self.units_per_pallet, 6)

    @fields.depends('batch_quantity', 'batch_uom', 'units_per_mass',
        'product', '_parent_product.default_uom')
    def on_change_with_batch_masses(self, name=None):
        if (self.batch_quantity is not None and self.units_per_mass
                and self.batch_uom and self.product):
            Uom = Pool().get('product.uom')
            return round(Uom.compute_qty(self.batch_uom, self.batch_quantity,
                self.product.default_uom, round=False) / self.units_per_mass, 6)

    @fields.depends('product', '_parent_product.default_uom', 'batch_uom')
    def _quantity_from_batch(self, value, factor):
        if value is None:
            return None
        if not factor or not self.product or not self.batch_uom:
            raise UserError(gettext('production_batch.msg_missing_batch_conversion'))
        Uom = Pool().get('product.uom')
        return Uom.compute_qty(self.product.default_uom, value * factor,
            self.batch_uom)

    @fields.depends('batch_pallets', 'units_per_pallet',
        methods=['_quantity_from_batch', 'on_change_with_batch_masses'])
    def on_change_batch_pallets(self):
        self.batch_quantity = self._quantity_from_batch(
            self.batch_pallets, self.units_per_pallet)
        self.batch_masses = self.on_change_with_batch_masses()

    @fields.depends('batch_masses', 'units_per_mass',
        methods=['_quantity_from_batch', 'on_change_with_batch_pallets'])
    def on_change_batch_masses(self):
        self.batch_quantity = self._quantity_from_batch(
            self.batch_masses, self.units_per_mass)
        self.batch_pallets = self.on_change_with_batch_pallets()

    @classmethod
    def set_batch_equivalent(cls, records, name, value):
        factor_name = ('units_per_pallet' if name == 'batch_pallets'
            else 'units_per_mass')
        for record in records:
            if getattr(record, name) == value:
                continue
            cls.write([record], {'batch_quantity': record._quantity_from_batch(
                value, getattr(record, factor_name))})


class ProductionLeadTime(BatchMixin, metaclass=PoolMeta):
    __name__ = 'production.lead_time'
