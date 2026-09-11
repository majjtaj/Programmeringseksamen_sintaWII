import pandas as pd     
import dash                
from dash import html, dcc, Input, Output, callback, ctx
import plotly.express as px
import plotly.graph_objects as go
import dash_cytoscape as cyto

VictGeo_df = pd.read_csv('Victims_geocoded.csv', encoding='UTF-8', dtype={'ID': str}) 
Rela_df = pd.read_csv('Relationships.csv', encoding='utf-8', dtype=str)
#Converting the dataframe to a dictionary
vict_dict = VictGeo_df.set_index('ID').to_dict('index') 

'''
Table of victims
'''
table_fig = go.Figure(data=[go.Table(
    header=dict(values=['Name', 'Date of birth', 'Date of death', 'Age of death']), #header names
    cells=dict(values=[VictGeo_df['Name'],
                       VictGeo_df['Birthdate'],
                       VictGeo_df['Deathdate'],
                       VictGeo_df['age']])
)])

'''
Map of Birthplaces
'''
birth_circles = (
    VictGeo_df.groupby(['Birthplace', 'Birthlatitude', 'Birthlongitude'], as_index=False)
    .size() #groupby + size makes bubbles according to size
    .rename(columns={'size': 'victims'})
)

'''
Map of deathplaces
'''
death_circles = (
    VictGeo_df.groupby(['Deathplace', 'Deathlatitude', 'Deathlongitude'], as_index=False)
    .size()
    .rename(columns={'size': 'victims'})
)

'''
Network graph
'''
elements = []
#Creating the nodes 
for item in pd.concat([Rela_df['ID1'], Rela_df['ID2']]).unique():
    v_data = vict_dict.get(item, {})
    elements.append({'data': {
        'id': item,
        'birthplace': v_data.get('Birthplace', 'Unknown'),
        'deathplace': v_data.get('Deathplace', 'Unknown')}})

#Creating the edges
for _, row in Rela_df.iterrows():
    elements.append({'data': {'source': row['ID1'], 'target': row['ID2'], 
                              'general':row['General relationship type'],
                              'detailed':row['Detailed relationship type']}})

'''
Dash app
'''
app = dash.Dash(__name__) 
app.layout = html.Div([
        #table
        html.H1('Table over victims'),
        dcc.Graph(id = 'victims_table',figure = table_fig),
            #dropdown
            html.H2("Map"),
            dcc.Dropdown(
                id="map_selector",
                options=[
                    {"label": "Birthplaces", "value": "birth"},
                    {"label": "Deathplaces", "value": "death"},
                ],
                value="birth",  #set birth as default
                clearable=False
            ),
            #map graph
            dcc.Graph(id="map_graph"), 
            #network graph
            html.H2("Network"),
            cyto.Cytoscape(
                id="cytoscape",
                elements=elements,
                minZoom = 0.3,
                maxZoom = 2,
                layout={"name": "cose"},
                stylesheet=[
                    {'selector': 'node', 'style': {'background-color': '#636EFA'}},
                    {'selector': 'edge', 'style': {'line-color': '#ccc'}}
                ]),
            html.Div(id="cytoscape-tapNodeData-output"),
            html.Div(id="cytoscape-tapEdgeData-output"),
])

'''
Callbacks
'''
@callback(
    Output("map_graph", "figure"),
    [Input("map_selector", "value"),
     Input("cytoscape", "tapNodeData"), 
     Input("map_graph", "clickData")]   
)
def update_map(which, net_data, map_data): 
    trigger = ctx.triggered_id #which of the inputs triggered the callback

    if which == "death":
        df = death_circles #copies the map data
        lat_c = 'Deathlatitude'
        lon_c = 'Deathlongitude'
        hover_c = 'Deathplace'
    else:
        df = birth_circles
        lat_c = 'Birthlatitude'
        lon_c = 'Birthlongitude'
        hover_c = 'Birthplace'

    df['color'] = 'blue' #setting default color to blue, by making a new column
    place_to_highlight = None #setting the highlight to none to start

    if trigger == 'cytoscape' and net_data:
        place_to_highlight = net_data.get(which + 'place') #which circle to highlight
    elif trigger == 'map_graph' and map_data:
        place_to_highlight = map_data['points'][0].get('hovertext') #highlight the clicked circle

    if place_to_highlight:
        df.loc[df[hover_c] == place_to_highlight, 'color'] = 'red' #change color to red

    fig = px.scatter_geo(   
                     df,
                     lat=lat_c,
                     lon=lon_c,
                     hover_name=hover_c,
                     size='victims',
                     projection='natural earth', scope='europe',
                     color='color', #color assigned from the column created
                     color_discrete_map={'blue': '#636EFA', 'red': '#EF553B'}
    )
    fig.update_layout(uirevision='constant', showlegend=False) #when updated we keep the zoom-level
    return fig

@callback(
    Output('cytoscape', 'stylesheet'),
    [Input('map_graph', 'clickData'),
     Input('cytoscape', 'tapNodeData'),
     Input('map_selector', 'value')]
)
def update_network_style(map_data, net_data, map_type):
    base_style = [
        {'selector': 'node', 'style': {'background-color': '#636EFA'}},
        {'selector': 'edge', 'style': {'line-color': '#ccc'}}
    ] #keeping the colors as defined in the stylesheet
    
    trigger = ctx.triggered_id
    
    if trigger == 'map_selector':
        return base_style #no change when choosing from the map dropdown
        
    highlight = None 
    
    if trigger == 'map_graph' and map_data:
        place = map_data['points'][0]['hovertext']
        if map_type == 'birth':
            attr = 'birthplace'
        else:
            attr = 'deathplace'
        highlight = f'node[{attr} = "{place}"]' #all nodes that has the place
        
    elif trigger == 'cytoscape' and net_data:
        node_id = net_data['id']
        highlight = f'node[id = "{node_id}"]' #highlight the clicked node
        
    if highlight:
        base_style.append({
            'selector': highlight,
            'style': {'background-color': '#EF553B'}
        }) #update style to change color of the nodes
        
    return base_style

@callback(
    Output('cytoscape-tapNodeData-output', 'children'),
    Input('cytoscape', 'tapNodeData')
)

def displayTapNodeData(data):
    if data is None:
        return ""
    return "You tapped the id: " + data['id']

@callback(
     Output('cytoscape-tapEdgeData-output', 'children'),
     Input('cytoscape', 'tapEdgeData')
)

def displayTapEdgeData(data):
    if data is None:
        return ""
    if 'source' not in data or 'target' not in data:
        return ""
    return "The relation is " + data['general'] + " and " + data['detailed']


#run the app:
if __name__ == '__main__':
    app.run(debug=False, port=8040)
