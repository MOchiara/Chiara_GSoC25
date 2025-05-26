import numpy as np
import pandas as pd
import json
from pyodide.ffi import create_proxy
from pyodide.http import open_url
from js import document
import plotly
from ioos_qc.config import QcConfig
import js
from js import eval as js_eval
import plotly.graph_objects as go
import js

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
    uploaded_file = "./water_level_example_test.csv"
    df = pd.read_csv(open_url(uploaded_file))

    variable = "sea_surface_height_above_sea_level"
    result = run_tests(df, variable)
    mask = make_mask(df, result, variable, qc_test)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['time'].astype(str).tolist(),
        y=df['sea_surface_height_above_sea_level'].tolist(),
        mode='lines',
        name='Sea Surface Height',
        line=dict(color='blue')
    ))

    fig.add_trace(go.Scatter(
        x=df['time'].tolist(),
        y=mask['qc_fail'].tolist(),
        mode='markers',
        name='Fail',
        marker=dict(color='red')
    ))

    fig.add_trace(go.Scatter(
        x=df['time'].tolist(),
        y=mask['qc_notrun'].tolist(),
        mode='markers',
        name='Not Run',
        marker=dict(color='gray')
    ))

    fig.add_trace(go.Scatter(
        x=df['time'].tolist(),
        y=mask['qc_suspect'].tolist(),
        mode='markers',
        name='Suspect',
        marker=dict(color='orange')
    ))

    fig.add_trace(go.Scatter(
        x=df['time'].tolist(),
        y=mask['qc_pass'].tolist(),
        mode='markers',
        name='Pass',
        marker=dict(color='green')
    ))

    fig.update_layout(
        title=f'Sea Surface Height - {qc_test}',
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

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    js_code = f"""
        var figure = {graphJSON};
        Plotly.newPlot('qc_test', figure.data, figure.layout);
    """
    js_eval(js_code)

def selectChange(event):
    choice = document.getElementById("select").value
    print(f"Selected choice: {choice}")
    plot(choice)


def setup():
    change_proxy = create_proxy(selectChange)
    e = document.getElementById("select")
    e.addEventListener("change", change_proxy)


setup()

plot(qc_test="gross_range_test")


