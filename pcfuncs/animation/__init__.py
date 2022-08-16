import json
import logging

import azure.functions as func
from pydantic import ValidationError

from .animation import PcMosaicAnimation
from .models import AnimationRequest, AnimationResponse
from .utils import BBoxTooLargeError, upload_gif


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
    animator = PcMosaicAnimation(
        bbox=req.bbox,
        zoom=req.zoom,
        cql=req.cql,
        render_params=req.get_encoded_render_params(),
        frame_duration=req.duration,
    )

    gif = await animator.get(
        req.get_relative_delta(),
        req.start,
        req.get_valid_frames(),
    )

    gif_url = upload_gif(gif, req.get_collection())
    return AnimationResponse(url=gif_url)
