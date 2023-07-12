#!/usr/bin/env python
# coding: utf-8

# In[1]:
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

import dash
import dash_bootstrap_components as dbc
from dash import Dash
from dash import dcc, html, dash_table, Input, Output,State, callback
from dash.dash_table import DataTable, FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign, Symbol,Trim, Group


def create_figure(df, title):
    fig = px.line(df, x="date", y="balance", title=title,
    labels={"date": "Date","balance": "Balance"},
    template='plotly_white')
    
    # Add markers and increase the line width
    fig.update_traces(mode='lines+markers', line=dict(width=2)),
    fig.update_xaxes(tickangle=45, dtick="D1", tickformat="%d-%m-%Y")
        
    return fig

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Load the data
df = pd.read_csv('data/omni_extracted.csv')

#Transform the data - main table 
df.drop(['id'], axis=1, inplace=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['date'] = df['timestamp'].dt.date
#df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['address', 'date', 'timestamp'])
df = df.drop_duplicates(subset=['address', 'date'], keep='first')
df = df.round(3)
df_total_balance = df.groupby('date')['balance'].sum().reset_index()

#Find latest balances
latest_df = df.sort_values('date').drop_duplicates('address', keep='last')

## Flag Balances with empty wallets 
#majority_date = latest_df['date'].value_counts().idxmax()
#majority_date = pd.to_datetime(latest_df['date'].mode()[0])
#latest_df.loc[latest_df['date'] < majority_date, 'balance'] = 0

majority_date = pd.to_datetime(latest_df['date'].mode()[0])
majority_date = pd.Timestamp(majority_date)
latest_df.loc[latest_df['date'].apply(pd.Timestamp) != majority_date, 'balance'] = 0

## Calculate each address contribution  
total_balance = latest_df['balance'].sum()
latest_df['percentage'] = latest_df['balance'] / total_balance
latest_df = latest_df.round(3)

## Attribute Labels to addresses 
latest_df['label']= ''
address_labels = {
    '14gF3Up7wdRdkxAL4GgQLdnM8CThgDUSHR': 'ICO Wallet',
    '1DUb2YYbQA1jjaNYzVXLZ7ZioEhLXtbUru': 'Bittrex',
    '1KGv7PL3zz5CE5jz1dtFnauMJHJLkKjXAE': 'BCEX',
    '1vxQFvJ8k6cQzNxdo7cBwCHyNwFhRLN1M': 'Whitebit',
    
}
latest_df['label'] = latest_df['address'].map(address_labels)

## Final formating of latest_df 
latest_df = latest_df[['address', 'balance', 'percentage','label','date']]
latest_df = latest_df.sort_values(by='balance', ascending=False)
latest_df = latest_df.reset_index(drop=True)

#Calculation of balance differences 
df_diff = df
df_diff['abs_diff'] = df_diff.groupby('address')['balance'].diff()
df_diff['rel_diff'] = df_diff.groupby('address')['balance'].pct_change()
df_diff['rel_diff'] = df_diff['rel_diff'].replace([np.inf, -np.inf], np.nan).fillna(0)
df_diff.sort_values(by='abs_diff', ascending=False)
df_pivot = df_diff.pivot(index='address', columns='date', values=['balance', 'abs_diff', 'rel_diff'])

#Find the changed addresses  

changes_found_df = df_diff[(df_diff['abs_diff'] > 0) |(df_diff['abs_diff'] < 0)] #['address'] #.unique()
changes_found_df = changes_found_df[['address', 'date', 'abs_diff', 'rel_diff']]
matching_addresses = changes_found_df['address'].tolist()

merged_df = pd.merge(changes_found_df, latest_df[['address', 'balance', 'percentage']], on='address', how='left')
merged_df = merged_df.sort_values(by=['date'])
merged_df = merged_df[['address','date', 'abs_diff','rel_diff','balance', 'percentage']]
merged_df = merged_df.rename(columns={"date":"date", 
                                      'abs_diff':'absolute_diff',
                                      'rel_diff':'relative_diff',
                                      "balance": "current balance", 
                                      "percentage": "balance weight"})
merged_df['relative_diff']= merged_df['relative_diff'].round(3)
changes_found_df = merged_df

app.layout = dbc.Container([
    

    dbc.Row([dbc.Col(html.H1('Omni Agoras Balance Tracking',
                              className='text-center text-primary, mb-4'),
                              style={'marginTop': '20px', 'marginBottom': '20px'},
                      width=12)]),
    dcc.Store(id='selected-address'),

    dbc.Row([

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5('Latest Balances', className='card-title'),
                    
                    dcc.Graph(id='pie-chart'),
                    
                    dash_table.DataTable(
                        id='latest_df',
                        columns=[
                            {"name": i, "id": i, 'deletable': False, 'selectable': True,
                             'type': 'numeric',
                             'format': Format(precision=3, scheme=Scheme.fixed)} if i=='balance' else 
                            {"name": i, "id": i, 'deletable': False, 'selectable': True,
                             'type': 'numeric',
                             'format': FormatTemplate.percentage(2)} if i=='percentage' else 
                            {"name": i, "id": i}
                            for i in latest_df.columns],
                        data=latest_df.to_dict('records'),
                        editable=False,
                        filter_action="native",
                        #sort_action="native",
                        #sort_by=[{'column_id':'balance', 'direction':'desc'}],
                        page_action="none",
                        page_current=0,
                        page_size=24,
                        #row_selectable="multi",  
                        #selected_rows=[],  
                        style_cell={'textAlign': 'center', 'padding': '5px', 'width': '50px', 'minWidth': '30px', 'maxWidth': '250px', 'overflow': 'hidden'},
                        style_cell_conditional=[{
                            'if': {'column_id': 'balance'},
                            'textAlign': 'right'}],
                        style_data ={'width': '50px', 'minWidth': '30px', 'maxWidth': '250px', 'overflow': 'hidden'},
                        style_data_conditional=[{
                            'if': {'column_id': 'address', 
                                  'filter_query': '{{address}} = {}'.format(addr)},
                                 
                            'backgroundColor': 'rgba(255, 255, 0, 0.25)'  # or any other color#
                                    } for addr in matching_addresses
                                ],
                       
                        style_as_list_view=True,
                        style_header={'backgroundColor': 'white','fontWeight': 'bold'},
                        style_table={'height': '400px', 'overflowY': 'auto'},
                    ),
                ]),
            ], className='mb-4'),
        ],width=6),

        dbc.Col([
            dbc.Card([

                dbc.CardBody([
                    
                    html.H5("Balance Changes ", className='card-title'),
                    html.P('Please select a time frame'),
                    
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
                    
                    html.P('Please click on an address from Latest Balances table (on the left).'),
                    
                    html.Button('Clear Selection', id='clear-button', n_clicks=0),
                    
                    dcc.Graph(id='line-chart')])
            ], className='mt-4')
        ], width=6)

    ], justify="around", align="start")  # Center and align to the top
    
],fluid=True, style={'max-width': '90%'})

