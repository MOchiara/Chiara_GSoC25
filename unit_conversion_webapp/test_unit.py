from pyscript import document
from pyudunits2 import UnitSystem, Converter

def run_conversion(input_unit, output_unit, val):
    ut_system = UnitSystem.from_udunits2_xml()
    in_u = ut_system.unit(input_unit)
    out_u = ut_system.unit(output_unit)
    converter = Converter(in_u, out_u)
    output_val = converter.convert(float(val))
    return output_val, converter.expression

def convert_value(event=None):
    input_val = float(document.getElementById("input_value").value)
    input_unit = document.getElementById("input_unit").value
    output_unit = document.getElementById("output_unit").value

    try:
        converted, expression = run_conversion(input_unit, output_unit, input_val)
        document.getElementById("result").innerText = f"{input_val} {input_unit} = {converted} {output_unit}"
        document.getElementById("equation").innerText = expression
    except Exception as e:
        document.getElementById("result").innerText = f"Error: {e}"
        document.getElementById("equation").innerText = ""


