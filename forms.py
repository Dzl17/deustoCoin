from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextField
from markupsafe import Markup

strEdit = '<span class="iconify" data-icon="ant-design:edit-filled" data-inline="false"></span>'
iconEdit = Markup(strEdit)
iconRm = Markup('<span class="iconify" data-icon="clarity:remove-solid" data-inline="false"></span>')
class EnviarUDCForm(FlaskForm):
    destino = StringField('Dirección del destinatario')
    cantidad = FloatField('Cantidad de UDCs a enviar')
    submit = SubmitField('Enviar')

class CrearAccionForm(FlaskForm):
    nomCamp = StringField('Nombre de la acción')
    empresa = StringField('Empresa proveedora')
    desc = TextField('Descripción')
    recompensa = FloatField('Recompensa (en UDC)')
    submit = SubmitField('Añadir acción')

class AccionesForm(FlaskForm):
    editar = SubmitField("✎")
    eliminar = SubmitField("✖")