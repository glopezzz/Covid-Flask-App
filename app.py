from flask import Flask, render_template, request, redirect
import scrpt
import random
from bokeh.models import (HoverTool, FactorRange, Plot, LinearAxis, Grid,
                          Range1d)
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/', methods=["POST","GET"])
def index():
    if request.method == "POST":
        if request.form.get("info_type") != None:
            scrpt.top_countries_comparisson(request.form.get("info_type"),request.form.get("order"),
                                            request.form.get("study_type"),int(request.form.get("n_countries")))
        elif request.form.get("n_countries_tests") != None:
            scrpt.top_countries_tests(int(request.form.get("n_countries_tests")),request.form.get("order_tests"))
        elif request.form.get("country") != None:
            scrpt.stringency_index(request.form.get("country"),request.form.get("reference"))     
        elif request.form.get("country") != None:
            scrpt.mobility(request.form.get("sectors"),request.form.get("country_mov"))
        elif request.form.get("numbers") != None:
            scrpt.numbers(request.form.get("numbers"))
        return redirect(request.url)
    else: 
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')