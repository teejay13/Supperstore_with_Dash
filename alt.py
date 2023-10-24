# Imports
import pandas as pd
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input
from numerize import numerize
from plotly.subplots import make_subplots
import plotly.express as px
from app import app, server

# Data Preparation
def prepare_data():
    df = pd.read_csv('https://raw.githubusercontent.com/teejay13/Supperstore_with_Dash/main/Sample_Superstore.csv')
    df.columns = df.columns.str.replace(" ", "_").str.lower()
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['ship_date'] = pd.to_datetime(df['ship_date'])
    df['quantity'] = df['quantity'].astype(float)
    return df

# Helper functions
def gen_total_bans(df, column):
    return df[column].sum()

# Generate all aggregations and plots
def generate_plots(df):
    total_customers = df['customer_id'].agg(['count']).reset_index()
    sales_df = df.sort_values(by='order_date')
    sales_by_date = sales_df.groupby([pd.Grouper(key='order_date', freq='M')])['sales'].sum().reset_index()
    sales_by_loc = sales_df.groupby('state')['sales'].sum().reset_index()
    sales_by_segment = sales_df.groupby('segment')['sales'].sum().reset_index()
    sales_by_segment['sales'] = sales_by_segment['sales'].round(1)

    df_states = pd.read_csv('https://raw.githubusercontent.com/teejay13/Supperstore_with_Dash/main/states.csv')
    df_merge_state = pd.merge(sales_by_loc, df_states[['state', 'abbreviation']], on='state')

    # Plots
    sales_line = px.area(sales_by_date, x="order_date", y="sales", title='Sales over Time')
    sales_choro = px.choropleth(
        data_frame=df_merge_state,
        locationmode='USA-states',
        locations='abbreviation',
        scope="usa",
        color='sales',
        color_continuous_scale=[(0, '#E0F8FF'), (1, '#003366')],
        hover_data=['state', 'sales'],
        labels={'sales': 'total sales'}
    )
    
    sales_segment_bar = px.bar(sales_by_segment, x="sales", y="segment", text_auto=True, title="Sales by Segment", orientation='h')
    sales_segment_bar.update_traces(textfont_size=12, textangle=0, textposition="inside")
    sales_segment_bar.update_layout(yaxis={'categoryorder': 'total ascending'})

    Sales_by_ship_mode = sales_df.groupby(['ship_mode', 'region'])['sales'].sum().reset_index()
    ship_mode_classes = ["First Class", "Standard Class", "Second Class", "Same Day"]
    ship_mode_data = {mode: Sales_by_ship_mode[Sales_by_ship_mode['ship_mode'] == mode] for mode in ship_mode_classes}
    
    # Subplots
    sales_region_ship = make_subplots(rows=1, cols=4, shared_yaxes=True)
    for i, mode in enumerate(ship_mode_classes, start=1):
        fig = px.bar(ship_mode_data[mode], x="sales", y="region", orientation='h')
        sales_region_ship.add_trace(fig['data'][0], row=1, col=i)
        sales_region_ship.update_xaxes(title_text=mode, row=1, col=i)

    return sales_line, sales_choro, sales_segment_bar, sales_region_ship

# Initialize Dash app
def init_dashboard():
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    server = app.server
    sales_line, sales_choro, sales_segment_bar, sales_region_ship = generate_plots(prepare_data())

    sales = dbc.Card(
        [
            html.Div(
                [
                    # dcc.Graph(id="pie-graph",figure=sales_category_bar),
                    dbc.CardBody(
                    [
                        html.H1(f"${numerize.numerize(gen_total_bans(prepare_data(),'sales'), 1)} ", className="card-title"),
                        html.H6("Total Sales", className="card-title"),
                    ])
                ]
            ),
        ],
        body=True,
    )

    discount = dbc.Card(
        [
            html.Div(
                [
                    # dcc.Graph(id="pie-graph",figure=sales_category_bar),
                    dbc.CardBody(
                    [
                        html.H1(f"${numerize.numerize(gen_total_bans(prepare_data(),'discount'),1)}", className="card-title"),
                        html.H6("Total Discount", className="card-title"),
                    ])
                ]
            ),
        ],
        body=True,
    )

    profit = dbc.Card(
        [
            html.Div(
                [
                    # dcc.Graph(id="pie-graph",figure=sales_category_bar),
                    dbc.CardBody(
                    [
                        html.H1(f"${numerize.numerize(gen_total_bans(prepare_data(),'profit'),1)}", className="card-title"),
                        html.H6("Total Profit", className="card-title"),
                    ])
                ]
            ),
        ],
        body=True,
    )

    quantity = dbc.Card(
        [
            html.Div(
                [
                    # dcc.Graph(id="pie-graph",figure=sales_category_bar),
                    dbc.CardBody(
                    [
                        html.H1(numerize.numerize(gen_total_bans(prepare_data(),'quantity'),1), className="card-title"),
                        html.H6("Total Quantity", className="card-title"),
                    ])
                ]
            ),
        ],
        body=True,
    )


    app.layout = html.Div(
        [
            dcc.Location(id="url"),
            dbc.NavbarSimple(
                children=[
                    dbc.NavLink("Overview", href="/", active="exact"),
                    dbc.NavLink("Product Analysis", href="/page-1", active="exact"),
                    dbc.NavLink("Regional Analysis", href="/page-2", active="exact"),
                    dbc.NavLink("Order Details", href="/page-3", active="exact"),
                ],
                brand="Superstore Dashboard",
                color="primary",
                dark=True,
            ),
            dbc.Container(id="page-content", className="pt-4"),
        ]
    )

    @app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def render_page_content(pathname):
        if pathname == "/":
            return dbc.Row(
                children = [
                    dbc.Row([
                        dbc.Col(sales, md=3),
                        dbc.Col(discount, md=3),
                        dbc.Col(profit, md=3),
                        dbc.Col(quantity, md=3),
                    ]),
                    dbc.Row([
                        #dbc.Col(ok, md=6),
                        dbc.Col(dcc.Graph(id="cluster-graph",figure=sales_line), md=6),
                        dbc.Col(dcc.Graph(id="choro-graph",figure=sales_choro), md=6),
                    ]),
                    dbc.Row([
                        dbc.Col(dcc.Graph(id="region-segment-graph",figure=sales_region_ship), md=8),
                        dbc.Col(dcc.Graph(id="segment-graph",figure=sales_segment_bar), md=4),
                    ])
                ],
                align="center",
            )
        elif pathname == "/page-1":
            return html.P("THey Yay!")
        elif pathname == "/page-2":
            return html.P("wE MOVE")
        # If the user tries to reach a different page, return a 404 message
        return html.Div(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ],
            className="p-3 bg-light rounded-3",
        )

    if __name__ == '__main__':
        app.run_server(debug=False)

# Execute main function
init_dashboard()
