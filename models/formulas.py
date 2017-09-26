# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp

from toposort import toposort_flatten
import re
import logging

def calcular(operacion, atributos):
    result = 0
    if len(operacion.strip()) > 0:
        try:
            op = operacion.encode('ascii', 'ignore')
            result = eval(op, {}, atributos)
        except (SyntaxError, NameError):
            result = 0

    return result

class FormulasCategoria(models.Model):
    _name = 'formulas.categoria'
    _description = 'Categoria'

    name = fields.Char(string='Nombre', required=True)

class FormulasAtributo(models.Model):
    _name = 'formulas.atributo'
    _description = 'Atributo'
    _order = 'sequence'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Char(string='Descripcion')
    categoria_id = fields.Many2one('formulas.categoria', string='Categoria')
    tipo = fields.Selection([('valor','Valor'), ('opciones','Opciones'), ('calculado','Calculado'), ('rango','Rango')], string='Tipo', required=True)
    valor = fields.Float(string='Valor', digits=dp.get_precision('Product Unit of Measure'))
    opcion_ids = fields.One2many('formulas.atributo.opcion', 'atributo_id', string='Opcion')
    rango_ids = fields.One2many('formulas.atributo.rango', 'atributo_id', string='Rango')
    operacion = fields.Char(string='Nombre')

class FormulasAtributoOpcion(models.Model):
    _name = 'formulas.atributo.opcion'
    _description = 'Atributo Opcion'

    atributo_id = fields.Many2one('formulas.atributo', string='Atributo', required=True)
    codigo = fields.Char(string='Codigo', required=True)
    name = fields.Char(string='Nombre', required=True)
    valor = fields.Float(string='Valor', digits=dp.get_precision('Product Unit of Measure'))

class FormulasAtributoRango(models.Model):
    _name = 'formulas.atributo.rango'
    _description = 'Atributo Rango'

    atributo_id = fields.Many2one('formulas.atributo', string='Atributo', required=True)
    atributo_valor_id = fields.Many2one('formulas.atributo', string='Atributo', required=True, ondelete='restrict')
    inicial = fields.Float(string='Inicial', digits=dp.get_precision('Product Unit of Measure'), required=True)
    final = fields.Float(string='Final', digits=dp.get_precision('Product Unit of Measure'), required=True)
    atributo_resultado_id = fields.Many2one('formulas.atributo', string='Resultado', required=True, ondelete='restrict')

class FormulasGrupo(models.Model):
    _name = 'formulas.grupo'
    _description = 'Grupo'

    name = fields.Char(string='Nombre', required=True)

class FormulasCondicion(models.Model):
    _name = 'formulas.condicion'
    _description = 'Condicion'

    name = fields.Char(string='Nombre', required=True)
    tipo = fields.Selection([('and','Y'), ('or','O')], string='Tipo', required=True, default='and')
    grupo_id = fields.Many2one('formulas.grupo', string='Grupo')
    linea_ids = fields.One2many('formulas.condicion.linea', 'condicion_id', string='Linea')
    producto_ids = fields.One2many('formulas.condicion.producto', 'condicion_id', string='Productos')

class FormulasCondicionLinea(models.Model):
    _name = 'formulas.condicion.linea'
    _description = 'Condicion Linea'

    condicion_id = fields.Many2one('formulas.condicion', string='Condicion', required=True)
    atributo_id = fields.Many2one('formulas.atributo', string='Atributo', required=True, ondelete='restrict')
    operador = fields.Selection([('<','<'), ('>','>'), ('>=','>='), ('<=','<='), ('==','='), ('!=','!=')], string='Operador', required=True)
    valor = fields.Float(string='Valor', digits=dp.get_precision('Product Unit of Measure'))
    opcion = fields.Char(string='Opcion')

class FormulasCondicionProducto(models.Model):
    _name = 'formulas.condicion.producto'
    _description = 'Condicion Producto'

    condicion_id = fields.Many2one('formulas.condicion', string='Condicion', required=True)
    producto_id = fields.Many2one('product.product', string='Producto', required=True, ondelete='restrict')
    operacion = fields.Char(string='Operacion')
    instrucciones = fields.Char(string='Instrucciones')

class FormulasFormula(models.Model):
    _name = 'formulas.formula'
    _description = 'Formula'

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Char(string='Descripcion')
    producto_id = fields.Many2one('product.product', string='Producto', required=True, ondelete='restrict')
    condicion_ids = fields.Many2many('formulas.condicion', string='Elementos')

