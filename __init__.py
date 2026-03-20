# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.pool import Pool

from . import product, production


def register():
    Pool.register(
        product.ProductBom,
        product.ProductionLeadTime,
        production.Production,
        module='production_batch', type_='model')
