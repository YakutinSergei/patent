import time
import asyncio
import aiohttp
import os
from datetime import datetime
from aiohttp import ClientSession
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Настройка драйвера (замените путь на путь к вашему драйверу)
driver = webdriver.Chrome()

# Открываем сайт
url = "https://data.epo.org/publication-server/?lg=en"
driver.get(url)


# Асинхронная функция для скачивания PDF
async def download_pdf(session, pdf_url):
    """Скачивает PDF файл по указанному URL и сохраняет его в директорию."""
    try:
        async with session.get(pdf_url) as response:
            if response.status == 200:
                print(f'{pdf_url=}')
                pdf_name = pdf_url.split("/")[-1]
                year = pdf_url.split("/")[-6].split("=")[-1]
                print(f'{pdf_name=}')
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
    # Создание директории для сохранения PDF

    async with ClientSession() as session:
        for link in links:
            try:
                # Переход по ссылке
                driver.get(link)

                # Поиск iframe с PDF
                iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'pdf')]"))
                )
                pdf_url = iframe.get_attribute("src")
                print(f"PDF найден: {pdf_url}")

                # Асинхронное скачивание PDF файла
                await download_pdf(session, pdf_url)

            except TimeoutException:
                print(f"PDF не найден на странице: {link}")
            except Exception as e:
                print(f"Ошибка при обработке {link}: {e}")


# Открываем файл для записи ссылок на патенты
with open("patent_links.txt", "w") as file:
    try:
        # Ожидаем, пока кнопка с текстом "Search" станет кликабельной и находим её
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Search']"))
        )

        # Нажимаем на кнопку
        search_button.click()

        # Ждём загрузки страницы после нажатия
        time.sleep(2)

        all_links = []
        i = 0
        while i < 2:
            # Ищем все теги <td>, содержащие <span> с текстом "PDF", и извлекаем ссылки
            pdf_links = driver.find_elements(By.XPATH, "//td[a/span[text()='PDF']]/a")

            # Сохраняем ссылки в список
            for link in pdf_links:
                print(link.get_attribute("href"))
                href = link.get_attribute("href")
                file.write(href + "\n")
                all_links.append(href)

            i += 1
            # Переход на следующую страницу
            try:
                next_page = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "next-page-link"))
                )
                next_page.click()
                time.sleep(1)
            except Exception as e:
                print("Нет следующей страницы или ошибка: ", e)
                break

            # Асинхронная обработка найденных ссылок
            #asyncio.run(fetch_pdf_links(all_links))

    finally:
        # Закрываем браузер
        driver.quit()
