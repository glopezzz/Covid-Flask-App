import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy
import requests
from bs4 import BeautifulSoup
import requests
import io
from datetime import datetime
from bokeh.plotting import figure, output_file, show, ColumnDataSource
from bokeh.palettes import Category10
from bokeh.models import HoverTool

def plot_style(p):
    p.xaxis.major_label_orientation = 1.2
    p.legend.location="top_left"
    p.legend.click_policy="hide"
    p.yaxis.axis_label_text_font="helvetica"
    p.yaxis.axis_label_text_font_size="20px"
    p.yaxis.axis_label_text_font_style="normal"
    p.yaxis.axis_label_text_color="#000000"
    p.title.text_font = "helvetica"
    p.title.text_font_size = "20px"
    p.title.text_font_style = "normal"
    p.title.text_color = "#000000"
    p.title.align = 'center'


def get_daily_new(country):
    contador = 0
    country_data = copy.deepcopy(country)
    for i in country_data.index:
        country_data[i] = country_data[i]-contador
        contador += country_data[i]
    return country_data
    
def download_data(data_type):
    if data_type == "tests":
        url = "https://data.humdata.org/dataset/c87c4508-9caf-4959-bf06-6ab4855d84c6/resource/8c7d6af8-c703-4904-b5d0-0ab693e54ee4/download/covid-19-tests-country.csv" 
    elif data_type == "confirmed":
        url = "https://covid19tracking.narrativa.com/csv/confirmed.csv"
    elif data_type == "deaths":
        url = "https://covid19tracking.narrativa.com/csv/deaths.csv"
    elif data_type == "recovered":
        url = "https://covid19tracking.narrativa.com/csv/recovered.csv"
    elif data_type == "movility":
        url = "https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv?cachebust=57b4ac4fc40528e2"
    elif data_type == "gov_response":
        url = "https://oxcgrtportal.azurewebsites.net/api/CSVDownload"
    else: print("No such data, please read the index")
    s = requests.get(url).content
    return pd.read_csv(io.StringIO(s.decode('utf8')))

