# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from decimal import Decimal

from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval, If


class Production(metaclass=PoolMeta):
    __name__ = 'production'

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

    @fields.depends('product', 'bom', 'routing', 'batch_uom',
        methods=['_set_batch_from_product_bom'])
    def on_change_product(self):
        super().on_change_product()
        if self.product and not self.batch_uom:
            self.batch_uom = self.product.default_uom
        self._set_batch_from_product_bom()

    @fields.depends('product', 'bom', 'batch_uom',
        methods=['_set_batch_from_product_bom'])
    def on_change_bom(self):
        super().on_change_bom()
        self._set_batch_from_product_bom()

    @fields.depends('product', 'bom', 'routing', 'batch_quantity', 'batch_uom')
    def _set_batch_from_product_bom(self):
        line = self._get_product_bom_line()
        if not line:
            self.batch_quantity = None
            if self.product:
                self.batch_uom = self.product.default_uom
            else:
                self.batch_uom = None
            return
        self.batch_quantity = line.batch_quantity
        self.batch_uom = line.batch_uom

    @fields.depends('product')
    def on_change_with_batch_uom_category(self, name=None):
        if self.product and self.product.default_uom_category:
            return self.product.default_uom_category.id

    @fields.depends('batch_uom')
    def on_change_with_batch_uom_digits(self, name=None):
        if self.batch_uom:
            return self.batch_uom.digits
        return 2

    def _get_product_bom_line(self):
        if not self.product:
            return
        if self.product.boms:
            return min(
                self.product.boms,
                key=lambda line: (
                    line.sequence if line.sequence is not None else float('inf'),
                    line.id or 0))

    @classmethod
    def validate(cls, productions):
        super().validate(productions)
        for production in productions:
            production.check_batch_multiple()

    def check_batch_multiple(self):
        if not (self.batch_quantity and self.batch_uom
                and self.quantity and self.unit):
            return
        Uom = Pool().get('product.uom')
        quantity = Decimal(str(Uom.compute_qty(
                    self.unit, self.quantity, self.batch_uom, round=False)))
        batch = Decimal(str(self.batch_quantity))
        remainder = quantity % batch
        tolerance = Decimal(str(self.batch_uom.rounding or 0.01)) / Decimal(10)
        distance = min(remainder, batch - remainder) if remainder else Decimal(0)
        if distance > tolerance:
            production_name = self.number or getattr(self, 'id', None) or '/'
            raise UserError(gettext(
                    'production_batch.msg_invalid_batch_multiple',
                    production=production_name,
                    quantity=self.quantity,
                    unit=self.unit.rec_name,
                    batch_quantity=self.batch_quantity,
                    batch_uom=self.batch_uom.rec_name))
