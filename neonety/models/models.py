# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)


SEX_TYPES = [
	('Masculino',"Masculino"),
	('Femenino',"Femenino"),
]

def calculate_age(_birth_date):
	age = 0
	current_date = datetime.date.today()
	birth_date = datetime.datetime.strptime(_birth_date, '%Y-%m-%d').date()
	born = relativedelta(current_date,birth_date).years
	if born > 0:
		age = born
	return age


class NeonetyCountry(models.Model):
	_name = 'res.country'
	_inherit = 'res.country'
	province_ids = fields.One2many(
	    'neonety.province',
	    'country_id',
	    string='Provincias',
	    ondelete='cascade'
	)


class NeonetyProvince(models.Model):
	_name = 'neonety.province'
	code = fields.Char(
		string='Código',
		size=3,
		required=True,
		translate=True)
	name = fields.Char(
		string='Nombre',
		size=255,
		required=True,
		translate=True)
	country_id = fields.Many2one(
	    'res.country',
	    string='País',
	    required=False,
	    translate=True,
	    compute='_get_country_id',
	    store=True,
	    ondelete='cascade')
	district_ids = fields.One2many(
	    'neonety.district',
	    'province_id',
	    string='Distritos'
	)

	@api.depends('name')
	def _get_country_id(self):
		country = self.pool.get('res.country')
		country_id = self.env['res.country'].search([['name', '=', 'Panama']]).id
		self.country_id = country_id


class NeonetyDistrict(models.Model):
	_name = 'neonety.district'
	code = fields.Char(
		string='Código',
		size=3,
		required=True,
		translate=True)
	name = fields.Char(
		string='Nombre',
		size=255,
		required=True,
		translate=True)
	country_id = fields.Many2one(
	    'res.country',
	    string='País',
	    required=False,
	    translate=True,
	    compute='_get_country_id',
	    store=True)
	province_id = fields.Many2one(
	    'neonety.province',
	    string='Distrito',
	    required=False,
	    translate=True)
	sector_ids = fields.One2many(
	    'neonety.sector',
	    'district_id',
	    string='Corregimientos',
	)

	@api.depends('name')
	def _get_country_id(self):
		country = self.pool.get('res.country')
		country_id = self.env['res.country'].search([['name', '=', 'Panama']]).id
		self.country_id = country_id


class NeonetySector(models.Model):
	_name = 'neonety.sector'
	code = fields.Char(
		string='Código',
		size=3,
		required=True,
		translate=True)
	name = fields.Char(
		string='Nombre',
		size=255,
		required=True,
		translate=True)
	country_id = fields.Many2one(
	    'res.country',
	    string='País',
	    required=False,
	    translate=True,
	    compute='_get_country_id',
	    store=True)
	province_id = fields.Many2one(
	    'neonety.province',
	    string='Distrito',
	    required=False,
	    translate=True)
	district_id = fields.Many2one(
	    'neonety.district',
	    string='Distrito',
	    required=False,
	    translate=True)

	@api.depends('name')
	def _get_country_id(self):
		country = self.pool.get('res.country')
		country_id = self.env['res.country'].search([['name', '=', 'Panama']]).id
		self.country_id = country_id

class NeonetyPartnerConcept(models.Model):
	_name = 'neonety.partner.concept'
	name = fields.Char(
	    string='Concepto',
	    required=True,
	    translate=True)
	status = fields.Boolean(
	    string='Estatus',
	    required=True,
	    translate=True)