# Info_type: "confirmed" "deaths" "recovered"
# Order: "total" "per habitant"
# study_type: "accumulated" "new"
def top_countries_comparisson(info_type,order,study_type,n_countries):
    # Getting the countries populations number by web scrapping
    data = download_data(info_type)
    data.fillna("-",inplace=True)
    color_list = Category10[n_countries]
    output_file('chart.html')
    p = figure(
        x_axis_type="datetime",
        tools="pan,save,hover",
        plot_width=800,
        plot_height=600)

    if order=="per habitant":
        r = requests.get(r"https://www.worldometers.info/world-population/population-by-country/")
        soup = BeautifulSoup(r.text,"html.parser")
        body = soup.find("tbody")
        names = list()
        population = dict()
        for i in body:
            if type(i.find('a')) != int:
                if i.find('a').text == "United States":
                    names.append("US")
                elif i.find('a').text == "South Korea":
                    names.append("Korea, South")
                elif i.find('a').text == "Czech Republic (Czechia)":
                    names.append("Czechia")
                else:names.append(i.find('a').text)
    
        for j,i in enumerate(body.find_all('td',attrs={"style":"font-weight: bold;"})):
            population[names[j]]=(int(i.text.replace(",","")))
    
        # Dividing the Nº infections by every million citicens

        countries = data.loc[data["Region"]=="-",["Country_EN",data.columns[-1]]]
        index = list()
        for i in countries.index:
            if (countries["Country_EN"][i] in population.keys() and countries[data.columns[-1]][i]>5000):
                countries[data.columns[-1]][i] = countries[data.columns[-1]][i] / population[countries["Country_EN"][i]]
                index.append(i)
        plot_index=list()
        plot_index = countries.loc[index,data.columns[-1]].sort_values(ascending=False)[:n_countries].index
        
        # Plotting of n top infected countries per habitant
        for j,i in enumerate(plot_index):
            for fecha in data.columns[4:]:
                data.loc[i,fecha] = data.loc[i,fecha]/(population[data.loc[i,"Country_EN"]]/100000)
            source = ColumnDataSource(data={'Date': pd.to_datetime(data.columns[4:]),
                                            'Date_hover':data.columns[4:],
                                            'y_accum':data.loc[i,"2020-01-23":],
                                            'y_daily':get_daily_new(data.loc[i,"2020-01-23":])})
            if study_type == "accumulated":
                p.line('Date','y_accum',source=source,color=color_list[j],legend=data.loc[i,"Country_EN"],line_width=3)
                hover = p.select(dict(type=HoverTool))
                hover.tooltips = [("Date", "@Date_hover"),  ("Total "+info_type+" cases", "@y_accum{0}")]
                hover.mode = 'mouse'
            elif study_type == "new":
                p.line('Date','y_daily',source=source,color=color_list[j],legend=data.loc[i,"Country_EN"],line_width=3)
                hover = p.select(dict(type=HoverTool))
                hover.tooltips = [("Date", "@Date_hover"),  ("New "+info_type+" cases", "@y_daily{0}")]
                hover.mode = 'mouse'
        plot_style(p)
        p.title.text = 'Top '+str(n_countries)+" countries "
        if study_type == "accumulated":
            p.yaxis.axis_label = "Accumulated "+info_type+" cases per capita" 
        elif study_type == "new":
            p.yaxis.axis_label = "Daily new  "+info_type+" cases per capita" 

        return show(p)

    elif order == "total":
        for j,i in enumerate(data.loc[data["Region"]=="-",data.columns[-1]].sort_values(ascending=False)[:n_countries].index):
            source = ColumnDataSource(data={'Date': pd.to_datetime(data.columns[4:]),
                                            'Date_hover':data.columns[4:],
                                            'y_accum':data.loc[i,"2020-01-23":],
                                            'y_daily':get_daily_new(data.loc[i,"2020-01-23":])})
            if study_type == "accumulated":
                p.line('Date','y_accum',source=source,legend=data.loc[i,"Country_EN"],color=color_list[j],line_width=3)
                hover = p.select(dict(type=HoverTool))
                hover.tooltips = [("Date", "@Date_hover"),  ("Total "+info_type+" cases", "@y_accum{0}")]
                hover.mode = 'mouse'
            elif study_type == "new":
                p.line('Date','y_daily',source=source,legend=data.loc[i,"Country_EN"],color=color_list[j],line_width=3)
                hover = p.select(dict(type=HoverTool))
                hover.tooltips = [("Date", "@Date_hover"),  ("Total "+info_type+" cases", "@y_daily{0}")]
                hover.mode = 'mouse'

        plot_style(p)
        p.title.text = 'Top '+str(n_countries)+" countries "
        if study_type == "accumulated":
            p.yaxis.axis_label = "Accumulated "+info_type+" cases" 
        elif study_type == "new":
            p.yaxis.axis_label = "Daily new  "+info_type+" cases" 
        return show(p)

# study_type: "total" "per habitant"
def top_countries_tests(n_countries,study_type):
    tests = download_data("tests")
    tests.fillna("-",inplace=True)
    color = 'darkturquoise'
    output_file('chart.html')
    if study_type == "per habitant":
        r = requests.get(r"https://www.worldometers.info/world-population/population-by-country/")
        soup = BeautifulSoup(r.text,"html.parser")
        body = soup.find("tbody")
        names = list()
        population = dict()   
        for i in body:
            if type(i.find('a')) != int:    
                if i.find('a').text == "Czech Republic (Czechia)":
                        names.append("Czech Republic")
                else:names.append(i.find('a').text)
        for j,i in enumerate(body.find_all('td',attrs={"style":"font-weight: bold;"})):
            population[names[j]]=(int(i.text.replace(",","")))
        countries = tests.loc[tests["Code"]!="-",["Entity",tests.columns[-1]]]
        index = list()
        for i in countries.index:
            if countries["Entity"][i] in population.keys():
                countries[tests.columns[-1]][i] = countries[tests.columns[-1]][i] / (population[countries["Entity"][i]]/10000)
                index.append(i)
        plot_index = list()
        plot_index = countries.loc[index,tests.columns[-1]].sort_values(ascending=False)[:n_countries].index
        source = ColumnDataSource(data={'Country': tests.loc[plot_index,"Entity"],
                                        'Tests' : countries.loc[plot_index,tests.columns[-1]]})
        p = figure(
            x_range=tests.loc[plot_index,"Entity"],
            tools="pan,save,hover",
            plot_width=800,
            plot_height=600)
        p.vbar(x='Country',top='Tests',source=source,color=color,width=0.7)
        hover = p.select(dict(type=HoverTool))
        hover.tooltips = [("Country", "@Country"),  ("Tests Per Capita", "@Tests{0}")]
        hover.mode = 'mouse'
        plot_style(p)
        p.title.text = 'Top '+str(n_countries)+" countries "
        p.yaxis.axis_label = "Tests Per Capita"
        return show(p)

    elif study_type == "total":
        index = tests.loc[tests["Code"]!="-","Total COVID-19 tests"].sort_values(ascending=False)[:n_countries].index
        source = ColumnDataSource(data={'Country': tests.loc[index,"Entity"],
                                        'Tests' : tests.loc[index,"Total COVID-19 tests"]})
        p = figure(
            x_range=tests.loc[index,"Entity"],
            tools="pan,save,hover",
            plot_width=800,
            plot_height=600)
        p.vbar(x='Country',top='Tests',source=source, color=color, width=0.7)
        hover = p.select(dict(type=HoverTool))
        hover.tooltips = [("Country", "@Country"),  ("Tests", "@Tests{0}")]
        hover.mode = 'mouse'
        p.title.text = 'Top '+str(n_countries)+" countries "
        p.yaxis.axis_label = "Total Tests"
        plot_style(p)

        return show(p)

def stringency_index(country,reference):
    gov_response = download_data("gov_response")
    output_file('chart.html')
    for j in gov_response.loc[gov_response["CountryName"]==country,"Date"].index:
        gov_response.loc[j,"Date"] = datetime.strftime(datetime.strptime(str(gov_response.loc[j,"Date"]),"%Y%m%d"),"%Y-%m-%d")
    
    aux_name = country
    if country == "United States":
        aux_name = 'US'

    if reference == "confirmed":
        confirmed = download_data(reference)
        confirmed.fillna('-',inplace=True)

    if reference == "time":
        source = ColumnDataSource(data={'Date': pd.to_datetime(gov_response.loc[gov_response["CountryName"]==aux_name,"Date"]),
                            'Date_hover':gov_response.loc[gov_response["CountryName"]==country,"Date"],
                            'y':gov_response.loc[gov_response["CountryName"]==country,'StringencyIndex']})
        p = figure(
            x_axis_type="datetime",
            tools="pan,save,hover",
            plot_width=800,
            plot_height=600)
        p.line('Date','y',source=source,line_width=3)
        hover = p.select(dict(type=HoverTool))
        hover.tooltips = [("Date", "@Date_hover"),  ("Stringency Index", "@y{0}")]
        hover.mode = 'mouse'        
        plot_style(p)
        p.title.text = country+"'s government response vs time"
        p.yaxis.axis_label = "Stringency Index"  
        return show(p)

    elif reference == "confirmed":
        source = ColumnDataSource(data={
                            'Confirmed':confirmed.loc[(confirmed["Country_EN"]==aux_name) & (confirmed["Region"]=="-"),confirmed.columns[4:]].values[0],
                            'y':gov_response.loc[(gov_response["CountryName"]==aux_name) & (gov_response["Date"].isin(confirmed.columns[4:])),'StringencyIndex']})
        p = figure(
            tools="pan,save,hover",
            plot_width=800,
            plot_height=600)
        p.line('Confirmed','y',source=source,line_width=3)
        hover = p.select(dict(type=HoverTool))
        hover.tooltips = [("Confirmed Cases", "@Confirmed"),  ("Stringency Index", "@y{0}")]
        hover.mode = 'mouse'        
        plot_style(p)
        p.title.text = country+"'s government response vs confirmed cases"
        p.yaxis.axis_label = "Stringency Index" 
        return show(p)

def mobility(sectors, country):

    variables = ['retail_and_recreation_percent_change_from_baseline',
       'grocery_and_pharmacy_percent_change_from_baseline',
       'parks_percent_change_from_baseline',
       'transit_stations_percent_change_from_baseline',
       'workplaces_percent_change_from_baseline',
       'residential_percent_change_from_baseline']

    if "retail" not in sectors:
        variables.remove('retail_and_recreation_percent_change_from_baseline')
    elif "grocery" not in sectors:
        variables.remove('grocery_and_pharmacy_percent_change_from_baseline')
    elif "parks" not in sectors:
        variables.remove('parks_percent_change_from_baseline')
    elif "transit" not in sectors:
        variables.remove('transit_stations_percent_change_from_baseline')
    elif "workplaces" not in sectors:
        variables.remove('workplaces_percent_change_from_baseline')
    elif "residential" not in sectors:
        variables.remove('residential_percent_change_from_baseline')

def numbers(numbers):
    p = figure(
            tools="pan,save,hover",
            plot_width=800,
            plot_height=600)
    p.line(numbers,numbers,line_width=3)
    return show(p)
