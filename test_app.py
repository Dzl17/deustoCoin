from app import home
from flask import render_template

def test_home():
    assert index() == render_template("index.html")

