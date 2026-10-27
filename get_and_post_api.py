# uvicorn get_and_post_api:app --reload

from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

import os

os.environ["OMP_NUM_THREADS"] = "1"

import math
import multiprocessing
from typing import List

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from starlette.middleware.gzip import GZipMiddleware
from mpire import WorkerPool

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import RedirectResponse



filename = os.path.basename(__file__).split(".")[0]

app = FastAPI(
    title=filename,
    version="1.0.0"
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")



@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/docs")

class UserInput(BaseModel):
    name: str
    age: int

my_dict = {}

@app.get("/enter-names")
def get_data(name: str,age: int = Query(..., ge=1, le=100)):
    my_dict[name] = age
    return {"name": name, "age": my_dict[name]}

@app.post("/get-names")
def post_data():
    return my_dict


