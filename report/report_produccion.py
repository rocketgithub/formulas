# -*- encoding: utf-8 -*-

from openerp.osv import osv
from openerp.tools.translate import _
import logging

class ReporteProduccion(osv.AbstractModel):
    _name = 'report.fersuc.report_produccion'

    def lineas(self, o):
        grupos = {}
        i=0
        for ep in o.explosion_produccion:
            dato = {'producto':ep.producto.name, 'valor':ep.valor}
            if not grupos.has_key(ep.grupo.name):
                grupos[ep.grupo.name]={'grupo':ep.grupo.name,'productos':[dato]}
            else:
                prods = grupos[ep.grupo.name]['productos']
                prods.append(dato)
        logging.getLogger("GRUPOS").warn(grupos)
        result = grupos.values()
        logging.getLogger("LINEAS RESULT").warn(result)
        return result

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        explosion_obj = self.pool['fersuc.explosion']

        report = report_obj._get_report_from_name(cr, uid, 'fersuc.report_produccion')
        explosiones = explosion_obj.browse(cr, uid, ids, context=context)


        logging.getLogger("REPORTE").warn("ENTRO A RENDER HTML")
        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'data': data,
            'docs': explosiones,
            'lineas': self.lineas,
        }

        return report_obj.render(cr, uid, ids, 'fersuc.report_produccion', docargs, context=context)
