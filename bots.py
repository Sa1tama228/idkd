import time
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
import random
import requests
from io import BytesIO

bot = Bot(token='6413776546:AAFn6X1n-Fuuay7kLnorDMGOUFeHo2WsIj8')
dp = Dispatcher(bot)


def generate_user_agent():
    platforms = [
        "Windows NT 10.0; Win64; x64",
        "Windows NT 10.0; Win32; x32",
        "Macintosh; Intel Mac OS X 10_15_7",
        "Macintosh; Intel Mac OS X 11_2_3",
        "X11; Ubuntu; Linux x86_64",
        "iPhone; CPU iPhone OS 14_6 like Mac OS X",
        "iPhone; CPU iPhone OS 15_2 like Mac OS X",
        "iPad; CPU OS 14_7 like Mac OS X",
        "Linux; Android 11; SM-G998B"
    ]

    webkits = [
        "AppleWebKit/537.36 (KHTML, like Gecko)",
        "AppleWebKit/605.1.15 (KHTML, like Gecko)"
    ]

    browsers = [
        "Chrome/91.0.4472.124",
        "Chrome/92.0.4515.107",
        "Firefox/90.0",
        "Firefox/91.0",
        "Safari/604.1",
        "Safari/537.36",
        "Edge/92.0.902.67"
    ]

    extras = [
        " Mobile/15E148",
        " Version/15.0 Mobile/15E148",
        " Version/14.1.1 Mobile/15E148"
    ]

    platform = random.choice(platforms)
    webkit = random.choice(webkits)
    browser = random.choice(browsers)
    extra = random.choice(extras)

    return f"Mozilla/5.0 ({platform}) {webkit} {browser}{extra}"


# Генерация списка user-agent строк
USER_AGENTS = [generate_user_agent() for _ in range(10)]


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply(
        "Привет! Я выгружаю с авито объявления телефонов. Напиши сколько последних объявлений (от 2 до 50) выгрузить и увидишь результат."
    )

@dp.message_handler()
async def get_avito_ads(message: types.Message):
    try:
        number_of_ads = int(message.text)
        if not 2 <= number_of_ads <= 50:
            raise ValueError

        await message.reply("Начинаю выгружать данные...")
        url = "https://www.avito.ru/sankt-peterburg/telefony/mobilnye_telefony/apple-ASgBAgICAkS0wA3OqzmwwQ2I_Dc?s=104"

        options = uc.ChromeOptions()
        options.add_argument("window-size=1200x600")
        options.add_argument(USER_AGENTS[random.randint(0, len(USER_AGENTS))])
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument('--headless')

        driver = uc.Chrome(options=options, version_main=125)  # я поменял версию на свою

        ad_list = []
        seen_ads = set()

        try:
            while True:
                driver.get(url)
                driver.implicitly_wait(10)

                all_ads_on_page = driver.find_elements(By.CSS_SELECTOR, 'div[data-marker="item"]')
                new_ads_found = False

                for count, ad in enumerate(all_ads_on_page[:number_of_ads]):
                    ad_data = {}
                    try:
                        ad_data['Цена'] = ad.find_element(By.CSS_SELECTOR, 'meta[itemprop="price"]').get_attribute("content")
                    except:
                        ad_data['Цена'] = "Нет цены в объявлении"
                    try:
                        ad_data['URL'] = ad.find_element(By.CSS_SELECTOR, 'a[itemprop="url"]').get_attribute("href")
                    except:
                        ad_data['URL'] = "Нет ссылки на объявление"

                    if ad_data['URL'] in seen_ads:
                        continue  # скип рекламы

                    try:
                        ad_data['Название'] = ad.find_element(By.CSS_SELECTOR, 'h3[itemprop="name"]').text
                    except:
                        ad_data['Название'] = "Нет названия объявления"
                    try:
                        ad_data['Адрес'] = ad.find_element(By.CSS_SELECTOR, 'div[class="geo-root-zPwRk"] > span').text
                        print(ad_data['Адрес'])
                    except:
                        ad_data['Адрес'] = "Нет адреса в объявлении"
                    try:
                        ad_data['Описание'] = ad.find_element(By.CSS_SELECTOR, 'div[class="iva-item-descriptionStep-C0ty1"').text
                    except:
                        ad_data['Описание'] = "Нет описания в объявлении"
                    try:
                        img_url = ad.find_element(By.CSS_SELECTOR, 'img[itemprop="image"]').get_attribute("src")
                        ad_data['Фото'] = requests.get(img_url).content
                    except:
                        ad_data['Фото'] = None

                    seen_ads.add(ad_data['URL'])
                    new_ads_found = True

                    await message.reply(
                        f"Имя объявления: {ad_data['Название']}\n"
                        f"URL объявления: {ad_data['URL']}\n"
                        f"Цена в объявлении: <b>{ad_data['Цена']}</b>\n"
                        f"Описание объявления: {ad_data['Описание']}\n"
                        f"Адрес в объявлении: {ad_data['Адрес']}\n"
                    )
                    if ad_data['Фото']:
                        await message.reply_photo(photo=BytesIO(ad_data['Фото']), caption="Фото объявления")
                    await message.reply(f"Обработано объявлений: {count + 1} из {number_of_ads}")

                if not new_ads_found:
                    await message.reply("Новых объявлений нет.")

                time.sleep(5)  # задержка по рефрешу

        except Exception as ex:
            await message.reply(f"Произошла ошибка: {ex}")
        finally:
            driver.quit()
    except ValueError:
        await message.reply("Нужно указать целое число от 2 до 50 включительно! Попробуй еще раз!")
    except Exception as ex:
        await message.reply(f"Произошла ошибка: {ex}")

if __name__ == '__main__':
    executor.start_polling(dp)
