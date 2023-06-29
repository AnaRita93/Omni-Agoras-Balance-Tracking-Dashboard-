#!/usr/bin/env python
# coding: utf-8

# In[1]:


import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd

# Load the data
df = pd.read_csv('data/omni_extracted.csv')
latest_balance = df.sort_values('timestamp').drop_duplicates('address', keep='last')
latest_balance = latest_balance[['address', 'balance', 'timestamp']]

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    html.H1('Omni Agoras Balance Tracking', className='mb-4 text-center'),

    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in latest_balance.columns],
        data=latest_balance.to_dict('records'),
        sort_action="native",
        filter_action="native",
        style_cell={'textAlign': 'left'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        }
    )
], className='mt-4')

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8081)







# In[ ]:




