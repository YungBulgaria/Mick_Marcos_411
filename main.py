from dash import Dash, html, dash_table, dcc, ctx
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dbms_connections import (
    get_mysql_keywords, get_mongodb_pie, get_neo4j_bar, get_mysql_search, get_faculty,
    get_highest_KRC, list_faculty, list_faculty_details, update_faculty_details,
    list_faculty_keywords, update_faculty_keywordsA, update_faculty_keywordsD
)
import dash_bootstrap_components as dbc

app = Dash(external_stylesheets=[dbc.themes.CYBORG])

search_empty_response = html.Div([html.P("Please enter the name of a keyword.")])

# Clear button
@app.callback(
    Output("table", "selected_rows"),
    Input("clear", "n_clicks")
)
def clear(n_clicks):
    return []

# Refresh button
@app.callback(
    Output("keyword-container", "children"),
    Input("refresh", "n_clicks")
)
def refresh(n_clicks):
    return generate_keywordtable()

# Creating table of keywords
def generate_keywordtable():
    data_input = get_mysql_keywords()
    data_table = [{"name": name} for name in data_input["name"]]
    table = dash_table.DataTable(
        id='table',
        data=data_table,
        columns=[{"name": "Name", "id": "name"}],
        virtualization=True,
        page_size=9999,
        style_table={'maxHeight': '200px', 'overflowX': 'auto', 'border': 'thin lightgrey solid'},
        style_cell={'textAlign': 'left'},
        sort_action='native',
        filter_action='native',
        sort_by=[{"column_id": "name", "direction": "asc"}],
        row_selectable='multi',  # Enable row selection
        selected_rows=[],  # Initialize with no rows selected
    )
    return table

# Generate searched keywords
def generate_searched_keywordtable(data):
    data_table = [{"name": name} for name in data]
    table = dash_table.DataTable(
        id='result_table',
        data=data_table,
        columns=[{"name": "Result", "id": "name"}],
        virtualization=True,
        page_size=9999,
        style_table={'maxHeight': '200px', 'border': 'thin lightgrey solid'},
        style_cell={'textAlign': 'left'},
        sort_action='native',
        filter_action='native'
    )
    return table

# Define the callback to update the output container

# MySQL part1
@app.callback(
    Output('output-container1', 'children'),
    Output('memory', 'data'),
    [
        Input('input-box1', 'value'),
        Input('table', 'derived_virtual_selected_rows'),
        Input('table', 'derived_virtual_data')
    ]
)
def update_output1(input_value, selected_rows, datatable):
    query = {}
    data = []
    resulting_data = []
    if ctx.triggered_id == 'input-box1' and input_value:
        query['input_val'] = input_value
        data = get_mysql_search(query)
    elif ctx.triggered_id == 'table' and selected_rows:
        for row in selected_rows:
            resulting_data.append(datatable[row]["name"])
    else:
        return search_empty_response, []
    for i in data:
        resulting_data.append(i[0])
    return generate_searched_keywordtable(resulting_data), resulting_data

# Create MongoDB keyword pie chart
def keyword_f_p_pie(data, value):
    result = []
    # Faculty
    if len(data[0]) > 0:
        f_keywords = []
        f_count = []
        for i in data[0]:
            f_keywords.append(i["_id"])
            f_count.append(i["faculty_count"])
        fdata = {"keyword": f_keywords, "count": f_count}
        fdf = pd.DataFrame(fdata).sort_values(by=["count"], ascending=False).head(value)
        fpie = px.pie(fdf, width=600, names="keyword", values="count", title=f"Top {len(fdf)} Keywords Among Faculty", hover_name="keyword")
        result.append(dcc.Graph(id="fpie", figure=fpie))
    # Publications
    if len(data[1]) > 0:
        p_keywords = []
        p_count = []
        for i in data[1]:
            p_keywords.append(i["_id"])
            p_count.append(i["publication_count"])
        pdata = {"keyword": p_keywords, "count": p_count}
        pdf = pd.DataFrame(pdata).sort_values(by=["count"], ascending=False).head(value)
        ppie = px.pie(pdf, width=600, names="keyword", values="count", title=f"Top {len(pdf)} Keywords Among Publications", hover_name="keyword")
        result.append(dcc.Graph(id="ppie", figure=ppie))
    return result

