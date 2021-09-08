from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextAreaField, FileField
from markupsafe import Markup

str_edit = '<span class="iconify" data-icon="ant-design:edit-filled" data-inline="false"></span>'
icon_edit = Markup(str_edit)
icon_rm = Markup('<span class="iconify" data-icon="clarity:remove-solid" data-inline="false"></span>')


class CustomFloatField(FloatField):
    """Allows to use commas along with dots to indicate decimals in a form."""
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = float(valuelist[0].replace(',', '.'))
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid float value'))


class SendUDCForm(FlaskForm):
    destiny = StringField('Correo electrónico del destinatario')
    quantity = CustomFloatField('Cantidad de UDCs a enviar')
    submit = SubmitField('Enviar')


class CreateCampaignForm(FlaskForm):
    campaign_name = StringField('Nombre de la campaña')
    company = StringField('Empresa proveedora')
    description = TextAreaField('Descripción')
    create_campaign = SubmitField('Crear campaña')


class CreateOfferForm(FlaskForm):
    offer_name = StringField('Nombre de la oferta')
    company = StringField('Organización')
    description = TextAreaField('Descripción')
    price = FloatField('Precio')
    create_offer = SubmitField('Crear oferta')


class CampaignsForm(FlaskForm):
    edit = SubmitField("✎")
    delete = SubmitField("✖")


class OffersForm(FlaskForm):
    edit = SubmitField("✎")
    delete = SubmitField("✖")


class ActionsForm(FlaskForm):
    edit = SubmitField("✎")
    delete = SubmitField("✖")


class ImageForm(FlaskForm):
    image = FileField('Imagen')
    submit = SubmitField('Enviar')
