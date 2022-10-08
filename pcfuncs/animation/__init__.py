import json
import logging
from typing import Callable, List

import azure.functions as func
from funclib.errors import BBoxTooLargeError
from funclib.stamps.branding import LogoStamp
from funclib.stamps.progress_bar import ProgressBarStamp
from funclib.stamps.stamp import ImageStamp
from pydantic import ValidationError

from .animation import PcMosaicAnimation
from .models import AnimationRequest, AnimationResponse
from .settings import AnimationSettings
from .utils import upload_gif


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
    settings = AnimationSettings.get()
    stamps: List[Callable[[int, int], ImageStamp]] = []
    if req.show_progressbar:
        stamps.append(
            lambda frame_count, frame_number: ProgressBarStamp(
                frame_count, frame_number
            )
        )
    if req.show_branding:
        stamps.append(lambda x, y: LogoStamp())

    animator = PcMosaicAnimation(
        bbox=req.bbox,
        zoom=req.zoom,
        cql=req.cql,
        render_options=req.get_render_options(),
        settings=settings,
        stamps=stamps,
        frame_duration=req.duration,
        data_api_url_override=req.data_api_url,
    )

    gif = await animator.get(
        req.get_relative_delta(),
        req.start,
        req.get_valid_frames(),
    )

    gif_url = upload_gif(gif, req.get_collection())
    return AnimationResponse(url=gif_url)
