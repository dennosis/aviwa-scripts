import base64
from playwright.async_api import Page, Locator, async_playwright
from IPython.display import HTML, display


async def start_page() -> Page:
    # Iniciamos o gerenciador assíncrono
    pw = await async_playwright().start()

    # Lançamos o navegador (com a tela visível)
    browser = await pw.chromium.launch(headless=True)
    # Criamos o contexto e a página
    context = await browser.new_context()
    page = await context.new_page()

    return page


async def display_page(page: Page):
    html_content = await page.content()
    encoded = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    display(
        HTML(f"""
        <iframe src="data:text/html;base64,{encoded}"
                width="100%"
                height="600"
                style="border:none;">
        </iframe>
    """)
    )


async def check_exist_element(element: Locator, name: str) -> bool:
    count = await element.count()
    if count == 0:
        raise ValueError(f"O elemento '{name}' não está sendo encontrado")
    return True


async def redirect_to_url(page: Page, url: str):
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
