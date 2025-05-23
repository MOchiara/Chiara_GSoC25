
import numpy as np
import pandas as pd
import plotly.express as px
import json
from pyodide.ffi import create_proxy
from pyodide.http import open_url
from js import document
import plotly
from ioos_qc import qartod
from ioos_qc.config import QcConfig
import js

# Load QC config
def run_tests(df, variable):
    from pyodide.http import open_url
    config_file_path = "./qc_config.json"
    with open_url(config_file_path) as config_json:
        qc_config = json.load(config_json)

    qc = QcConfig(qc_config)
    qc_results = qc.run(
        inp=df[variable],
        tinp=df["timestamp"],
        zinp=df["z"],
    )

    qc_result_pd = pd.DataFrame(
        qc_results["qartod"], columns=qc_results["qartod"].keys()
    )
    result = pd.concat([df, qc_result_pd], axis=1)

    return result.set_index("time")




def make_mask(df, result, variable="sea_surface_height_above_sea_level", qc_test="spike_test"):
    obs = df[variable]
    mask = result[qc_test]

    return {
        "qc_pass": np.ma.masked_where(mask != 1, obs),
        "qc_suspect": np.ma.masked_where(mask != 3, obs),
        "qc_fail": np.ma.masked_where(mask != 4, obs),
        "qc_notrun": np.ma.masked_where(mask != 2, obs),
    }

def plot(qc_test):
    # Get the data
    uploaded_file = "./water_level_example_test.csv"
    df = pd.read_csv(open_url(uploaded_file))

    variable = "sea_surface_height_above_sea_level"
    result = run_tests(df, variable)
    print(f'{df[variable].min()},{df[variable].max()}')
    mask = make_mask(df, result, variable, qc_test)
    import plotly.graph_objects as go
    fig = go.Figure()

    # Main line plot
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['sea_surface_height_above_sea_level'],
        mode='lines',
        name='Sea Surface Height',
        line=dict(color='blue')
    ))

    # QC markers
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=mask['qc_fail'],
        mode='markers',
        name='Fail',
        marker=dict(color='red')
    ))

    fig.add_trace(go.Scatter(
        x=df['time'],
        y=mask['qc_notrun'],
        mode='markers',
        name='Not Run',
        marker=dict(color='gray')
    ))

    fig.add_trace(go.Scatter(
        x=df['time'],
        y=mask['qc_suspect'],
        mode='markers',
        name='Suspect',
        marker=dict(color='orange')
    ))

    fig.add_trace(go.Scatter(
        x=df['time'],
        y=mask['qc_pass'],
        mode='markers',
        name='Pass',
        marker=dict(color='green')
    ))

    # Layout configuration
    fig.update_layout(
        title='Sea Surface Height with QC Tests',
        xaxis_title='Time',
        yaxis_title='Sea Surface Height (m)',
        yaxis=dict(rangemode='tozero'),
        showlegend=True,
        legend=dict(
            x=1.05,
            y=0.5,
            traceorder='normal',
            font=dict(size=12),
            bgcolor='rgba(255,255,255,0)',
            borderwidth=0
        )
    )


    '''
    fig = px.line(df,
                  x="time", y=variable,
                  width=800, height=400)
    fig.add_trace(
        px.scatter(x=df["time"], y=mask["qc_fail"], color_discrete_sequence=["red"]).data[0]
    )
    fig.add_trace(
        px.scatter(x=df["time"], y=mask["qc_notrun"], color_discrete_sequence=["gray"]).data[0]
    )
    fig.add_trace(
        px.scatter(x=df["time"], y=mask["qc_suspect"], color_discrete_sequence=["orange"]).data[0]
    )
    fig.add_trace(
        px.scatter(x=df["time"], y=mask["qc_pass"], color_discrete_sequence=["green"]).data[0]
    )
   '''
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    js_code = f"""
        var figure = {graphJSON};
        Plotly.newPlot('qc_test', figure.data, figure.layout);
    """
    from js import eval as js_eval
    
    js_eval(js_code)

def selectChange(event):
    print("Dropdown value changed")  # Debug log
    choice = document.getElementById("select").value
    print(f"Selected choice: {choice}")
    plot(choice)


def setup():
    print("Setting up event listener for dropdown")  # Debug log
    change_proxy = create_proxy(selectChange)
    e = document.getElementById("select")
    e.addEventListener("change", change_proxy)


setup()

try:
    plot(qc_test="gross_range_test")
except Exception as e:
    print(f"Top-level plot error: {e}")
    import traceback
    traceback.print_exc()



