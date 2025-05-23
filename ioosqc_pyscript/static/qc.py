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
# Load QC config
def run_tests(df, variable):
    from pyodide.http import open_url
    config_file_path = "./qc_config.json"
    with open_url(config_file_path) as config_json:
        qc_config = json.load(config_json)

    qc = QcConfig(qc_config)
    print(qc)
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
    print(f"Plotting for {qc_test}")  # Debug log
    uploaded_file = "./water_level_example_test.csv"
    df = pd.read_csv(open_url(uploaded_file))
    print(df.size)
    print('data exists')
    variable = "sea_surface_height_above_sea_level"

    result = run_tests(df, variable)

    mask = make_mask(df, result, variable, qc_test)
    fig = px.line(df, x="time", y=variable, width=800, height=400)

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

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    js_code = f"""
        var figure = {graphJSON};
        Plotly.newPlot('qc_test', figure.data, figure.layout);
    """
    js.run(js_code)


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
plot(qc_test="gross_range_test")