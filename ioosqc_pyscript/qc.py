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
import asyncio


uploaded_df = None

test_params = {
    "gross_range_test": [
        {"name": "fail_span_min", "label": "Fail Span Min", "type": "number", "default": -10},
        {"name": "fail_span_max", "label": "Fail Span Max", "type": "number", "default": 10},
        {"name": "suspect_span_min", "label": "Suspect Span Min", "type": "number", "default": -2},
        {"name": "suspect_span_max", "label": "Suspect Span Max", "type": "number", "default": 3},
    ],
    "flat_line_test": [
        {"name": "tolerance", "label": "Tolerance", "type": "number", "default": 0.001},
        {"name": "suspect_threshold", "label": "Suspect Threshold", "type": "number", "default": 10800},
        {"name": "fail_threshold", "label": "Fail Threshold", "type": "number", "default": 21600},
    ],
    "rate_of_change_test": [
        {"name": "threshold", "label": "Threshold", "type": "number", "default": 0.001},
    ],
    "spike_test": [
        {"name": "suspect_threshold", "label": "Suspect Threshold", "type": "number", "default": 0.8},
        {"name": "fail_threshold", "label": "Fail Threshold", "type": "number", "default": 3},
    ]
}


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


def get_value_by_id(id):
    el = document.getElementById(id)
    if el is None:
        raise ValueError(f"Element with ID '{id}' not found.")
    return float(el.value)

def render_test_inputs(event=None):
    selected_test = document.getElementById("select").value
    container = document.getElementById("params-form")
    container.innerHTML = ""  # Clear existing

    for param in test_params[selected_test]:
        div = document.createElement("div")
        div.setAttribute("class", "form-group")

        label = document.createElement("label")
        label.innerText = param["label"]

        input_el = document.createElement("input")
        input_el.setAttribute("type", param["type"])
        input_el.setAttribute("class", "form-control")
        input_el.setAttribute("id", param["name"])
        input_el.setAttribute("value", str(param["default"]))

        div.appendChild(label)
        div.appendChild(input_el)
        container.appendChild(div)

def get_user_config(selected_test):
    config = {}
    if selected_test == "gross_range_test":
        config = {
            "fail_span": [
                get_value_by_id("fail_span_min"),
                get_value_by_id("fail_span_max")
            ],
            "suspect_span": [
                get_value_by_id("suspect_span_min"),
                get_value_by_id("suspect_span_max")
            ]
        }
    elif selected_test == "flat_line_test":
        config = {
            "tolerance": get_value_by_id("tolerance"),
            "suspect_threshold": get_value_by_id("suspect_threshold"),
            "fail_threshold": get_value_by_id("fail_threshold")
        }
    elif selected_test == "rate_of_change_test":
        config = {
            "threshold": get_value_by_id("threshold")
        }
    elif selected_test == "spike_test":
        config = {
            "suspect_threshold": get_value_by_id("suspect_threshold"),
            "fail_threshold": get_value_by_id("fail_threshold")
        }
    else:
        raise ValueError(f"Unknown test selected: {selected_test}")

    return {"qartod": {selected_test: config}}


def run_tests(df, variable, selected_test, use_defaults=False):
    if use_defaults:
        from pyodide.http import open_url
        config_file_path = "./qc_config.json"
        with open_url(config_file_path) as config_json:
            qc_config = json.load(config_json)
    else:
        qc_config = get_user_config(selected_test)


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

async def plot(qc_test, use_defaults=False):
    global uploaded_df
    loader = document.getElementById("loadingIndicator")
    if loader:
        loader.style.display = "block"

    await asyncio.sleep(0)
    try:
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

        result = run_tests(df, variable,qc_test, use_defaults=use_defaults)
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
    except Exception as e:
        show_message(f"Error during plotting: {e}", "danger")
        print(f"Plotting error: {e}")

    finally:
        if loader:
            loader.style.display = "none"
def selectChange(event):
    choice = document.getElementById("select").value
    print(f"Selected choice: {choice}")
    render_test_inputs()

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

def run_qc_test(event):
    global uploaded_df
    qc_test = document.getElementById("select").value
    if uploaded_df is None:
        show_message("No uploaded file found. Please upload a file first.", "warning")
        return
    try:
        plot(qc_test)
    except Exception as e:
        show_message(f"Error running test: {e}", "danger")
        print(f"Error: {e}")

def setup():
    change_proxy = create_proxy(selectChange)
    file_input_proxy = create_proxy(handle_file_upload)

    document.getElementById("select").addEventListener("change", change_proxy)
    document.getElementById("fileInput").addEventListener("change", file_input_proxy)

    download_button_proxy = create_proxy(download_processed_data)
    document.getElementById("downloadBtn").addEventListener("click", download_button_proxy)
    run_qc_proxy = create_proxy(run_qc_test)
    document.getElementById("runQcBtn").addEventListener("click", run_qc_proxy)
    select_change_proxy = create_proxy(render_test_inputs)
    document.getElementById("select").addEventListener("change", select_change_proxy)
    render_test_inputs()
    asyncio.ensure_future(run_default_plot())
def show_message(msg, alert_type="info"):
    message_div = document.getElementById("message")
    message_div.className = f"alert alert-{alert_type}"
    message_div.innerText = msg
    message_div.style.display = "block"
async def run_default_plot():
    qc_test = document.getElementById("select").value
    await plot(qc_test, use_defaults=True)
async def run_qc_test(event):
    global uploaded_df
    qc_test = document.getElementById("select").value
    if uploaded_df is None:
        show_message("No uploaded file found. Please upload a file first.", "warning")
        return
    try:
        plot(qc_test)
    except Exception as e:
        show_message(f"Error running test: {e}", "danger")
        print(f"Error: {e}")

setup()