class FormulasComponente(models.Model):
    _name = 'formulas.componente'
    _description = 'Componente'

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Char(string='Descripcion')
    producto_id = fields.Many2one('product.product', string='Producto', required=True, ondelete='restrict')
    precio_id = fields.Many2one('formulas.atributo', string='Precio', required=True, ondelete='restrict')
    costo_por_precio = fields.Boolean(string='Multiplicar costo por atributo de precio')
    formula_ids = fields.Many2many('formulas.formula', string='Formula')
    predeterminado_ids = fields.One2many('formulas.componente.atributo', 'componente_id', string='Atributo Predeterminado')
    requerido_ids = fields.Many2many('formulas.atributo', string='Atributo Requerido')

class FormulasComponenteAtributo(models.Model):
    _name = 'formulas.componente.atributo'
    _description = 'Componente Atributo'

    componente_id = fields.Many2one('formulas.componente', string='Componente', required=True)
    atributo_id = fields.Many2one('formulas.atributo', string='Atributo', required=True, ondelete='restrict')
    valor = fields.Float(string='Valor', digits=dp.get_precision('Product Unit of Measure'))
    opcion = fields.Char(string='Opcion')

class FormulasExplosion(models.Model):
    _name = 'formulas.explosion'
    _description = 'Explosion'

    name = fields.Char(string='Nombre', required=True)
    componente_id = fields.Many2one('formulas.componente', string='Componente', required=True, ondelete='restrict')
    cantidad = fields.Float(string='Cantidad', digits=dp.get_precision('Product Unit of Measure'), default=1)
    atributo_ids = fields.One2many('formulas.explosion.atributo', 'explosion_id', string='Atributo')
    produccion_ids = fields.One2many('formulas.explosion.produccion', 'explosion_id', string='Produccion')
    valor_atributo_ids = fields.One2many('formulas.explosion.valor_atributo', 'explosion_id', string='Valor Atributo')

    @api.onchange('componente_id')
    def onchange_componente(self):
        atributos = []
        for a in self.componente_id.requerido_ids:
            atributos.append((0, 0, {
                'explosion_id': self.id,
                'atributo_id': a.id,
            }))

        self.atributo_ids = atributos

    def atributos(self):
        atributos = {}

        # Asignar todas las constantes
        for atributo in self.env['formulas.atributo'].search([('tipo','=','valor')]):
            atributos[atributo.name.encode('ascii', 'ignore')] = atributo.valor

        # Sobreescribir los valores con los ingresados en los componentes (linea de producción)
        for p in self.componente_id.predeterminado_ids:
            if p.atributo_id.tipo == 'opciones':
                valor = ""
                for opcion in [x for x in p.atributo.atributo_opcion if x.codigo == p.opcion]:
                    if opcion.valor != 0:
                        valor = opcion.valor
                    else:
                        valor = opcion.codigo

                atributos[p.atributo_id.name.encode('ascii', 'ignore')] = valor
            else:
                atributos[p.atributo_id.name.encode('ascii', 'ignore')] = p.valor

        # Sobreescribir los valores con los ingresados en la explosion
        for a in self.atributo_ids:
            if a.atributo_id.tipo == 'opciones':
                valor = ""
                for opcion in [x for x in a.atributo_id.opcion_ids if x.codigo == a.opcion]:
                    if opcion.valor != 0:
                        valor = opcion.valor
                    else:
                        valor = opcion.codigo
                atributos[a.atributo_id.name.encode('ascii', 'ignore')] = valor
            else:
                atributos[a.atributo_id.name.encode('ascii', 'ignore')] = a.valor

        # Generar listado de atributos para dependencias
        listado_ids = {}
        for atributo in self.env['formulas.atributo'].search([]):
            listado_ids[atributo.name.encode('ascii', 'ignore')] = atributo.id

        # Asignar dependencias
        dependencias = {}
        for atributo in self.env['formulas.atributo'].search([]):
            listado = set()
            if atributo.tipo == 'calculado':
                for a in re.split('[\+\-\*\/\(\)]', atributo.operacion):
                    token = a.strip().encode('ascii', 'ignore')
                    if len(token) > 0:
                        if token in listado_ids:
                            listado.add(listado_ids[token])

            elif atributo.tipo == 'rango':
                for r in atributo.rango_ids:
                    listado.add(r.atributo_resultado_id.id)

            dependencias[atributo.id] = listado

        ordenados = toposort_flatten(dependencias)

        for atributo in self.env['formulas.atributo'].browse(ordenados):

            # Asignar todos los calculados
            if atributo.tipo == 'calculado':
                atributos[atributo.name.encode('ascii', 'ignore')] = calcular(atributo.operacion, atributos)

            # Asignar todos los rangos
            if atributo.tipo == 'rango':
                for rango in atributo.rango_ids:
                    valor = atributos.get(rango.atributo_id.name, 0)
                    if rango.inicial <= valor and valor <= rango.final:
                        atributos[atributo.name.encode('ascii', 'ignore')] = atributos.get(rango.atributo_resultado_id.name, 0)

        self.valor_atributo_ids.unlink()

        nuevos_valores = []
        for a in sorted(atributos.keys()):
            nuevos_valores.append((0, 0, {'name': a, 'valor': atributos[a]}))
        self.valor_atributo_ids = nuevos_valores

        return atributos

    def producir(self):
        atributos = self.atributos()

        condiciones = []
        cantidad_explosion = 1

        componente = self.componente_id
        cantidad_explosion = self.cantidad
        for formula in self.componente_id.formula_ids:
            for condicion in formula.condicion_ids:
                condiciones.append([condicion, formula])

        self.produccion_ids.unlink()

        for condicion in condiciones:
            c = condicion[0]
            f = condicion[1]

            condiciones_string = []
            for cl in c.linea_ids:

                # Si un atributo de la condicion no esta en el dict, descartar condicion
                if not cl.atributo_id.name.encode('ascii', 'ignore') in atributos:
                    continue

                condicion = ""
                if cl.atributo_id.tipo == 'opciones':
                    condicion = "'"+str(atributos[cl.atributo_id.name.encode('ascii', 'ignore')])+"'" + cl.operador + "'"+str(cl.opcion)+"'"
                else:
                    condicion = str(atributos[cl.atributo_id.name.encode('ascii', 'ignore')]) + cl.operador + str(cl.valor)

                condiciones_string.append(condicion)

            union = " "+c.tipo+" "
            if len(condiciones_string) == 0 or eval(union.join(condiciones_string)):
                nuevos_productos = []

                for p in c.producto_ids:
                    valor_produccion = calcular(p.operacion, atributos)
                    nuevos_productos.append((0, 0, {'grupo_id': c.grupo_id.id, 'condicion_id': c.id, 'producto_id': p.producto_id.id, 'valor': valor_produccion * cantidad_explosion, 'instrucciones': p.instrucciones, 'formula_id': f }))

                self.produccion_ids = nuevos_productos

        return True

    def actualizar_precio(self):
        costo = 0
        precio = 1
        for produccion in self.produccion_ids:
            costo += produccion.producto_id.standard_price * produccion.valor

        if self.componente_id.costo_por_precio:
            for atributo in self.valor_atributo_ids:
                if atributo.name == self.componente_id.precio_id.name:
                    precio = float(atributo.valor)

        logging.warn(costo)
        logging.warn(precio)
        self.componente_id.producto_id.list_price = costo * precio
        return True

