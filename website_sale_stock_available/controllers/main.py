# -*- encoding: utf-8 -*-
from openerp import http
from openerp.http import request
from openerp.addons.website_sale.controllers.main import website_sale


class WebsiteSale(website_sale):

    @http.route(['/shop/product/<model("product.template"):product>'],
                type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        cr, uid, context, pool = (request.cr, request.uid,
                                  request.context, request.registry)
        resp = super(WebsiteSale, self).product(product, category,
                                                search, **kwargs)

        settings_obj = pool.get('stock.config.settings')
        config_ids = settings_obj.search(cr, uid, [], limit=1,
                                         order='id DESC', context=context)
        if config_ids:
            stock_set = settings_obj.browse(cr, uid,
                                            config_ids[0], context=context)
            resp.qcontext['min_stock'] = stock_set.group_website_minimum_stock
        return resp
