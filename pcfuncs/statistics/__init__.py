import json
import logging
from typing import Dict

import azure.functions as func
from funclib.errors import BBoxTooLargeError
from pydantic import ValidationError

from .models import StatisticsRequest
from .settings import StatisticsSettings
from .statistics import PcMosaicImage


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
        parsed_request = StatisticsRequest(**body)
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
            body=json.dumps(response),
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


async def handle_request(req: StatisticsRequest) -> Dict:
    settings = StatisticsSettings.get()

    mosaic_image = PcMosaicImage(
        bbox=req.bbox,
        zoom=req.zoom,
        cql=req.cql,
        render_options=req.get_render_options(),
        settings=settings,
        data_api_url_override=req.data_api_url,
    )

    img = await mosaic_image.get()

    return {k: v.dict() for k, v in img.statistics().items()}
