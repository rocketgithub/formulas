# -*- encoding: utf-8 -*-

{
    'name': 'Produccion con Formulas',
    'version': '1.0',
    'category': 'Custom',
    'description': """
Produccion flexible usando formulas y atributos
""",
    'author': 'Luis Carlos Martinez y Rodrigo Fernandez',
    'website': 'http://solucionesprisma.com/',
    'depends': ['mrp'],
    'data': [
        'views/formulas_view.xml',
        'security/ir.model.access.csv',
        # 'views/sale_view.xml',
        # 'views/report.xml',
        # 'views/report_produccion.xml',
    ],
    'demo': [],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
