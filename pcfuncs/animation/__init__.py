import json
import logging

import azure.functions as func
from pydantic import ValidationError


from .animation import PcMosaicAnimation
from .models import AnimationRequest, AnimationResponse
from .stamps.progress_bar import ProgressBarStamp
from .stamps.brand import BrandStamp
from .utils import upload_gif

from funclib.errors import BBoxTooLargeError


async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            status_code=400,
            mimetype="application/text",
            body="Error: Invalid JSON",
        )

    try:
        parsed_request = AnimationRequest(**body)
    except ValidationError as e:
        return func.HttpResponse(
            status_code=400,
            mimetype="application/json",
            body=e.json(),
        )

    try:
        response = await handle_request(parsed_request)

        return func.HttpResponse(
            status_code=200,
            mimetype="application/json",
            body=response.json(),
        )
    except BBoxTooLargeError as e:
        logging.exception(e)
        return func.HttpResponse(
            status_code=400,
            mimetype="application/json",
            body=json.dumps({"error": str(e)}),
        )
    except Exception as e:
        logging.exception(e)
        return func.HttpResponse(
            status_code=500,
            mimetype="application/json",
        )


async def handle_request(req: AnimationRequest) -> AnimationResponse:
    stamps = []
    if req.show_progressbar:
        stamps.append(ProgressBarStamp)
    if req.show_branding:
        stamps.append(BrandStamp)

    animator = PcMosaicAnimation(
        bbox=req.bbox,
        zoom=req.zoom,
        cql=req.cql,
        render_params=req.get_encoded_render_params(),
        frame_duration=req.duration,
        stamps=stamps,
    )

    gif = await animator.get(
        req.get_relative_delta(),
        req.start,
        req.get_valid_frames(),
    )

    gif_url = upload_gif(gif, req.get_collection())
    return AnimationResponse(url=gif_url)
