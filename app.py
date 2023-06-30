#!/usr/bin/env python
# coding: utf-8

# In[1]:
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import dash
import dash_bootstrap_components as dbc
from dash import Dash
from dash import dcc, html, dash_table, Input, Output,State, callback
from dash.dash_table import DataTable, FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign, Symbol,Trim, Group

# Load the data
df = pd.read_csv('data/omni_extracted.csv')

#Transform the data - main table 
df.drop(['id'], axis=1, inplace=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['date'] = df['timestamp'].dt.date
df = df.sort_values(['address', 'date', 'timestamp'])
df = df.drop_duplicates(subset=['address', 'date'], keep='first')
df = df.round(3)
df_total_balance = df.groupby('date')['balance'].sum().reset_index()

#Find latest balances
latest_df = df.sort_values('date').drop_duplicates('address', keep='last')
total_balance = latest_df['balance'].sum()
latest_df['relative_weight'] = latest_df['balance'] / total_balance
latest_df = latest_df[['address', 'balance', 'relative_weight','date']]
latest_df = latest_df.round(3)
latest_df.sort_values(by='balance', ascending=False)


#Calculation of balance differences 
df_diff = df
df_diff['abs_diff'] = df_diff.groupby('address')['balance'].diff()
df_diff['rel_diff'] = df_diff.groupby('address')['balance'].pct_change()
df_diff['rel_diff'] = df_diff['rel_diff'].replace([np.inf, -np.inf], np.nan).fillna(0)
df_diff.sort_values(by='abs_diff', ascending=False)
df_pivot = df_diff.pivot(index='address', columns='date', values=['balance', 'abs_diff', 'rel_diff'])

#Find the changed addresses  

changes_found_df = df_diff[df_diff['abs_diff'] > 0] #['address'] #.unique()
#changes_found_df = df[df['address'].isin(addresses_with_abs_diff)]
changes_found_df = changes_found_df[['address', 'date', 'abs_diff', 'rel_diff']]
matching_addresses = changes_found_df['address'].tolist()

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([

    dbc.Row([dbc.Col(html.H1('Omni Agoras Balance Tracking',
                              className='text-center text-primary, mb-4'),
                              style={'marginTop': '20px', 'marginBottom': '20px'},
                      width=12)]),

    dbc.Row([

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5('Latest Balances', className='card-title'),
                    dash_table.DataTable(
                        id='latest_df',
                        columns=[
                            {"name": i, "id": i, 'deletable': False, 'selectable': True,
                             'type': 'numeric',
                             'format': Format(precision=3, scheme=Scheme.fixed)} if i=='balance' else 
                            {"name": i, "id": i, 'deletable': False, 'selectable': True,
                             'type': 'numeric',
                             'format': FormatTemplate.percentage(2)} if i=='relative_weight' else 
                            {"name": i, "id": i}
                            for i in latest_df.columns],
                        data=latest_df.to_dict('records'),
                        editable=False,
                        filter_action="native",
                        sort_action="native",
                        sort_by=[{'column_id':'balance', 'direction':'desc'}],
                        page_action="native",
                        page_current=0,
                        page_size=24,
                        style_cell={'textAlign': 'center', 'padding': '5px'},
                        style_cell_conditional=[{
                            'if': {'column_id': 'balance'},
                            'textAlign': 'right'}],
                        style_data_conditional=[{
                            'if': {'column_id': 'address', 
                                  'filter_query': '{{address}} = {}'.format(addr)},
                                 
                            'backgroundColor': 'rgba(255, 255, 0, 0.25)'  # or any other color#
                                    } for addr in matching_addresses
                                ],
                       
                        style_as_list_view=True,
                        style_header={'backgroundColor': 'white','fontWeight': 'bold'},
                        style_table={'height': '800px', 'overflowY': 'auto'},
                    ),
                ]),
            ], className='mb-4'),
        ], width=6),

        dbc.Col([
            dbc.Card([

                dbc.CardBody([
                    
                    html.H5("Balance Changes ", className='card-title'),
                    
                      dcc.Dropdown(
                        id='dropdown-time-filter',
                        options=[
                            {'label': 'Last 24h', 'value': '1D'},
                            {'label': 'Last 7 days', 'value': '7D'},
                            {'label': 'Last 30 Days', 'value': '1M'},
                            {'label': 'Last 90 Days', 'value': '3M'},
                            {'label': 'Last 6 Months', 'value': '6M'},
                            {'label': 'Last Year', 'value': '1Y'},
                        ],
                        placeholder="Select a time range",
                    ),
                    
                    dash_table.DataTable(
                        id='changes_found_df',
                            columns=[{"name":i,"id":i,'type':'numeric','format':FormatTemplate.percentage(2)} if i=='rel_diff' else {"name": i, "id": i} 
                                 for i in changes_found_df.columns],
                        data=changes_found_df.to_dict('records'),
                        style_cell={'textAlign': 'center', 'padding': '5px'},
                        style_data={'backgroundColor': 'rgba(255, 0, 0, 0.25)'},
                        style_data_conditional=[
                            {
                                'if': {'column_id': 'rel_diff'},
                                'textAlign': 'right'
                            }
                        ],
                        style_as_list_view=True,
                        style_header={'backgroundColor': 'white', 'fontWeight': 'bold'},
                        style_table={'overflowX': 'auto', 'maxHeight': '300px', 'overflowY': 'auto'},
                    ),
                ]), 
            ], className='mb-4'),
          
            dbc.Card([
                dbc.CardBody([
                    
                    html.H5("Balance Changes Over Time", className='card-title'),
                    
                    html.Button('Clear Selection', id='clear-button', n_clicks=0),
                    
                    dcc.Graph(id='line-chart')])
            ], className='mt-4')
        ], width=6)

    ], justify="around", align="start")  # Center and align to the top
])

