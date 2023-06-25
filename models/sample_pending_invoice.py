from odoo import api, fields, models
from odoo.exceptions import UserError


class SamplePendingInvoice(models.Model):
    _name = "sample.pending.invoice"

    srf_id = fields.Many2one('lerm.civil.srf',string='SRF ID')
    kes_no = fields.Many2one('lerm.srf.sample',string='KES NO')
    customer = fields.Many2one('res.partner',string="Customer")
    pricelist = fields.Many2one('product.pricelist',string='Pricelist')
    amount = fields.Float(string="Amount")
    invoiced = fields.Selection([
        ('invoice_pending', 'Invoice Pending'),
        ('invoiced', 'Invoiced'),
    ], 'Invocing Status', default='invoice_pending')




class InheritedAllotmentWizard(models.TransientModel):
    _inherit = "sample.allotment.wizard"


    def allot_sample_inherited(self):
        # super(InheritedAllotmentWizard,self).allot_sample()
        # import wdb ; wdb.set_trace()
        # print("sdjksdkajsdhkjsadhkjsahkjsdkjasdkjbkjdasdnslkndlakndlka")
        active_ids = self.env.context.get('active_ids')
        for id in active_ids:
            parameters = []
            parameters_result = []
            sample = self.env['lerm.srf.sample'].sudo().search([('id','=',id)])
            if sample.state == '1-allotment_pending':
                for parameter in sample.parameters:
                    parameters.append((0,0,{'parameter':parameter.id ,'spreadsheet_template':parameter.spreadsheet_template.id}))
                    parameters_result.append((0,0,{'parameter':parameter.id,'unit': parameter.unit.id,'test_method':parameter.test_method.id}))
                    self.env['lerm.eln'].sudo().create({
                        'srf_id': sample.srf_id.id,
                        'srf_date':sample.srf_id.srf_date,
                        'kes_no':sample.kes_no,
                        'discipline':sample.discipline_id.id,
                        'group': sample.group_id.id,
                        'material': sample.material_id.id,
                        'witness_name': sample.witness,
                        'sample_id':sample.id,
                        'parameters':parameters,
                        'technician': self.technicians.id,
                        'parameters_result':parameters_result,
                        'conformity':sample.conformity,
                        'has_witness':sample.has_witness
                    })
                sample.write({'state':'2-alloted' , 'technicians':self.technicians.id})
                self.env['sample.pending.invoice'].sudo().create({'srf_id': sample.srf_id.id ,'kes_no':sample.id, 'customer':sample.srf_id.customer.id })
            else:
                pass
            
         
            return {'type': 'ir.actions.act_window_close'}
