import numpy as np
import pandas as pd
import json
from pyodide.ffi import create_proxy
from pyodide.http import open_url
from js import document
import plotly
from ioos_qc.config import QcConfig
from js import eval as js_eval
import plotly.graph_objects as go
from js import FileReader
import js

uploaded_df = None

def handle_file_upload(event):
    global uploaded_df

    file = event.target.files.item(0)
    if file:
        reader = FileReader.new()

        def onload(evt):
            global uploaded_df
            content = evt.target.result
            from io import StringIO
            uploaded_df = pd.read_csv(StringIO(content))
            print("File loaded successfully")
            update_variable_options()

        onload_proxy = create_proxy(onload)
        reader.onload = onload_proxy
        reader.readAsText(file)



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
    global uploaded_df

    if uploaded_df is None:
        show_message("No file uploaded. Using default file for display.")
        uploaded_file = "./water_level_example_test.csv"
        df = pd.read_csv(open_url(uploaded_file))
    else:
        df = uploaded_df
        show_message("Uploaded file loaded and used.")

    # Selected variable from dropdown
    variable_select = js.document.getElementById("variableSelect")
    variable = variable_select.value

    # If no variable selected, back to default var in default dataset
    if not variable:
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
def load_data_click(event):
    qc_test = document.getElementById("select").value
    if uploaded_df is None:
        show_message("No uploaded file found. Please upload a file first.", "warning")
        return
    print(f"Loading plot with test: {qc_test}")
    plot(qc_test)

def update_variable_options():
    global uploaded_df
    if uploaded_df is None:
        return

    variable_select = js.document.getElementById("variableSelect")

    variable_select.innerHTML = ""

    for col in uploaded_df.columns:
        option = js.document.createElement("option")
        option.value = col
        option.text = col
        variable_select.appendChild(option)

def download_processed_data(event):
    global uploaded_df

    if uploaded_df is None:
        show_message("No data to download. Please upload a file first.", "warning")
        return

    qc_test = document.getElementById("select").value
    variable = document.getElementById("variableSelect").value

    result = run_tests(uploaded_df, variable)
    csv_content = result.to_csv(index=False)

    blob = js.Blob.new([csv_content], {"type": "text/csv"})
    url = js.URL.createObjectURL(blob)

    download_link = js.document.createElement("a")
    download_link.href = url
    download_link.download = "masked_qc_data.csv"
    download_link.style.display = "none"
    js.document.body.appendChild(download_link)
    download_link.click()
    js.document.body.removeChild(download_link)
    js.URL.revokeObjectURL(url)

    show_message("File successfully downloaded.", "success")

def setup():
    change_proxy = create_proxy(selectChange)
    file_input_proxy = create_proxy(handle_file_upload)
    load_button_proxy = create_proxy(load_data_click)

    document.getElementById("select").addEventListener("change", change_proxy)
    document.getElementById("fileInput").addEventListener("change", file_input_proxy)
    document.getElementById("loadDataBtn").addEventListener("click", load_button_proxy)

    download_button_proxy = create_proxy(download_processed_data)
    document.getElementById("downloadBtn").addEventListener("click", download_button_proxy)

def show_message(msg, alert_type="info"):
    message_div = document.getElementById("message")
    message_div.className = f"alert alert-{alert_type}"
    message_div.innerText = msg
    message_div.style.display = "block"

setup()
plot(qc_test="gross_range_test")

