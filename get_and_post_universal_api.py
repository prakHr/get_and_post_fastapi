
import os
os.environ["OMP_NUM_THREADS"] = "1"

from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from starlette.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, create_model, Field

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


# -----------------------------
# Request models
# -----------------------------

class FieldConfig(BaseModel):
    type: str
    required: bool = True


class CreateModelRequest(BaseModel):
    model_name: str
    params: dict[str, FieldConfig]


# Store generated models and data
dynamic_models: dict[str, type[BaseModel]] = {}
my_dict: dict[str, Any] = {}


# Allowed field types
ALLOWED_TYPES = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
}


# -----------------------------
# Create a model dynamically
# -----------------------------

@app.post("/create-model")
def create_dynamic_model(request: CreateModelRequest):
    if not request.model_name.isidentifier():
        raise HTTPException(
            status_code=400,
            detail="Invalid model name"
        )

    if not request.params:
        raise HTTPException(
            status_code=400,
            detail="At least one parameter is required"
        )

    model_fields = {}

    for field_name, config in request.params.items():
        if not field_name.isidentifier():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field name: {field_name}"
            )

        field_type = ALLOWED_TYPES.get(config.type.lower())

        if field_type is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported type '{config.type}' "
                    f"for field '{field_name}'. "
                    f"Allowed types: {list(ALLOWED_TYPES)}"
                )
            )

        if config.required:
            model_fields[field_name] = (field_type, ...)
        else:
            model_fields[field_name] = (
                Optional[field_type],
                None
            )

    model = create_model(
        request.model_name,
        **model_fields
    )

    dynamic_models[request.model_name] = model

    return {
        "message": "Model created successfully",
        "model_name": request.model_name,
        "fields": {
            name: {
                "type": config.type,
                "required": config.required
            }
            for name, config in request.params.items()
        }
    }


# -----------------------------
# Validate data using the model
# -----------------------------

@app.post("/validate-data/{model_name}")
def validate_dynamic_data(
    model_name: str,
    data: dict[str, Any]
):
    model = dynamic_models.get(model_name)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found. Create it first."
        )

    try:
        validated_data = model.model_validate(data)
        return {
            "message": "Data validated successfully",
            "model_name": model_name,
            "data": validated_data.model_dump()
        }

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )



from typing import Any
from fastapi import HTTPException, Query

# Store validated records by model name
my_dict: dict[str, list[dict[str, Any]]] = {}


@app.post("/enter-names/{model_name}")
def get_data(
    model_name: str,
    data: dict[str, Any]
):
    # Find the dynamically created model
    model = dynamic_models.get(model_name)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found. Create it first."
        )

    # Validate the incoming data against that model
    try:
        validated_data = model.model_validate(data)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    # Save the validated data
    record = validated_data.model_dump()
    my_dict.setdefault(model_name, []).append(record)

    return {
        "message": "Data saved successfully",
        "model_name": model_name,
        "data": record
    }


@app.get("/get-names/{model_name}")
def post_data(model_name: str):
    # Check that the model exists
    if model_name not in dynamic_models:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found. Create it first."
        )

    return {
        "model_name": model_name,
        "data": my_dict.get(model_name, [])
    }
