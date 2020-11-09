from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextField

class EnviarUDCForm(FlaskForm):
    destino = StringField('Dirección del destinatario')
    cantidad = FloatField('Cantidad de UDCs a enviar')
    submit = SubmitField('Enviar')

class CrearCampanaForm(FlaskForm):
    nomCamp = StringField('Nombre de la campaña')
    empresa = StringField('Empresa proveedora')
    desc = TextField('Descripción')
    recompensa = FloatField('Recompensa (en UDC)')
    submit = SubmitField('Añadir campaña')


