# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
import logging

class fersuc_generar_linea_pedido(osv.osv_memory):
    _name = 'fersuc.generar.linea.pedido'
    _description = 'Generar Linea'
    _columns = {
        'componente': fields.many2one('fersuc.componente', 'Componente', required=True),
        'atributo': fields.one2many('fersuc.generar.linea.pedido.atributo', 'generar_linea_id', 'Atributos'),
        'explosion': fields.many2one('fersuc.explosion', 'Explosion'),
        'pedido': fields.many2one('sale.order', 'Pedido'),
        'pricelist_id': fields.many2one('product.pricelist', 'Lista de Precios', required=True),
    }

    def onchange_componente(self, cr, uid, ids, componente, context=None):
        val = {}
        if not componente:
            return {'value': val}

        atributos = []
        componente = self.pool.get('fersuc.componente').browse(cr, uid, componente, context=context)
        for a in componente.componente_atributo_requerido:
            atributos.append( (0, 0, { 'atributo': a.id }) )

        val = { 'atributo': atributos }
        return { 'value': val }


    def calcular(self, cr, uid, ids, context=None):
        active_id = context and context.get('active_id', False)
        for gl in self.browse(cr, uid, ids, context=context):
            
            atributos = []
            for a in gl.atributo:
                atributos.append((0, 0, {'atributo': a.atributo.id, 'valor': a.valor, 'opcion': a.opcion.codigo}))
            logging.getLogger("PEDIDO").warn(str(active_id))
            explosion_id = self.pool.get('fersuc.explosion').create(cr, uid, {
                'name': "Pedido "+str(active_id),
                'componente': gl.componente.id,
                'cantidad': 1,
                'explosion_atributo': atributos
            }, context=context)

            self.pool.get('fersuc.explosion').producir(cr, uid, explosion_id, context=context)
            self.write(cr, uid, gl.id, {'explosion': explosion_id, 'pedido': active_id}, context=context)

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fersuc.generar.linea.pedido',
            'res_id': ids[0],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def agregar(self, cr, uid, ids, context=None):
        for gl in self.browse(cr, uid, ids, context=context):
            logging.getLogger("PEDIDO").warn(gl.pedido.name)
            for a in gl.explosion.valor_atributo:
                if a.name == 'AREA_PUERTA_DLA':
                    producto = gl.componente.producto
                    precio = self.pool.get('product.pricelist').price_rule_get_multi(cr, uid, gl.pricelist_id.id, products_by_qty_by_partner=[(producto, 1, gl.pedido.partner_id)], context=context)
                    logging.getLogger("PRECIO").warn(precio[producto.id][gl.pricelist_id.id][0])
                    self.pool.get('sale.order').write(cr, uid, gl.pedido.id, { 'order_line': [(0, 0, {
                        'name': producto.name,
                        'product_id': producto.id,
                        'price_unit': precio[producto.id][gl.pricelist_id.id][0] * float(a.valor),
                        'product_uom_qty': 1,
                        'product_uom': 1,
                        'explosion': gl.explosion.id,
                        'pricelist_id': gl.pricelist_id.id,
                    })] }, context=context)

        return

class fersuc_generar_linea_pedido_atributo(osv.osv_memory):
    _name = 'fersuc.generar.linea.pedido.atributo'
    _description = 'Generar Linea Atributo'

    def _get_opciones(self, cr, uid, context=None):
        logging.warn(self.atributo)
        return (('choice1', 'This is the choice 1'),
           ('choice2', 'This is the choice 2'))

    _columns = {
        'generar_linea_id': fields.many2one('fersuc.generar.linea.pedido', 'Generar Linea'),
        'atributo': fields.many2one('fersuc.atributo', 'Atributo', required=True),
        'valor': fields.float('Valor', digits=(12,3)),
        'opcion': fields.many2one('fersuc.atributo.opcion', 'Opcion'),
    }

class fersuc_linea_pedido(osv.osv_memory):
    _inherit = 'sale.order.line'

    _columns = {
        'explosion': fields.many2one('fersuc.explosion', 'Explosion'),
        'pricelist_id': fields.many2one('product.pricelist', 'Lista de Precios'),
        'condiciones_venta': fields.char('Condiciones de Venta'),
    }

class fersuc_pedido(osv.osv_memory):
    _inherit = 'sale.order'

    def copiar(self, cr, uid, ids, context=None):
        logging.getLogger("ENTRO COPIAR").warn(ids)
        logging.getLogger("ENTRO COPIAR").warn(uid)
        for data in self.browse(cr, uid, ids, context=context):
            logging.getLogger("ENTRO COPIAR").warn(data.id)
            logging.getLogger("ENTRO COPIAR").warn(data.pedidos_anteriores)
            c_id = self.copy(cr, uid, data.id, default=None, context=None)
            logging.getLogger("COPIA").warn(c_id)
            self.pool.get('sale.order').write(cr, uid, c_id, {'pedidos_anteriores': [(4,data.id)]}, context=context)
            for data2 in self.browse(cr, uid, c_id, context=context):
                logging.getLogger("ENTRO COPIAR data2").warn(data2.pedidos_anteriores)
#                self.write(cr, uid, data2.id, {'pedidos_anteriores': [(0,0,[data.id])]}, context=context)
#            self.pool.get('sale.order').write(cr, uid, c_id, {'pedidos_anteriores': [(4,data.id)]}, context=context)

    _columns = {
        'limite_credito': fields.boolean('Limite de Credito'),
        'cheque_rechazado': fields.boolean('Cheque Rechazado'),
        'cuenta_vencida': fields.boolean('Cuenta Por Cobrar Vencida'),
        'pedidos_anteriores': fields.many2many('sale.order', 'fersuc_sale_order_rel','order_id','anterior_id','Pedidos Anteriores'),
        'recibo_caja': fields.boolean('Recibo de Caja Depositado'),
        'dias_entrega': fields.integer('Días de Entrega'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
