from django.http import JsonResponse
from rest_framework.decorators import api_view
from playwright.async_api import async_playwright
from asgiref.sync import async_to_sync


@api_view(["GET"])
def scrape_data(request):
    return async_to_sync(scrape_data_async)(request)


async def scrape_data_async(request):
    facebook_data = []
    instagram_data = []
    GENERAL_LABELS_SIZE = 5
    GENERAL_TABLE_SIZE = 11
    URL = "https://lookerstudio.google.com/u/0/reporting/36960dab-5e03-4c64-8b14-cf4c76c61e40/page/p_pj1bqu80od?s=spVfW1z_NAs"
    labels = [
        "Impresiones",
        "Reacciones",
        "Alcance",
        "Costo por reacción",
        "Reproducciones (15 seg)",
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(URL, wait_until="load", timeout=120000)

        await page.wait_for_selector("div.valueLabel", timeout=120000)
        await page.wait_for_selector("div.cell", timeout=120000)

        value_label_elements = await page.query_selector_all("div.valueLabel")
        value_label_cells = await page.query_selector_all("div.cell")

        general_labels_data = [await el.inner_text() for el in value_label_elements]

        def general_labels():
            return [
                {"title": labels[i], "value": general_labels_data[i]}
                for i in range(GENERAL_LABELS_SIZE)
            ]

        cells_labels = [await cell.inner_text() for cell in value_label_cells]

        array_chunked = [
            cells_labels[i : i + GENERAL_TABLE_SIZE]
            for i in range(0, len(cells_labels), GENERAL_TABLE_SIZE)
        ]

        is_section_two = False
        for chunk in array_chunked:
            if chunk[0] == "1.":
                is_section_two = not is_section_two

            if is_section_two:
                instagram_data.append(chunk)
            else:
                facebook_data.append(chunk)

        await browser.close()

    return JsonResponse(
        {
            "generalLabels": general_labels(),
            "facebookData": facebook_data,
            "instagramData": instagram_data,
        }
    )