@app.callback(
    Output('pie-chart', 'figure'),
    Input('latest_df', 'data')
)
def update_pie_chart(data):
    latest_df = pd.DataFrame(data)
    fig = go.Figure(data=[go.Pie(labels=latest_df['address'], values=latest_df['balance'], hole=.3, hoverinfo='label+percent+value', textinfo='none')])
    fig.update_layout(showlegend=False, title_text='Relative Weights of Addresses')
    return fig


@app.callback(
    Output('changes_found_df', 'data'),
    Input('dropdown-time-filter', 'value')
)
def update_table(time_range):
    if time_range:
        time_values = {'1D': 1, '7D': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365}
        num_days = time_values[time_range]
        changes_found_df['date'] = pd.to_datetime(changes_found_df['date'])
        cutoff_date = datetime.now() - timedelta(days=num_days)

        filtered_df = changes_found_df[changes_found_df['date'] > cutoff_date]
    else:
        filtered_df = changes_found_df

    return filtered_df.to_dict('records')

@app.callback(
    Output('selected-address', 'data'),
    Input('latest_df', 'active_cell'),
    Input('changes_found_df', 'active_cell'),
    Input('clear-button', 'n_clicks'),
    State('latest_df', 'data'),
    State('changes_found_df', 'data'))
def update_selected_address(active_cell_latest, active_cell_changes, n_clicks, data_latest, data_changes):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Overall Balance"
    else:
        input_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if input_id == 'clear-button':
            return "Overall Balance"
        elif input_id == 'latest_df':
            if active_cell_latest and active_cell_latest['column_id'] == 'address':
                return data_latest[active_cell_latest['row']]['address']
        elif input_id == 'changes_found_df':
            if active_cell_changes and active_cell_changes['column_id'] == 'address':
                return data_changes[active_cell_changes['row']]['address']

@app.callback(
    Output('line-chart', 'figure'),
    Input('selected-address', 'data'),
)
def update_line_chart(selected_address):
    if selected_address == "Overall Balance":
        return create_figure(df_total_balance, 'Total Balance Over Time')

    df_selected = df[df['address'] == selected_address]
    
    return create_figure(df_selected, f'Balance for Address: {selected_address}')


            
if __name__ == '__main__':
    app.run_server(debug=True,host='144.91.121.7', port=8081)



# In[ ]:




