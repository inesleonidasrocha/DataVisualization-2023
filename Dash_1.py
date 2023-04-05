from typing import Union, Any

import dash
import pandas as pd
import plotly.express as px
from dash import dcc
from dash import html
import plotly.graph_objects as go
import numpy as np
from pandas import DataFrame
import json
from plotly.subplots import make_subplots

# Load the treated dataset
data = pd.read_csv('todos_v1.csv')



def create_scatter_plot(city_name, data):
    # Filtering the dataframe to only show the row that corresponds to the city selected
    dados_distrito = data.loc[data['Distrito'] == city_name]

    # Create a scatter plot trace for dados_distrito
    trace = dict(type='scatter',
                 y=dados_distrito['Preço'],
                 x=dados_distrito['Dimensão m2'],
                 text=dados_distrito['Tipo'],
                 mode='markers')

    data = [trace]

    # Defining the layout
    layout = dict(title=dict(text='Relação Preço Vs Dimensão das casas em m2: ' + city_name),
                  xaxis=dict(title='Dimensão m2'),
                  yaxis=dict(title='Preço'))

    # Create the figure
    fig = go.Figure(data=data, layout=layout).update_layout(
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)'
                            )

    # Return the scatter plot as a dcc.Graph object
    return dcc.Graph(id='scatter-plot', figure=fig)

def create_sun_plot(city_name,data):#,type):
    dados_distrito = data.loc[(data['Distrito'] == city_name)]#&(data['Tipo'] == type)]
    figure=px.sunburst(dados_distrito, path=['Tipo', 'Condição']).update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)')

    # Return the scatter plot as a dcc.Graph object
    return dcc.Graph(id='scatter-plot', figure=figure)


# Create the footer with authors and sources information
footer_layout = html.Div(
    [
        html.P("Authors: John Doe, Jane Smith, Jackie Doe"),
        html.P("Sources: imovirtual, google maps, ..."),
    ],
    style={'background-color': '#f2f2f2', 'padding': '10px'}
)

#------------------------------
#CODE FOR THE BAR AND LINE PLOTS
# group by district and count the number of ads
ads_per_district = data.groupby('Distrito').size().reset_index(name='Count')

# group by district and calculate the mean price
mean_price_per_district = data.groupby('Distrito')['Preço'].mean().reset_index(name='MeanPrice')

# sort by count in descending order
ads_per_district = ads_per_district.sort_values('Count', ascending=False)

# create a figure with two subplots
fig33 = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.05)

# add the bar chart for number of ads
fig33.add_trace(go.Bar(x=ads_per_district['Count'], y=ads_per_district['Distrito'], orientation='h', name='Number of houses listed'), row=1, col=1)

# add the line chart for mean price
mean_price_per_district = mean_price_per_district.set_index('Distrito') # set index to district for easy indexing
mean_price_per_district_sorted = mean_price_per_district.loc[ads_per_district['Distrito']] # sort by the sorted index
fig33.add_trace(go.Scatter(x=round(mean_price_per_district_sorted['MeanPrice'],2), y=ads_per_district['Distrito'], mode='lines+markers', name='Average House Price'), row=1, col=2)

# update the layout
fig33.update_layout(title='House listings and Average price per district', height=500, width=600, xaxis2_tickprefix="€", xaxis2_tickformat=',',xaxis1_tickformat=',',
                  yaxis=dict(title='City', autorange='reversed', showgrid=False, showline=False, showticklabels=True, tickfont=dict(size=8), tickangle=0),
                  xaxis=dict(showgrid=False, showline=False, showticklabels=True, range=[0, max(ads_per_district['Count'])+1000]),
                  xaxis2=dict(showgrid=False, showline=False, showticklabels=True, range=[0, max(mean_price_per_district['MeanPrice'])+20000]),
                  legend=dict(orientation='h', yanchor='top', y=-0.03, xanchor='center', x=0.459),
                #ve destas cores
                  margin=dict(l=50, r=50, t=50, b=50), font=dict(size=10),plot_bgcolor='rgba(233,227,234,20)',
                    paper_bgcolor='rgba(0,0,0,0)')

#------------------------------

#-----------------------------------------------------
#CODE FOR THE MAPPPP
# Load topojson data
with open('portugal-freg.geojson') as f:
    geojson_data = json.load(f)

# convert geojson into dataframe
df_geojson = pd.json_normalize(geojson_data['features'])
# Define a function to split the Localidade column
def split_localidade(localidade):
    if localidade.count(',') == 2:
        freguesia = localidade.split(',')[0].strip()
        concelho = localidade.split(',')[1].strip()
        distrito = localidade.split(',')[2].strip()

    elif localidade.count(',') == 1:
        freguesia = localidade.split(',')[0].strip()
        concelho = localidade.split(',')[0].strip()
        distrito = localidade.split(',')[1].strip()

    elif localidade.count(',') == 0:
        freguesia = localidade.strip()
        concelho = localidade.strip()
        distrito = localidade.strip()

    elif localidade.count(',') >= 3:
      freguesia = localidade.rsplit(',', 2)[0].strip()
      concelho = localidade.rsplit(',', 2)[1].strip()
      distrito = localidade.rsplit(',', 2)[2].strip()

    return pd.Series([freguesia, concelho, distrito], index=['Freguesia', 'Concelho', 'Distrito'])
# Apply the function to the 'Localidade' column of the dataframe
data[['Freguesia', 'Concelho', 'Distrito']] = data['Localidade'].apply(split_localidade)
mean_price_per_freg = data.groupby(['Distrito','Concelho', 'Freguesia'])['Preço'].mean().reset_index(name='MeanPrice')
merged_data = pd.merge(df_geojson, mean_price_per_freg, left_on='properties.NAME_3', right_on='Freguesia', how='left')
fig_map = px.choropleth(merged_data, geojson=geojson_data, color='MeanPrice',
                    locations='Freguesia', featureidkey='properties.NAME_3',
                    color_continuous_scale='algae', range_color=(160000, 1300000),
                    labels={'MeanPrice': 'Preço Médio de Compra'})
fig_map.update_geos(fitbounds="locations", visible=False)

fig_map.update_layout(
    height=600,
    width=800,
    geo=dict(
        lonaxis=dict(
            range=[-10.0, -5.0]
        ),
        lataxis=dict(
            range=[36.0, 42.0]
        ),
        projection_scale=1.5
    )
)
#----------------------------------------------------
# Create a basic layout
app = dash.Dash('House Prices')
app.config.suppress_callback_exceptions=True
app.layout = html.Div(
    style={'backgroundColor': '#d4ffc1',
           'width': '500mm',
           'height': '297mm',
           'fontFamily': 'Open Sans Light'},
    children=[
        html.Div(
            style={'textAlign': 'center',
                   'marginTop': '20px'},
            children=[html.H1(children='House Prices Analysis for Portugal')]
        ),
        html.Div(
            style={'display': 'flex'},
            children=[
                html.Div(
                    style={'flex': 1}),
                html.Div(dcc.Graph(id='hello', figure=fig_map)),
                html.Div(
                    style={'flex': 2},
                    children=[
                        html.Div(
                            children=[
                                html.Div(dcc.Graph(id='fig33', figure=fig33)),
                                html.Label('Select a city:'),
                                dcc.Dropdown(
                                    id='city-dropdown',
                                    options=[{'label': city, 'value': city} for city in data['Distrito'].unique()],
                                    value='Lisboa'
                                ),
                                html.Div(
                                    style={'display': 'flex'},
                                    children=[
                                        html.Div(
                                            style={'flex': 1},
                                            children=[html.Div(id='scatter-plot-div', style={'width': '150mm', 'height':'100mm'})]
                                        ),
                                        html.Div(
                                            style={'flex': 1},
                                            children=[html.Div(id='sun-plot-div', style={'width': '150mm', 'height':'100mm'})]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                html.Div(style={'flex': 1}),
            ]
        ),
        html.Div(
            style={'textAlign': 'center',
                   'marginTop': '20px'},
            children=[html.P(children='Data Visualization project')]
        ),
        footer_layout
    ]
)







#------------------------------------

@app.callback(
    dash.dependencies.Output('scatter-plot-div', 'children'),
    dash.dependencies.Output('sun-plot-div', 'children'),
    [dash.dependencies.Input('city-dropdown', 'value')]
)
def update_plots(city_name):
    scatter_plot = create_scatter_plot(city_name, data)
    sun_plot = create_sun_plot(city_name, data)
    return scatter_plot, sun_plot


if __name__ == '__main__':
    app.run_server(debug=True)




