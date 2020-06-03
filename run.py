import json
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask
import os


server = Flask(__name__)
server.secret_key = os.environ.get('secret_key', 'secret')
app = dash.Dash(name = __name__, server = server)
#app.config.supress_callback_exceptions = True

path='europe.geojson'
with open(path) as json_file:
    europe = json.load(json_file)

path='hlth_cd_asdr2_1_Data.xlsx'   
dfEurostat = pd.read_excel(path)

path='ICD10.xlsx'
dfICD10=pd.read_excel(path)

path='Population.xlsx'
dfPopulation=pd.read_excel(path)

dfEurostat=pd.merge(dfEurostat,dfICD10,how='left',on='ICD10')


def ValuePop(year,country,value):
    pop=dfPopulation[str(year)].loc[dfPopulation['GEO/TIME']==country].item()
    death_toll=value*pop/100000
    return death_toll

dfTot=dfEurostat.loc[(dfEurostat['SEX']=='Total') &
                 (dfEurostat['AGE']=='Total')]

dfTot["Death_Toll"] = dfTot.apply(lambda x: ValuePop(x['TIME'], x['GEO'], 
                                                     x['Value']), axis = 1)


listeClasseMort=[]
ClasseMortUnique=dfICD10['Classe_mortalité'].unique()[2:]
ClasseMortUnique.sort()
for i in ClasseMortUnique:
    listeClasseMort.append({'label': i, 'value': i})

app.layout = html.Div([
                html.Section([
                    html.H3("Critères d'entrée"),
                    html.Hr(),
                    html.Br(),
                    html.Label('Cause de mortalité'),
                    dcc.Dropdown(
                        id='cause-dropdown',
                        options=listeClasseMort
                    ),
                    
                    html.Br(),
                    
                    dcc.RadioItems(
                        id='rate-number-radio',
                        options=[
                            {'label': 'Taux de mortalité', 'value': 'Death_Rate'},
                            {'label': 'Nombre de morts', 'value': 'Death_Toll'}
                        ],
                        value='Death_Toll'),
                    
                    html.Br(),
                    
                    html.Label('Année'),
                    dcc.Slider(
                        id='year-slider',
                        min=dfTot['TIME'].unique().min(),
                        max=dfTot['TIME'].unique().max(),
                        marks=pd.DataFrame(dfTot['TIME'].unique().astype(str), 
                                    index=dfTot['TIME'].unique()).to_dict()[0]
                        #formatage afin d'avoir un dictionnaire avec un format int, seul valable
                    )
                ],className='background2'),
                            
                html.Div([
                    html.Div([
                        html.Div(
                            dcc.Graph(id='graph'),className='width50'),
                        html.Div(
                            dcc.Graph(id='sex-pie-charts'),
                                className='width50')
                    ],className='row'),
                    
                    html.Div([
                        html.Div(
                            dcc.Graph(id='details-bar-charts'),
                                className='width50'),
                        html.Div(
                            dcc.Graph(id='age-pie-charts'),
                                className='width50')
                    ],className='row') 
                ],className='background2')
            ])

@app.callback(
    Output('graph', 'figure'),
    [Input('year-slider', 'value'),
     Input('cause-dropdown', 'value'),
     Input('rate-number-radio', 'value')])
def update_figure(selected_year, death_cause, radio_rate_number):
    if selected_year is None and death_cause is None:
        fig=dict(
                 data = [dict(x=0, y=0)],
     			 layout = dict(
     				title='Sélectionnez une année et une cause de mortalité')
                 )
    elif selected_year is None:
        fig=dict(
                 data = [dict(x=0, y=0)],
     			 layout = dict(
     				title='Sélectionnez une année')
                 )
    elif death_cause is None:
        fig=dict(
                 data = [dict(x=0, y=0)],
     			 layout = dict(
     				title='Sélectionnez une cause de mortalité')
                 )
    else: 
        if radio_rate_number=='Death_Rate':
            filtered_df = pd.DataFrame(dfTot.loc[(dfTot['TIME']==selected_year) &\
                             (dfTot['Classe_mortalité']==death_cause)]\
                            .groupby(['GEO']).sum()['Value']) 
            filtered_df = pd.DataFrame({'GEO':filtered_df.index, 
                                        'Value':filtered_df['Value']})
            filtered_df.loc[filtered_df['GEO']!='Union europenne - 28 pays (2013-2020)']
    
            fig = px.choropleth(filtered_df, geojson=europe, locations='GEO',
                            featureidkey="properties.NAME",
                            color='Value',
                            color_continuous_scale='Tealgrn',
                            range_color=(filtered_df.min()[1], filtered_df.max()[1]),
                            scope="europe",
                            labels={'Value':'Taux de mortalité'}
                                  )
        else:
            filtered_df = pd.DataFrame(dfTot.loc[(dfTot['TIME']==selected_year) &\
                     (dfTot['Classe_mortalité']==death_cause)]\
                    .groupby(['GEO']).sum()['Death_Toll']) 
            filtered_df = pd.DataFrame({'GEO':filtered_df.index, 
                                        'Death_Toll':filtered_df['Death_Toll']})
    
            fig = px.choropleth(filtered_df, geojson=europe, locations='GEO',
                            featureidkey="properties.NAME",
                            color='Death_Toll',
                            color_continuous_scale='Tealgrn',
                            range_color=(filtered_df.min()[1], filtered_df.max()[1]),
                            scope="europe",
                            labels={'Death_Toll':'Nombre de morts'},
                                  )  
              
        fig.update_geos(visible=False)
        fig.update_layout({'clickmode': 'event+select'})
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.update_layout(transition = {'duration': 300})
        fig.update_layout(coloraxis_showscale=False)
    
    return fig

