
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import pandas as pd
import numpy_financial as npf

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def read_root():
    from fastapi.responses import FileResponse
    return FileResponse("index.html")

class InputData(BaseModel):
    name: str
    capex: float
    opex: float
    benefits: float
    years: int
    rate: float

@app.post("/calculate")
def calculate(data: list[InputData]):
    results = []
    for item in data:
        try:
            r = item.rate / 100
            cash_flows = [-item.capex] + [(item.benefits - item.opex)] * item.years
            try:
                irr = float(npf.irr(cash_flows))
                if np.isnan(irr):
                    irr = "N/A"
                else:
                    irr = round(irr, 4)
            except:
                irr = "N/A"
            df = pd.DataFrame({
                "Year": list(range(item.years + 1)),
                "CAPEX": [item.capex] + [0]*item.years,
                "OPEX": [0] + [item.opex]*item.years,
                "BENEFITS": [0] + [item.benefits]*item.years
            })
            df["DF"] = 1 / (1 + r)**df["Year"]
            total_costs = (df["CAPEX"] * df["DF"]).sum() + (df["OPEX"] * df["DF"]).sum()
            total_benefits = (df["BENEFITS"] * df["DF"]).sum()
            npv = round(total_benefits - total_costs, 2)
            cbr = round(total_benefits / total_costs, 4)
            results.append({
                "name": item.name,
                "capex": item.capex,
                "opex": item.opex,
                "benefits": item.benefits,
                "years": item.years,
                "rate": item.rate,
                "npv": npv,
                "irr": irr,
                "cbr": cbr
            })
        except Exception as e:
            results.append({ "name": item.name, "error": str(e) })
    return results
