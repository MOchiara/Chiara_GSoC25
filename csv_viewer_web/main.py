from io import StringIO
import pandas as pd
from js import document, FileReader
from pyodide.ffi import create_proxy
from pyweb import pydom
from pyodide.http import open_url
from pyscript import display

url = "https://raw.githubusercontent.com/datasets/airport-codes/master/data/airport-codes.csv"
pydom["input#txt-url"][0].value = url

# Load CSV from URL
def loadFromURL(event):
    pydom["div#pandas-output-inner"].html = ""
    url = pydom["input#txt-url"][0].value

    df = pd.read_csv(open_url(url))

    pydom["div#pandas-output"].style["display"] = "block"
    display(df, target="pandas-output-inner", append="False")

# Load CSV from local file
def loadFromLocalFile(event):
    file_input = document.getElementById("file-input")
    file = file_input.files.item(0)
    reader = FileReader.new()

    def onload(event):
        csv_text = event.target.result
        df = pd.read_csv(StringIO(csv_text))
        pydom["div#pandas-output"].style["display"] = "block"
        pydom["div#pandas-output-inner"].html = df.to_html()

    reader.onload = create_proxy(onload)
    reader.readAsText(file)
