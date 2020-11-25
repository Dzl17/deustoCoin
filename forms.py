from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextAreaField
from markupsafe import Markup
from models import Campanya

strEdit = '<span class="iconify" data-icon="ant-design:edit-filled" data-inline="false"></span>'
iconEdit = Markup(strEdit)
iconRm = Markup('<span class="iconify" data-icon="clarity:remove-solid" data-inline="false"></span>')


class EnviarUDCForm(FlaskForm):
    destino = StringField('Dirección del destinatario')
    cantidad = FloatField('Cantidad de UDCs a enviar')
    submit = SubmitField('Enviar')


class CrearCampForm(FlaskForm):
    nomCamp = StringField('Nombre de la acción')
    empresa = StringField('Empresa proveedora')
    desc = TextAreaField('Descripción')
    submit = SubmitField('Añadir acción')

class CampanyasForm(FlaskForm):
    editar = SubmitField("✎")
    eliminar = SubmitField("✖")

class AccionesForm(FlaskForm):
    editar = SubmitField("✎")
    eliminar = SubmitField("✖")