from odoo import fields, models, api, exceptions
from dateutil.relativedelta import relativedelta
import datetime

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "This is a real estate offers training module"
    _order = "price desc"

    price = fields.Float()
    status = fields.Selection(copy=False, selection=[('accepted', 'Accepted'), ('refused', 'Refused')])
    partner_id = fields.Many2one("res.partner", required=True, string='Buyer')
    property_id = fields.Many2one("estate.property", required=True)
    property_type_id = fields.Many2one(related='property_id.property_type_id', store=True)

    validity = fields.Integer(default=7)
    date_deadline = fields.Date(compute='_compute_date_deadline', inverse='_inverse_date_deadline')

    @api.depends('validity')
    def _compute_date_deadline(self):
        for record in self:
            if not record.create_date is False:
                record.date_deadline = record.create_date + relativedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            if not (record.create_date is False or record.date_deadline is False):
                record.validity = (record.date_deadline - record.create_date.date()).days

    def accept(self):
        self.property_id.state = 'offer_accepted'
        self.status = 'accepted'
        self.property_id.selling_price = self.price
        self.property_id.partner_id = self.partner_id.id
        return True

    def refuse(self):
        self.status = 'refused'
        return True

    _sql_constraints = [
        ('check_price', 'CHECK(price > 0)', 'An offer price must be strictly positive')
        ]

    @api.model
    def create(self, vals):
        property_id = self.env['estate.property'].browse(vals['property_id'])
        property_id.state = 'offer_received'
        if len(property_id.offer_ids) > 0:
            if vals['price'] < max(property_id.offer_ids.mapped('price')):
                raise exceptions.UserError('Offer with a lower amount than an existing offer')
        return super().create(vals)