class FormulasExplosionAtributo(models.Model):
    _name = 'formulas.explosion.atributo'
    _description = 'Explosion Atributo'

    explosion_id = fields.Many2one('formulas.explosion', string='Explosion', required=True)
    atributo_id = fields.Many2one('formulas.atributo', string='Atributo', required=True, ondelete='restrict')
    valor = fields.Float(string='Valor', digits=dp.get_precision('Product Unit of Measure'))
    opcion = fields.Char(string='Opcion')

class FormulasExplosionProduccion(models.Model):
    _name = 'formulas.explosion.produccion'
    _description = 'Explosion Produccion'

    explosion_id = fields.Many2one('formulas.explosion', string='Componente', required=True)
    formula_id = fields.Many2one('formulas.formula', string='Formula', required=True, ondelete='restrict')
    producto_id = fields.Many2one('product.product', string='Producto', required=True, ondelete='restrict')
    grupo_id = fields.Many2one('formulas.grupo', string='Grupo')
    valor = fields.Float(string='Valor', digits=dp.get_precision('Product Unit of Measure'))
    instrucciones = fields.Char(string='Instrucciones')

class FormulasExplosionValorAtributo(models.Model):
    _name = 'formulas.explosion.valor_atributo'
    _description = 'Explosion Valor de Atributo'

    explosion_id = fields.Many2one('formulas.explosion', string='Componente', required=True)
    name = fields.Char(string='Nombre', required=True)
    valor = fields.Char(string='Valor')