@app.callback(
    [Output('sex-pie-charts', 'figure'),
     Output('age-pie-charts', 'figure'),
     Output('details-bar-charts', 'figure')],
    [Input('graph', 'clickData'),
     Input('year-slider', 'value'),
     Input('cause-dropdown', 'value'),
     Input('rate-number-radio', 'value')])
def update_details(clickData,selected_year,death_cause,radio_rate_number):
    if clickData is None:
        fig1=fig2=fig3=dict(
                        data = [dict(x=0, y=0)],
            			layout = dict(
            				title='Sélectionnez un pays')
                        )
    else:
        filtered_df_details = dfEurostat.loc[
         (dfEurostat['GEO']==clickData['points'][0]['location']) &\
                             (dfEurostat['TIME']==selected_year) &\
                             (dfEurostat['Classe_mortalité']==death_cause)]
        if radio_rate_number=='Death_Rate':         
            XHomme=filtered_df_details.loc[filtered_df_details['AGE']=='Total']\
                .groupby(['SEX']).sum()['Value']['Hommes']
            XFemme=filtered_df_details.loc[filtered_df_details['AGE']=='Total']\
                .groupby(['SEX']).sum()['Value']['Femmes']
            labels1 = ['Hommes','Femmes']
            values1 = [XHomme, XFemme]
            fig1=go.Figure(data=[go.Pie(labels=labels1, values=values1,
                                        hole=0.4,rotation=90,
                                        title={'text':'Répartition décès en '+
                                        clickData['points'][0]['location']+
                                        ' par sexe',
                                        'position':'top center'}
                                        )])
            
            XMoins65=filtered_df_details.loc[filtered_df_details['SEX']=='Total']\
                .groupby(['AGE']).sum()['Value']['Moins de 65 ans']
            XPlus65=filtered_df_details.loc[filtered_df_details['SEX']=='Total']\
                .groupby(['AGE']).sum()['Value']['65 ans ou plus']
            labels2 = ['Moins de 65 ans','65 ans ou plus']
            values2 = [XMoins65, XPlus65]    
            fig2=go.Figure(data=[go.Pie(labels=labels2, values=values2,
                                        hole=0.4,rotation=90,
                                        title={'text':'Répartition décès en '+
                                        clickData['points'][0]['location']+
                                        ' par âge',
                                        'position':'top center'}
                                        )])                                                
            
            details=filtered_df_details[['ICD10','Value']].\
                        loc[(filtered_df_details['SEX']=='Total') &
                            (filtered_df_details['AGE']=='Total')] 
            fig3=px.bar(details, x='ICD10', y='Value')
            fig3.update_yaxes(title='Taux de mortalité')

            
        else:
            deathSelectedCause=dfTot.loc[(dfTot['TIME']==selected_year) &\
                      (dfTot['GEO']==clickData['points'][0]['location'])]\
                        .groupby(['Classe_mortalité']).sum()['Death_Toll'][death_cause]
            XHomme=filtered_df_details.groupby(['SEX']).sum()['Value']['Hommes']
            XFemme=filtered_df_details.groupby(['SEX']).sum()['Value']['Femmes']
            percentXHomme=XHomme/(XHomme+XFemme)
            percentXFemme=XFemme/(XHomme+XFemme)
            XHomme=deathSelectedCause*percentXHomme
            XFemme=deathSelectedCause*percentXFemme
            labels1 = ['Hommes','Femmes']
            values1 = [XHomme, XFemme]
            fig1=go.Figure(data=[go.Pie(labels=labels1, values=values1,
                                        hole=0.4,rotation=90,
                                        title={'text':'Répartition décès en '+
                                        clickData['points'][0]['location']+
                                        ' par sexe',
                                        'position':'top center'}
                                        )]) 
            
            XMoins65=filtered_df_details.groupby(['AGE']).sum()['Value']['Moins de 65 ans']
            XPlus65=filtered_df_details.groupby(['AGE']).sum()['Value']['65 ans ou plus']
            percentXMoins65=XMoins65/(XMoins65+XPlus65)
            percentXPlus65=XPlus65/(XMoins65+XPlus65)
            XMoins65=deathSelectedCause*percentXMoins65
            XPlus65=deathSelectedCause*percentXPlus65
            labels2 = ['Moins de 65 ans','65 ans ou plus']
            values2 = [XMoins65, XPlus65]    
            fig2=go.Figure(data=[go.Pie(labels=labels2, values=values2,
                                        hole=0.4,rotation=90,
                                        title={'text':'Répartition décès en '+
                                        clickData['points'][0]['location']+
                                        ' par âge',
                                        'position':'top center'}
                                        )])                                        
            
            details = dfTot[['ICD10','Death_Toll']].loc[
                        (dfTot['GEO']==clickData['points'][0]['location']) &\
                        (dfTot['TIME']==selected_year) &\
                        (dfTot['Classe_mortalité']==death_cause)]
            fig3=px.bar(details, x='ICD10', y='Death_Toll')
            fig3.update_yaxes(title='Nombre de morts')

        fig1.update_traces(marker=dict(colors=['#537780','#009688']))
        fig1.update_layout(transition={'duration': 300},
                          legend_orientation="h")
        fig2.update_traces(marker=dict(colors=['#009688','#537780']))                          
        fig2.update_layout(transition={'duration': 300},
                          legend_orientation="h")
        fig3.update_traces(marker_color='#009688',
                           hovertemplate='%{x}<br>'+'%{y}')
        fig3.update_xaxes(visible=False)
        fig3.update_layout(transition={'duration': 300},
                           plot_bgcolor='rgba(0,0,0,0)')
        
    return fig1, fig2, fig3
    
#if __name__ == '__main__':
#    app.run_server(debug=False)
