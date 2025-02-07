import time
import asyncio
import aiohttp
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Настройка драйвера
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{os.getpid()}")  # Уникальный профиль
    return webdriver.Chrome(options=options)



# Асинхронная функция для скачивания PDF
async def download_pdf(session, pdf_url):
    """Скачивает PDF файл по указанному URL и сохраняет его в директорию."""
    try:
        async with session.get(pdf_url) as response:
            if response.status == 200:
                pdf_name = pdf_url.split("/")[-1]
                year = pdf_url.split("/")[-6].split("=")[-1]
                save_directory = os.path.join(os.getcwd(), f"pdf/{year}")
                os.makedirs(save_directory, exist_ok=True)
                pdf_path = os.path.join(save_directory, pdf_name)
                with open(pdf_path, "wb") as pdf_file:
                    while chunk := await response.content.read(1024):
                        pdf_file.write(chunk)
                print(f"PDF сохранен: {pdf_path}")
            else:
                print(f"Не удалось скачать PDF: {pdf_url}, статус: {response.status}")
    except Exception as e:
        print(f"Ошибка при скачивании PDF: {e}")


async def fetch_pdf_links(links):
    """Асинхронная загрузка страниц и поиск PDF-документов."""
    async with aiohttp.ClientSession() as session:
        for link in links:
            pdf_driver = create_driver()
            try:
                # Открываем новую вкладку для PDF
                pdf_driver.get(link)
                WebDriverWait(pdf_driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'pdf')]"))
                )
                iframe = pdf_driver.find_element(By.XPATH, "//iframe[contains(@src, 'pdf')]")
                pdf_url = iframe.get_attribute("src")
                print(f"PDF найден: {pdf_url}")

                # Асинхронное скачивание PDF файла
                await download_pdf(session, pdf_url)
            except TimeoutException:
                print(f"PDF не найден на странице: {link}")
            except Exception as e:
                print(f"Ошибка при обработке {link}: {e}")
            finally:
                pdf_driver.quit()


# Основная функция обработки
def main():
    print('Запущено')
    driver = create_driver()
    with open("patent_links.txt", "w") as file:
        try:
            url = "https://data.epo.org/publication-server/?lg=en"
            driver.get(url)

            # Ожидаем, пока кнопка с текстом "Search" станет кликабельной и находим её
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Search']"))
            )

            # Нажимаем на кнопку
            search_button.click()

            # Ждём загрузки страницы после нажатия
            time.sleep(2)

            all_links = []
            while True:
                # Ищем PDF ссылки на текущей странице
                pdf_links = driver.find_elements(By.XPATH, "//td[a/span[text()='PDF']]/a")
                for link in pdf_links:
                    href = link.get_attribute("href")
                    file.write(href + "\n")
                    all_links.append(href)


                # Асинхронная обработка найденных ссылок
                #asyncio.run(fetch_pdf_links(all_links))

                # Переход на следующую страницу
                try:
                    next_page = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "next-page-link"))
                    )
                    next_page.click()
                    time.sleep(2)
                except TimeoutException:
                    print("Нет следующей страницы.")
                    break
                except Exception as e:
                    print(f"Ошибка при переходе на следующую страницу: {e}")
                    #break
        finally:
            driver.quit()


if __name__ == "__main__":
    main()
