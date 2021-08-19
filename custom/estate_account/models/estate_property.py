from odoo import fields, models, api, exceptions, tools


class EstatePropertyInherit(models.Model):
    _inherit = "estate.property"

    def sold(self):
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        self.env['account.move'].create({'partner_id': self.partner_id, 'move_type': 'out_invoice',  'journal_id': journal.id,
                                         "invoice_line_ids": [
                                                        (
                                                            0,
                                                            0,
                                                            {
                                                                "name": self.name,
                                                                "quantity": "1",
                                                                "price_unit": self.selling_price*0.06
                                                            },
                                                        ),
                                                        (
                                                            0,
                                                            0,
                                                            {
                                                                "name": "Administrative Fees",
                                                                "quantity": "1",
                                                                "price_unit": "100.00"
                                                            },
                                                        ),
                                                    ],
                                        })

        return super().sold()
    