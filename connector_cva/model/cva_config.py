# -*- encoding: utf-8 -*-
from openerp import fields, models, api, _
import requests
from lxml import etree
import base64
#import ipdb


class cva_config(models.Model):
    _name = 'cva.config.settings'
    name = fields.Char(string='Client number')
    url = fields.Char(string='URL', default='http://www.grupocva.com/catalogo_clientes_xml/lista_precios.xml')
    allowed_groups = fields.Many2many('cva.group', string='Allowed groups')
    avialable = fields.Boolean(string='Get avialable products')
    avialable_dc = fields.Boolean(string='Get avialable products in Distribution Center')
    all_products = fields.Boolean(string='Get all products')

    @api.multi
    def connect_cva(self, params):
        """
            Connect to CVA web-services
            @param params: dict with parameters to generate xml file
            @return: returns a xml object
        """   
        data = requests.get(self.url, params=params).content
        root = etree.XML(data)
        return root

    @api.multi
    def get_groups(self):
        group = self.env['cva.group']
        group_list = [x.name for x in group.search([])]
        params = {'cliente': self.name}
        root = self.connect_cva(params)
        for item in root:
            if item.findtext('grupo') not in group_list:
                group.create({'name': item.findtext('grupo')})
                group_list.append(item.findtext('grupo'))
                
    @api.multi
    def create_product(self, item):
        product_obj = self.env['product.template']
        group_obj = self.env['cva.group']
        group = group_obj.search([('name', '=', item.findtext('grupo'))])
        if not item.findtext('imagen'):
            image = False
        else:
            image = base64.encodestring(requests.get(item.findtext('imagen')).content)
        if item.findtext('moneda') == 'Dolares':
            price = float(item.findtext('precio')) * float(item.findtext('tipocambio'))
        else:
            price = float(item.findtext('precio'))
        product_obj.create({'name': item.findtext('descripcion'),
                            'default_code': item.findtext('clave'),
                            'standard_price': price,
                            'description': _('Group\n' + item.findtext('grupo') + '\n\n' +
                                             'Subgroup\n' + item.findtext('subgrupo') + '\n\n' +
                                             'Ficha comercial\n' + item.findtext('ficha_comercial') +
                                             '\n\n' +
                                             'Ficha tecnica\n' + item.findtext('ficha_tecnica')),
                            'image_medium': image,
                            })

    @api.multi
    def update_product(self, item):
        product_obj = self.env('product.template')
        if item.findtext('moneda') == 'Dolares':
            price = float(item.findtext('precio')) * float(item.findtext('tipocambio'))
        else:
            price = float(item.findtext('precio'))
        product_obj.write({
                           'standard_price': price
                          })
    
    @api.one
    def get_products(self):
        product = self.env['product.template']
        group_list = []
        for x in self.allowed_groups:
            group_list.append(x.name)
        group_list = list(set(group_list))
        product_list = [x.default_code for x in product.search([])]
        for group in group_list:
            params = {'cliente': self.name,
                      'grupo': group,
                      'depto': '1',
                      'dt': '1',
                      'dc': '1',
                      'tc': '1',
                      'subgpo': '1',}
            root = self.connect_cva(params)
            for item in root:
                if item.findtext('clave') not in product_list:
                    if int(item.findtext('disponible')) > 0 and self.avialable == True:
                        self.create_product(item)
                    elif int(item.findtext('disponibleCD')) > 0 and self.avialable_dc == True:
                        self.create_product(item)
                    elif self.all_products == True:
                        self.create_product(item)


class cva_group(models.Model):
    _name = 'cva.group'
    _description = 'group of CVA'
    _order = 'name'
    
    name = fields.Char(required=True)