@app.callback(
    Output('changes_found_df', 'data'),
    Input('dropdown-time-filter', 'value')
)
def update_table(time_range):
    if time_range:
        time_values = {'1D': 1, '7D': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365}
        num_days = time_values[time_range]

        # Assuming 'date' column is a string formatted as 'YYYY-MM-DD'
        changes_found_df['date'] = pd.to_datetime(changes_found_df['date'])
        cutoff_date = datetime.now() - timedelta(days=num_days)

        filtered_df = changes_found_df[changes_found_df['date'] > cutoff_date]
    else:
        # If no time range is selected, show all data
        filtered_df = changes_found_df

    return filtered_df.to_dict('records')


@app.callback(
    Output('line-chart', 'figure'),
    Input('changes_found_df', 'active_cell'),
     Input('latest_df', 'active_cell'),
     State('changes_found_df', 'data'),
     State('latest_df', 'data')
)
def update_line_chart(active_cell_changes, active_cell_latest, data_changes, data_latest):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'changes_found_df' and active_cell_changes and active_cell_changes['column_id'] == 'address':
        selected_address = data_changes[active_cell_changes['row']]['address']
    elif trigger_id == 'latest_df' and active_cell_latest and active_cell_latest['column_id'] == 'address':
        selected_address = data_latest[active_cell_latest['row']]['address']
    else:
        return create_figure(df_total_balance, 'Total Balance Over Time')

    df_selected = df[df['address'] == selected_address]
    return create_figure(df_selected, f'Balance for Address: {selected_address}')


def create_figure(df_selected, title):
    df_selected['date'] = pd.to_datetime(df_selected['date'])
    fig = px.line(df_selected, x='date', y='balance', title=title)
    fig.update_xaxes(tickangle=45, dtick="D1", tickformat="%d-%m-%Y")

    return fig
@app.callback(
    [Output('latest_df', 'active_cell'),
     Output('changes_found_df', 'active_cell')],
    [Input('clear-button', 'n_clicks')],
)
def clear_active_cells(n_clicks):
    if n_clicks > 0:
        return None, None  # reset active cells in both DataTables
    raise PreventUpdate  # no action if button was not clicked




if __name__ == '__main__':
    app.run_server(debug=False,host='0.0.0.0', port=8081)



# In[ ]:




