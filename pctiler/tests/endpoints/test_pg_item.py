import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_item(client: AsyncClient) -> None:
    response = await client.get(
        "/item/info?collection=naip&item=al_m_3008501_ne_16_060_20191109_20200114"
    )
    assert response.status_code == 200

    response = await client.get(
        "/item/assets?collection=naip&item=al_m_3008501_ne_16_060_20191109_20200114"
    )
    assert response.status_code == 200
    assert response.json() == ["image"]


@pytest.mark.asyncio
async def test_item_preview_xss(client: AsyncClient) -> None:
    xss = "%27});alert('xss injected');//</script>"

    item_id = "al_m_3008501_ne_16_060_20191109_20200114"
    item_id_xss = f"{item_id}{xss}"

    response_xss = await client.get(f"/item/map?collection=naip&item={item_id_xss}")

    # The XSS should be sanitized out of the response
    assert response_xss.status_code == 200
    assert "//</script>" not in response_xss.text