# MongoDB part2
@app.callback(
    Output('output-container2', 'children'),
    Output("piememory", "data"),
    [
        Input('memory', 'data'),
        Input("pieslider", "value"),
        State("piememory", "data")
    ]
)
def update_output2(data, value, prevdata):
    if not data or len(data) == 0:
        return search_empty_response, prevdata
    if ctx.triggered_id == 'pieslider' and prevdata and len(prevdata) > 0:
        prevdata_save = prevdata
        return keyword_f_p_pie(prevdata, value), prevdata_save
    query = {}
    query['input_val'] = []
    for i in data:
        query['input_val'].append(i)
    mongodb_data = get_mongodb_pie(query)
    mongodb_data_save = mongodb_data
    return keyword_f_p_pie(mongodb_data, value), mongodb_data_save

# Neo4j part3
def related_keyword_barchart(data, value, dropdown):
    if len(data) == 0:
        return []
    data_table = []
    for i in data:
        data_table.append({"name": i[0]["name"], "count": i[0]["count"], "source": i[1]})
    neodf = pd.DataFrame(data_table)
    neodf = neodf[neodf["source"].isin(dropdown)]
    groupdf = neodf.groupby("name").sum(numeric_only=True).sort_values(by=["count"], ascending=False).head(value).reset_index()
    neodf = neodf[neodf["name"].isin(groupdf["name"].unique())]
    neoKbar = px.bar(data_frame=neodf, x="name", y="count", color="source", text_auto='.2s', title=f"Top {len(groupdf)} Related Keywords")
    neoKbar.update_traces(textangle=0, textposition="outside", cliponaxis=False)
    neoKbar.update_layout(xaxis={'categoryorder': 'total descending'})
    return dcc.Graph(id="neo4jbar", figure=neoKbar)

@app.callback(
    Output('output-container3', 'children'),
    Output("barmemory", "data"),
    [
        Input('memory', 'data'),
        Input("barslider", "value"),
        State("barmemory", "data"),
        Input("barneo4jdropdown", "value")
    ]
)
def update_output3(data, value, prevdata, dropdown):
    if not data or len(data) == 0:
        return search_empty_response, prevdata
    if ctx.triggered_id in ['barslider', "barneo4jdropdown"] and prevdata and len(prevdata) > 0:
        return related_keyword_barchart(prevdata, value, dropdown), prevdata
    query = {}
    query['input_val'] = []
    for i in data:
        query['input_val'].append(i)
    neo4j_data = get_neo4j_bar(query)
    return related_keyword_barchart(neo4j_data, value, dropdown), neo4j_data

# Part 4
@app.callback(
    Output('output-container4', 'children'),
    [
        Input('submit', 'n_clicks'),
        State('input-box1', 'value'),
        State('table', 'derived_virtual_selected_rows'),
        State('table', 'derived_virtual_data')
    ]
)
def update_output4(n_clicks, input_value, selected_rows, datatable):
    if n_clicks is None:
        raise PreventUpdate
    query = {}
    data = []
    keywords = []
    names = []
    index = 0
    query2 = {}
    data2 = []
    if input_value:
        query['input_val'] = input_value
        data = get_faculty(query)
        if len(data) > 0 and len(data[0]) > 1:
            image_url = data[0][1]
            return data[0][0], data[0][2], html.Img(src=image_url, alt="Faculty Image", style={"width": "300px", "height": "auto"})
        return "No image found"
    elif selected_rows:
        for row in selected_rows:
            query['input_val'] = datatable[row]["name"]
            if len(selected_rows) > 1:
                data.append(get_faculty(query))
            else:
                data = get_faculty(query)
            keywords.append(datatable[row]["name"])
            names.append(data[index][0][0])
            index += 1
        if len(names) > 1:
            for name in names:
                query2['input_val'] = name
                krcs = []
                for keyword in keywords:
                    query['input_val'] = keyword
                    result = get_highest_KRC(query, query2)
                    if result:
                        number = str(result[0]).strip("(),")
                        krcs.append(float(number))
                if len(krcs) != 0:
                    data2.append(sum(krcs) / len(krcs))
            if data2:
                highestAverage = max(data2)
                count = 0
                for num in data2:
                    if num == highestAverage:
                        break
                    count += 1
                image_url = data[count][0][1]
                return data[count][0][0], highestAverage, html.Img(src=image_url, alt="Faculty Image", style={"width": "300px", "height": "auto"})
            else:
                return "No image found"
        else:
            if len(data) > 0 and len(data[0]) > 1:
                image_url = data[0][1]
                return data[0][0], data[0][2], html.Img(src=image_url, alt="Faculty Image", style={"width": "300px", "height": "auto"})
            return "No image found"
    else:
        return "Please enter the name of a keyword"

# Part 5
# Make a drop down menu that lists every faculty
# Allow you to select a faculty member and in text boxes next to faculty member edit their details
@app.callback(
    Output('dd-output-container', 'children'),
    Output('ddmemory', 'data'),
    Output('output-container5', 'children'),
    Output('dddata', 'data'),
    Output('input-box2', 'value'),
    Output('input-box3', 'value'),
    Output('input-box4', 'value'),
    Output('input-box5', 'value'),
    Input('dropdown', 'value'),
    Input('save-button', 'n_clicks'),
    State('dropdown', 'value'),
    State('input-box2', 'value'),
    State('input-box3', 'value'),
    State('input-box4', 'value'),
    State('input-box5', 'value'),
    prevent_initial_call=True
)
def update_dd(value, n_clicks, faculty, position, email, phone, research_area):
    query = {}
    query['input_val'] = value
    if n_clicks > 0 and faculty:
        update_faculty_details(faculty, position, email, phone, research_area)
    data = list_faculty_details(query)
    flattened_data = [item for sublist in data for item in sublist]
    if data:
        labels = ["Position: ", "Email: ", "Phone: ", "Research Area: "]
        formatted_data_list = []
        for label, info in zip(labels, flattened_data):
            if info and info != " " and info != "":
                formatted_data_list.append(f"{label}{info}")
        formatted_data = ' '.join(formatted_data_list)
        return f'You have selected {value}', value, formatted_data, flattened_data, '', '', '', ''
    else:
        return "Select a value", None, None, None, '', '', '', ''

# Part 6
# Add or delete faculty members' keywords
@app.callback(
    Output('dd-output-container2', 'children'),
    Output('ddmemory2', 'data'),
    Output('output-container6', 'children'),
    Output('dddata2', 'data'),
    Output('input-box6', 'value'),
    Output('input-box7', 'value'),
    Input('dropdown2', 'value'),
    Input('save-button2', 'n_clicks'),
    State('input-box6', 'value'),
    Input('delete-button', 'n_clicks'),
    State('input-box7', 'value')
)
def update_dd2(value, n_clicksA, wordAdd, n_clicksD, wordDelete):
    query = {}
    query['input_val'] = value
    if n_clicksA > 0 and value and wordAdd != "" and wordAdd != " ":
        update_faculty_keywordsA(value, wordAdd)
    if n_clicksD > 0 and value and wordDelete != "" and wordDelete != " ":
        update_faculty_keywordsD(value, wordDelete)
    data = list_faculty_keywords(query)
    if data:
        formatted_data = ', '.join(data)
        to_return = "Keywords: " + formatted_data
        return to_return, None, None, None, '', ''
    else:
        return "Select a value", None, None, None, '', ''

tablewdiget = html.Div(children=[html.Div(children=[
    html.Div([html.H2("Keywords"), html.Div(children=[
        dbc.Label('Click a cell(s), filter the table', style={'display': 'inline-block', "marginRight": 80}),
        html.Button("Clear Selection", id="clear", style={'display': 'inline-block'}),
        html.Button("Refresh Keywords", id="refresh", style={'display': 'inline-block'})
    ])])], style={}),
    html.Div(children=[
        html.Div([generate_keywordtable()], id='keyword-container', style={'display': 'inline-block'})])], className='widget')

searchwidget = html.Div(children=[html.Div([html.Div([html.H2("Search")], style={'display': 'inline-block'}),
    html.Div([
        html.Label("Search keywords here (enter to submit) "),
        dcc.Input(
            id='input-box1', type='text', value='', debounce=True),], style={},),
    html.Div(id='output-container1', style={'display': 'inline-block'})
], style={'display': 'inline-block', 'vertical-align': 'top'})], className='widget')

