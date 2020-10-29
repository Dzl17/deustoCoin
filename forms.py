from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField

class EnviarUDCForm(FlaskForm):
    destino = StringField('Dirección del destinatario')
    cantidad = FloatField('Cantidad de UDCs a enviar')
    submit = SubmitField('Enviar')