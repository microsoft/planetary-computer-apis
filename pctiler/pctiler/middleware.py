import json

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class ModifyResponseMiddleware:
    def __init__(self, app: ASGIApp, route: str) -> None:
        self.app = app
        self.route = route

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] != self.route:
            return await self.app(scope, receive, send)

        async def send_with_searchid(message: Message) -> None:
            message_type = message["type"]
            if message_type == "http.response.start":
                # Don't send the initial message until we've determined how to
                # modify the outgoing content-length header.
                self.initial_message = message
            elif message_type == "http.response.body":
                # Rewrite id to searchid for backwards compatibility, keep key order
                body = json.loads(message["body"])
                body["searchid"] = body.get("id")

                updated_links = []
                for link in body.get("links", []):
                    link["href"] = link["href"].replace("/{tileMatrixSetId}", "")
                    updated_links.append(link)

                body["links"] = updated_links

                resp_body = json.dumps(body, ensure_ascii=False).encode("utf-8")
                message["body"] = resp_body

                # Update the content-length header on the start message
                headers = MutableHeaders(scope=self.initial_message)
                headers["Content-Length"] = str(len(resp_body))

                # Send the start and body asgi messages
                await send(self.initial_message)
                await send(message)

            else:
                await send(message)

        await self.app(scope, receive, send_with_searchid)