class NeonetyPartner(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'
	ruc = fields.Char(
	    string='RUC',
	    size=20,
	    required=False,
	    translate=True)
	dv = fields.Char(
	    string='DV',
	    size=2,
	    required=False,
	    translate=True)
	operation_notice_number = fields.Char(
	    string=' No. Aviso de Operación',
	    size=50,
	    required=False,
	    translate=True)
	partner_nationality = fields.Selection([
		('local', 'Local'),
		('extranjero', 'Extranjero')],
		string='Nacionalidad del cliente ó proveedor',
		required=False, translate=True)
	partner_type = fields.Selection([
		('natural', 'Persona natural (N)'),
		('juridica', 'Persona jurídica (J)'),
		('extranjero', 'Extranjero (E)')],
		string='Tipo de cliente ó proveedor',
		required=False, translate=True)
	neonety_partner_concept_id = fields.Many2one(
	    'neonety.partner.concept',
	    string='Concepto',
	    required=False,
	    translate=True)
	neonety_country_id = fields.Many2one(
	    'res.country',
	    string='País',
	    required=False,
	    translate=True,
	    default=lambda self: self._get_country_id())
	country_id = fields.Many2one(
	    'res.country',
	    string='País',
	    required=False,
	    translate=True,
	    default=lambda self: self._get_country_id())
	province_id = fields.Many2one(
	    'neonety.province',
	    string='Distrito',
	    required=False,
	    translate=True)
	district_id = fields.Many2one(
	    'neonety.district',
	    string='Distrito',
	    required=False,
	    translate=True)
	sector_id = fields.Many2one(
	    'neonety.sector',
	    string='Corregimiento',
	    required=False,
	    translate=True)
	street = fields.Char(
	    string='Dirección',
	    required=False,
	    translate=True)
	sex = fields.Selection(
		SEX_TYPES,
		string='Sexo',
		required=False,
		default=None)
	birth_date = fields.Date(
		string='Fecha de Nacimiento',
		required=False,
		default=None)
	age = fields.Char(
		string='Edad',
		required=False,
		compute='_calculate_age',
		default='0')

	@api.depends('birth_date')
	def _calculate_age(self):
		for record in self:
			record.age = '0'
			if record.birth_date:
				born = calculate_age(_birth_date=record.birth_date)
				if born > 0:
					record.age = '{0} año(s) de edad'.format(born)

	@api.onchange('birth_date')
	def _onchange_birth_date(self):
		self.age = '0'
		if self.birth_date:
			born = calculate_age(_birth_date=self.birth_date)
			if born > 0:
				self.age = '{0} año(s) de edad'.format(born)

	@api.model
	def _get_country_id(self):
		self._cr.execute("SELECT id FROM res_country WHERE code LIKE 'PA' LIMIT 1")
		country_id = self._cr.fetchone()
		return country_id

	@api.onchange('neonety_country_id')
	def onchange_neonety_country_id(self):
		res = {}
		if self.neonety_country_id:
			self._cr.execute('SELECT id, name FROM neonety_province WHERE country_id = %s', (self.neonety_country_id.id, ))
			provinces = self._cr.fetchall()
			ids = []

			for province in provinces:
				ids.append(province[0])
			res['domain'] = {'province_id': [('id', 'in', ids)]}
		return res

	@api.onchange('province_id')
	def onchange_province_id(self):
		res = {}

		if self.province_id:
			self._cr.execute('SELECT neonety_district.id, neonety_district.name FROM neonety_district WHERE neonety_district.province_id = %s AND neonety_district.country_id = ( SELECT neonety_province.country_id FROM neonety_province WHERE neonety_province.id = %s) ', (self.province_id.id, self.province_id.id))
			districts = self._cr.fetchall()
			ids = []

			for district in districts:
				ids.append(district[0])
			res['domain'] = {'district_id': [('id', 'in', ids)]}
		return res

	@api.onchange('district_id')
	def onchange_district_id(self):
		res = {}

		if self.district_id:
			self._cr.execute('SELECT neonety_sector.id, neonety_sector.name FROM neonety_sector WHERE neonety_sector.district_id = %s AND  neonety_sector.country_id = ( SELECT neonety_district.country_id FROM neonety_district WHERE neonety_district.id = %s) ', (self.district_id.id, self.district_id.id))
			sectors = self._cr.fetchall()
			ids = []

			for sector in sectors:
				ids.append(sector[0])
			res['domain'] = {'sector_id': [('id', 'in', ids)]}
		return res
