from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextAreaField, FileField
from markupsafe import Markup

strEdit = '<span class="iconify" data-icon="ant-design:edit-filled" data-inline="false"></span>'
iconEdit = Markup(strEdit)
iconRm = Markup('<span class="iconify" data-icon="clarity:remove-solid" data-inline="false"></span>')


class CustomFloatField(FloatField):
    """Allows to use commas along with dots to indicate decimals in a form."""
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = float(valuelist[0].replace(',', '.'))
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid float value'))


class EnviarUDCForm(FlaskForm):
    destino = StringField('Correo electrónico del destinatario')
    cantidad = CustomFloatField('Cantidad de UDCs a enviar')
    submit = SubmitField('Enviar')


class CrearCampForm(FlaskForm):
    nomCamp = StringField('Nombre de la campaña')
    empresa = StringField('Empresa proveedora')
    desc = TextAreaField('Descripción')
    crearCamp = SubmitField('Crear campaña')


class CrearOfertaForm(FlaskForm):
    nomOferta = StringField('Nombre de la oferta')
    empresa = StringField('Organización')
    desc = TextAreaField('Descripción')
    precio = FloatField('Precio')
    crearOf = SubmitField('Crear oferta')


class CampanyasForm(FlaskForm):
    editar = SubmitField("✎")
    eliminar = SubmitField("✖")


class OfertasForm(FlaskForm):
    editar = SubmitField("✎")
    eliminar = SubmitField("✖")


class AccionesForm(FlaskForm):
    editar = SubmitField("✎")
    eliminar = SubmitField("✖")


class ImageForm(FlaskForm):
    image = FileField('Imagen')
    submit = SubmitField('Enviar')
