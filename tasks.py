import os
from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
from robocorp.log import setup_log, info, debug
import shutil

ORDER_WEBSITE_URL = "https://robotsparebinindustries.com/#/robot-order"
ORDERS_CSV_URL = "https://robotsparebinindustries.com/orders.csv"
head_list = {
    "1": "Roll-a-thor head",
    "2": "Peanut crusher head",
    "3": "D.A.V.E head",
    "4": "Andy Roid head",
    "5": "Spanner mate head",
    "6": "Drillbit 2000 head",
}

mm = "🥝 🥝 🥝 Level 2 Robot: 🍎 "


@task
def order_robot_from_robot_spare_bin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    info(f"{mm} Starting the robot order task....")

    # browser.configure(headless=True)
    browser.configure(headless=False, slowmo=500)

    open_robot_order_website()
    download_orders()
    get_orders_and_submit()
    archive_receipts()
    finish()


def open_robot_order_website():
    """Navigates to the Robot Order Website"""
    debug(f"{mm} Opening {ORDER_WEBSITE_URL}")
    browser.goto(ORDER_WEBSITE_URL)
    page = browser.page()
    page.click("text=OK")
    debug(f"{mm} Opened {ORDER_WEBSITE_URL} and clicked OK")


def download_orders():
    """Downloads the orders file from the give URL"""
    debug(f"{mm} Downloading {ORDERS_CSV_URL}")
    http = HTTP()
    http.download(ORDERS_CSV_URL, overwrite=True)
    debug(f"{mm} Downloaded {http}")


def order_another_bot():
    """Clicks on order another bot button"""
    debug(f"{mm} Clicking on order another button")
    page = browser.page()
    page.click("#order-another")


def clicks_ok():
    """Clicks on ok whenever a new order is made for bots"""
    debug(f"{mm} Clicking on OK")
    page = browser.page()
    page.click("text=OK")


def get_orders_and_submit():
    """Read data from csv and fill in the robot order form"""
    debug(f"{mm} Filling in the robot order form")

    csv_file = Tables()
    robot_orders = csv_file.read_table_from_csv("orders.csv")
    for order in robot_orders:
        submit_order(order)


def submit_order(order):
    """Fills in the robot order details and submits the Order"""
    debug(f"{mm} Filling in the robot order form: {order}")
    page = browser.page()
    head_number = order["Head"]
    page.select_option("#head", head_list.get(head_number))
    #
    page.click(
        '//*[@id="root"]/div/div[1]/div/div[1]/form/div[2]/div/div[{0}]/label'.format(
            order["Body"]
        )
    )
    page.fill("input[placeholder='Enter the part number for the legs']", order["Legs"])
    page.fill("#address", order["Address"])

    # Error handling and retry logic
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            page.click("#order")
            order_another = page.query_selector("#order-another")
            debug(f"{mm} Order another: {order_another}")
            if order_another:
                debug(f"{mm} store_receipt_as_pdf")
                pdf_path = store_receipt_as_pdf(int(order["Order number"]))
                screenshot_path = get_screenshot_path(int(order["Order number"]))
                embed_screenshot_to_receipt(screenshot_path, pdf_path)
                order_another_bot()
                clicks_ok()
                break
            else:
                debug(f"{mm} Order failed. Retrying...")
                retry_count += 1
        except Exception as e:
            debug(f"{mm} Error submitting order: {e}")
            retry_count += 1

    if retry_count == max_retries:
        debug(f"{mm} Order failed after {max_retries} retries. Skipping.")


def store_receipt_as_pdf(order_number):
    """This stores the robot order receipt as pdf"""
    debug(f"{mm} Storing the robot order receipt as pdf")
    page = browser.page()
    order_receipt_html = page.locator("#receipt").inner_html()
    debug(f"{mm} Order receipt HTML: {order_receipt_html}")
    pdf = PDF()
    pdf_path = f"output/receipts/{order_number}.pdf"
    pdf.html_to_pdf(order_receipt_html, pdf_path)
    return pdf_path


def get_screenshot_path(order_number):
    """Takes screenshot of the ordered bot image"""
    debug(f"{mm} Taking screenshot of the ordered robot")
    page = browser.page()
    path = f"output/screenshots/{order_number}.png"
    page.locator("#robot-preview-image").screenshot(path=path)
    return path


def embed_screenshot_to_receipt(image_path, pdf_path):
    """Embeds the screenshot to the bot receipt"""
    debug(
        f"{mm} Embedding the screenshot to the bot receipt, image_path: {image_path} pdf_path: {pdf_path}"
    )
    pdf = PDF()
    pdf.add_watermark_image_to_pdf(
        image_path=image_path, source_path=pdf_path, output_path=pdf_path
    )


def archive_receipts():
    """Archives all the receipt pdf's into 1 zip archive"""
    debug(f"{mm} Zipping up the receipts ...")
    archiver = Archive()
    archiver.archive_folder_with_zip("./output/receipts", "./output/receipts.zip")


def finish():
    """Removes the folders where receipts, screenshots and orders are temporarily saved."""
    debug(f"{mm} Cleaning up the folders and stable muck!")
    shutil.rmtree("./output/receipts")
    shutil.rmtree("./output/screenshots")
    os.remove("orders.csv")
    debug(
        f"{mm} removed unnecessary files. Robot has completed it's work! 🥬 🥬 🥬 Done!"
    )
