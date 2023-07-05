from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError



class SamplePendingInvoice(models.Model):
    _name = "sample.pending.invoice"

    srf_id = fields.Many2one('lerm.civil.srf',string='SRF ID')
    kes_no = fields.Many2one('lerm.srf.sample',string='KES NO')
    material_id = fields.Many2one('product.template',string='Material')
    kes_date = fields.Date(string="KES Date")
    customer = fields.Many2one('res.partner',string="Customer")
    pricelist = fields.Many2one('product.pricelist',string='Pricelist')
    amount = fields.Float(string="Amount")
    invoiced = fields.Selection([
        ('invoice_pending', 'Invoice Pending'),
        ('invoiced', 'Invoiced'),
    ], 'Invocing Status', default='invoice_pending')

    def open_create_invoice_wizard(self):
        selected_records = self.filtered(lambda r: r.id in self.env.context.get('active_ids', []))
        if not selected_records:
            return False

        customers = selected_records.mapped('customer')
        if len(customers) != 1:
            raise ValidationError("Selected records must have the same customer.")
        action = self.env.ref('lerm_civil_inv_integration.create_invoice_wizard')
        return {
            'name': "Create Invoice",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.sample.invoice.wizard',
            'view_id': action.id,
            'target': 'new',
            'context':{
                "pending_invoice_ids":self.env.context.get('active_ids', [])
            }
            }


class CreateSampleInvoice(models.Model):
    
    _name = "create.sample.invoice.wizard"

    confirmation_message=fields.Char("Messge")

    def create_invoice(self):
        pending_invoices = self.env['sample.pending.invoice'].browse(self.env.context.get('pending_invoice_ids', []))
        invoice_material = pending_invoices.mapped('material_id')
        

        account_move_line = []

        for material in invoice_material:

            report_no = ""
            invoices_to_create = pending_invoices.filtered(lambda invoice: invoice.material_id == material)
    # Perform operations or create invoices for each material
            for invoice in invoices_to_create:
                # import wdb;wdb.set_trace()

                report_no += invoice.kes_no.kes_no+", "

                # Create invoice logic goes here
                # Example: invoice.create_invoice()
                print(f"Creating invoice for Material ID {material} and Invoice ID {invoice.id}")
            account_move_line.append((0,0,{'product_id': material.product_variant_ids.id,'report_no': report_no ,'price_unit': invoices_to_create[0].amount }))
        
        created_invoice = self.env["account.move"].sudo().create({
            'partner_id': pending_invoices[0].customer.id,
            'move_type':'out_invoice',
            'l10n_in_gst_treatment':'regular',
            'invoice_date': pending_invoices[0].kes_date,
            'journal_id':1,
            'currency_id': self.env.ref('base.INR'),
            'invoice_line_ids': account_move_line
        })

        pending_invoices.write({'invoiced':'invoiced'})

        return {'type': 'ir.actions.act_window_close'}

    def close(self):
        return {'type': 'ir.actions.act_window_close'}





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
                        'has_witness':sample.has_witness,
                        'size_id':sample.size_id.id,
                        'grade_id':sample.grade_id.id
                    })
                sample.write({'state':'2-alloted' , 'technicians':self.technicians.id})
                self.env['sample.pending.invoice'].sudo().create({
                        'srf_id': sample.srf_id.id ,
                        'kes_no':sample.id,
                        'material_id': sample.product_name.id,
                        'customer':sample.srf_id.customer.id,
                        'kes_date':sample.sample_received_date,
                        'amount':sample.price
                        })
            else:
                pass
            
         
        return {'type': 'ir.actions.act_window_close'}
