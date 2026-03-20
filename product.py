# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

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


class ProductionLeadTime(BatchMixin, metaclass=PoolMeta):
    __name__ = 'production.lead_time'