toppiewidget = html.Div([html.H2("Top Keywords"),
    dcc.Slider(1, 20, 1, value=10, id='pieslider'),
    html.Div(id='output-container2', style={'display': 'flex'})], className='widget')

topbarwidget = html.Div([html.H2("Top Related"),
    dcc.Slider(1, 20, 1, value=10, id='barslider'),
    dcc.Dropdown(["Faculty", "Publication"], ["Faculty", "Publication"], multi=True, id="barneo4jdropdown"),
    html.Div(id='output-container3', style={})], className='widget')

topfacultywidget = html.Div([html.H2("Top Faculty"),
    html.Button("Find Featured Faculty Member", id="submit", style={'display': 'inline-block'}),
    html.Div(id='output-container4', style={})], className='widget')

changefacultymemberwidget = html.Div([
    html.H2("Edit Faculty"),
    dcc.Dropdown(list_faculty(), "Hello", id='dropdown'),
    html.Div(id='dd-output-container'),
    dbc.Row([
        dbc.Col(dbc.Label("Position: ", className="text-right"), width=2),
        dbc.Col(dcc.Input(id='input-box2', type='text', value='', debounce=True), width=10)
    ], className="mb-3 align-items-center"),
    dbc.Row([
        dbc.Col(dbc.Label("Email: ", className="text-right"), width=2),
        dbc.Col(dcc.Input(id='input-box3', type='text', value='', debounce=True), width=10)
    ], className="mb-3 align-items-center"),
    dbc.Row([
        dbc.Col(dbc.Label("Phone: ", className="text-right"), width=2),
        dbc.Col(dcc.Input(id='input-box4', type='text', value='', debounce=True), width=10)
    ], className="mb-3 align-items-center"),
    dbc.Row([
        dbc.Col(dbc.Label("Research Area: ", className="text-right"), width=2),
        dbc.Col(dcc.Input(id='input-box5', type='text', value='', debounce=True), width=10)
    ], className="mb-3 align-items-center"),
    html.Button("Save", id="save-button", n_clicks=0, className="btn btn-primary mt-3"),
    html.Div(id='output-container5', style={})
], className='widget')

adddeletekeyword = html.Div([
    html.H2("Keyword A/D"),
    dcc.Dropdown(list_faculty(), "Agouris", id='dropdown2'),
    html.Div(id='dd-output-container2'),
    dbc.Row([
        dbc.Col(dbc.Label("Add Keyword: ", className="text-right"), width=2),
        dbc.Col(dcc.Input(id='input-box6', type='text', value='', debounce=True), width=10)
    ], className="mb-3 align-items-center"),
    dbc.Row([
        dbc.Col(dbc.Label("Delete Keyword: ", className="text-right"), width=2),
        dbc.Col(dcc.Input(id='input-box7', type='text', value='', debounce=True), width=10)
    ], className="mb-3 align-items-center"),
    dbc.Row([
        dbc.Col(html.Button("Save", id='save-button2', n_clicks=0, className="btn btn-primary"), width=6, className="text-right"),
        dbc.Col(html.Button("Delete", id="delete-button", n_clicks=0, className="btn btn-danger"), width=6)
    ], className="mb-3 align-items-center"),
    html.Div(id='output-container6', style={})
], className='widget')

app.layout = dbc.Container(
    [dcc.Store(id='memory'), dcc.Store(id='piememory'), dcc.Store(id='barmemory'), dcc.Store(id='ddmemory'),
     dcc.Store(id='dddata'), dcc.Store(id='ddmemory2'), dcc.Store(id='dddata2'),
     dbc.Row(
         [
             dbc.Col(tablewdiget, width=4),
             dbc.Col(searchwidget, width=4),
             dbc.Col(topbarwidget, width=4)
         ],
         className='rowing',
     ),
     dbc.Row(
         [
             dbc.Col(toppiewidget, width=12)
         ],
         className='rowing',
     ),
     dbc.Row(
         [
             dbc.Col(topfacultywidget, width=4),
             dbc.Col(changefacultymemberwidget, width=4),
             dbc.Col(adddeletekeyword, width=4)
         ],
         className='rowing',
     )
    ],
    fluid=True,
)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        {%favicon%}
        {%css%}
        <style>
            .widget {
                background-color: #4682b4;
                padding: 20px;
                margin: 10px;
                text-align: center;
                color: black;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
