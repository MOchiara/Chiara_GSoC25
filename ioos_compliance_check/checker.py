
from js import document
from pyodide.ffi import create_proxy
from compliance_checker.runner import CheckSuite, ComplianceChecker
import io
import tempfile
import sys
from pyodide.ffi import to_js
import js

check_suite = CheckSuite()
check_suite.load_all_available_checkers()

def get_checker_list():
    check_suite = CheckSuite()
    check_suite.load_all_available_checkers()
    checkers = list(check_suite.checkers.keys())
    if len(checkers) == 0:
        print("No checkers found!")
    else:
        print('Populating')
        js.populate_dropdown(to_js(checkers))


from js import document  # or import js


def on_test_selected(event):
    select_element = document.getElementById("select")
    selected_index = select_element.selectedIndex
    selected_option = select_element.options.item(selected_index)

    selected_text = getattr(selected_option, 'text', None)
    output_div = document.getElementById("output-text")
    output_div.textContent = f"You selected: {selected_text}"


def on_file_selected(event):
    file_input = document.querySelector('input[type="file"]')
    if not file_input or file_input.files.length == 0:
        document.getElementById("filename-display").textContent = ""
        return

    file = file_input.files.item(0)
    document.getElementById("filename-display").textContent = f"Loaded file: {file.name}"


async def run_checker(event):
    from js import document
    file_input = document.querySelector('input[type="file"]')
    files = list(file_input.files)

    if not files:
        document.getElementById("status-msg").textContent = "No file selected."
        return

    file = files[0]
    checker_name = document.getElementById("select").value.split(":")[0]

    file_data = await file.arrayBuffer()
    data_bytes = bytes(file_data.to_py())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".nc") as tmp:
        tmp.write(data_bytes)
        tmp_path = tmp.name

    output_capture = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = output_capture

    try:
        passed, had_errors = ComplianceChecker.run_checker(
            ds_loc=tmp_path,
            checker_names=[checker_name],
            verbose=2,
            criteria="normal",
            output_filename="-",
            output_format="text",
        )

        sys.stdout = original_stdout

        output_text = output_capture.getvalue()
        status_msg = document.getElementById("status-msg")
        status_text = f"Passed: {passed}, Had errors: {had_errors}. Check report below"
        status_msg.textContent = status_text

        status_msg.className = "text-center"

        if passed and not had_errors:
            status_msg.classList.add("alert", "alert-success", "pass")
        else:
            status_msg.classList.add("alert", "alert-danger", "fail")

        document.getElementById("report-output").textContent = output_text

    except Exception as e:
        sys.stdout = original_stdout
        document.getElementById("status-msg").textContent = f"Error: {e}"

def setup():
    button = document.getElementById("submit-btn")
    button.addEventListener("click", create_proxy(run_checker))

    file_input = document.querySelector('input[type="file"]')
    if file_input:
        file_input.addEventListener("change", create_proxy(on_file_selected))

    select_element = document.getElementById("select")
    if select_element:
        select_element.addEventListener("change", create_proxy(on_test_selected))
        on_test_selected(None)

setup()
get_checker_list()