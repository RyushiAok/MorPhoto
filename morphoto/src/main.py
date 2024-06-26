import base64
import io
import os
from dotenv import load_dotenv

import modal
import uvicorn
from fastapi import FastAPI
from modal import asgi_app
from starlette.middleware.cors import CORSMiddleware
from omegaconf import OmegaConf
from PIL import Image
from configs import MorphotoConfig, DiffusionConfig
from models import InferenceRequest
from morphoto import Morphoto

morphoto_config = OmegaConf.create(MorphotoConfig)
morphoto = Morphoto(morphoto_config)
fastapi_app = FastAPI()

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://api.morphoto.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = modal.App("mophoto-fastapi")
modal_image = modal.Image.debian_slim().poetry_install_from_file(
    poetry_pyproject_toml="pyproject.toml", poetry_lockfile="poetry.lock"
)


@fastapi_app.post("/inference")
def inference(request: InferenceRequest) -> dict[str, str]:
    if request.is_mock:
        return {"converted_image": request.image, "prompt": request.prompt}
    image = io.BytesIO(base64.b64decode(request.image))
    image = Image.open(image)
    converted_image, prompt = morphoto.convert(request.prompt, image, request.strength)

    buffered = io.BytesIO()
    converted_image.save(buffered, format="PNG")
    converted_image = base64.b64encode(buffered.getvalue()).decode()
    result = {"converted_image": converted_image, "prompt": prompt}
    return result


@fastapi_app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "device": DiffusionConfig.device}


load_dotenv()
data_dir = os.getenv("DATA_DIR") or "data"


@app.function(
    image=modal_image,
    mounts=[modal.Mount.from_local_dir(data_dir, remote_path="/root/data")],
    secrets=[modal.Secret.from_name("morphoto-ml-secrets")],
    gpu="T4",
)
@asgi_app()
def fastapi_app() -> FastAPI:
    return fastapi_app


@app.local_entrypoint()
def main() -> None:
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
