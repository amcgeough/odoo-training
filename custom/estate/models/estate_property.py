from odoo import fields, models, api, exceptions, tools
from dateutil.relativedelta import relativedelta


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "This is a real estate training module"
    _order = "id desc"

    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(copy=False, default=fields.Date.today() + relativedelta(months=3) )
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
                selection=[('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West')]
                )
    active = fields.Boolean(default=True)
    state = fields.Selection(
                required=True, copy=False, default='new', string='Status',
                selection=[('new', 'New'), ('offer_received', 'Offer Received'), ('offer_accepted', 'Offer Accepted'), ('sold', 'Sold'), ('canceled', 'Canceled')]
                )

    property_type_id = fields.Many2one('estate.property.type')

    partner_id = fields.Many2one("res.partner", string="Buyer", copy=False)

    user_id = fields.Many2one("res.users", string="Salesperson", default=lambda self: self.env.user)

    tag_ids = fields.Many2many('estate.property.tag')

    offer_ids = fields.One2many('estate.property.offer', 'property_id')

    total_area = fields.Integer(compute="_compute_total_area")

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    best_price = fields.Float(compute="_compute_best_price")
    
    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            if record.offer_ids:
                record.best_price = max(record.offer_ids.mapped('price'))
            else:
                record.best_price = False

    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = False
            self.garden_orientation = False


    def cancel(self):
        if self.state == 'sold':
            raise exceptions.UserError('Sold properties cannot be cancelled')
        else:
            self.state = 'canceled'
        return True

    def sold(self):
        if self.state == 'canceled':
            raise exceptions.UserError('Cancelled properties cannot be sold')
        else:
            self.state = 'sold'
        return True

    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0)', 'A property expected price must be strictly positive'),
        ('check_selling_price', 'CHECK(selling_price > 0)', 'A property selling price must be strictly positive')
        ]

    @api.constrains('selling_price', 'expected_price')
    def _selling_price_pctg(self):
        for record in self:
            if not record.selling_price is False and not tools.float_is_zero(record.selling_price, precision_rounding=2):
                if tools.float_compare(record.selling_price, (record.expected_price * 0.9), precision_rounding=2) == -1:
                    raise exceptions.ValidationError("Selling price cannot be lower than 0.9 of the expected price")


    def unlink(self):
        for prop in self:
            if prop.state not in ('new', 'canceled'):
                raise exceptions.UserError('You can not delete a property unless new. You must first cancel it.')
        return super(EstateProperty, self).unlink()
    