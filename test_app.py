from app import home
from flask import render_template

def test_home():
    assert home() == render_template("index.html")

def test_home(test_client, captured_templates):
    response = test_client.get("/")
    assert len(captured_templates) == 1
    template, context = captured_templates[0]
    assert template.name = "index.html"
