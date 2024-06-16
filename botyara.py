import time
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
import random
import requests
from io import BytesIO
from datetime import datetime, timedelta

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


# Генерация списка юзер агентов строк
USER_AGENTS = [generate_user_agent() for _ in range(10)]


def convert_time(publication_time):
    now = datetime.now()

    if "секунд" in publication_time or "минут" in publication_time or "час" in publication_time:
        if "секунд" in publication_time:
            seconds_ago = int(publication_time.split()[0])
            publication_time = now - timedelta(seconds=seconds_ago)
        elif "минут" in publication_time:
            minutes_ago = int(publication_time.split()[0])
            publication_time = now - timedelta(minutes=minutes_ago)
        elif "час" in publication_time:
            hours_ago = int(publication_time.split()[0])
            publication_time = now - timedelta(hours=hours_ago)
    else:
        if "Сегодня" in publication_time:
            time_part = publication_time.split(", ")[1]
            publication_time = datetime.strptime(f"{now.date()} {time_part}", "%Y-%m-%d %H:%M")
        elif "Вчера" in publication_time:
            time_part = publication_time.split(", ")[1]
            yesterday = now - timedelta(days=1)
            publication_time = datetime.strptime(f"{yesterday.date()} {time_part}", "%Y-%m-%d %H:%M")
        else:
            return publication_time

    return publication_time.strftime("%d.%m.%y %H:%M:%S")


def convert_to_mobile_url(desktop_url):
    try:
        ad_id = desktop_url.split('_')[-1].split('?')[0]
        mobile_url = f"https://avito.ru/{ad_id}"
        return mobile_url
    except Exception as e:
        return desktop_url


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
        url = "https://m.avito.ru/sankt_peterburg_i_lo/telefony/mobilnye_telefony/apple-ASgBAgICAkS0wA3OqzmwwQ2I_Dc?context=H4sIAAAAAAAAA0u0MrSqLraysFJKK8rPDUhMT1WyLrYys1LKzMvJzANyagF-_ClVIgAAAA&geoCoords=59.939095%2C30.315868&radius=0&s=104&presentationType=serp"

        options = uc.ChromeOptions()
        options.add_argument("window-size=1200x600")
        options.add_argument(USER_AGENTS[random.randint(0, len(USER_AGENTS) - 1)])
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = uc.Chrome(options=options, version_main=125)

        seen_ads = set()

        while True:
            try:
                driver.get(url)
                driver.implicitly_wait(10)

                all_ads_on_page = driver.find_elements(By.CSS_SELECTOR, 'div[data-marker="item"]')
                new_ads_found = False

                for count, ad in enumerate(all_ads_on_page[:number_of_ads]):
                    ad_data = {}
                    try:
                        ad_data['Цена'] = ad.find_element(By.CSS_SELECTOR, 'meta[itemprop="price"]').get_attribute(
                            "content")
                    except:
                        ad_data['Цена'] = "Нет цены в объявлении"
                    try:
                        desktop_url = ad.find_element(By.CSS_SELECTOR, 'a[itemprop="url"]').get_attribute("href")
                        ad_data['URL'] = convert_to_mobile_url(desktop_url)
                    except:
                        ad_data['URL'] = "Нет ссылки на объявление"

                    if ad_data['URL'] in seen_ads:
                        continue  # Skip ads we've already seen

                    try:
                        ad_data['Название'] = ad.find_element(By.CSS_SELECTOR, 'h3[itemprop="name"]').text
                    except:
                        ad_data['Название'] = "Нет названия объявления"

                    try:
                        address_element = ad.find_element(By.CSS_SELECTOR, '.geo-root-zPwRk')
                        ad_data['Адрес'] = address_element.text
                    except:
                        ad_data['Адрес'] = "Нет адреса в объявлении"

                    try:
                        time_element = ad.find_element(By.CSS_SELECTOR, 'p[data-marker="item-date"]')
                        raw_time = time_element.text
                        ad_data['Время публикации'] = convert_time(raw_time)
                    except:
                        ad_data['Время публикации'] = "Нет времени публикации"

                    try:
                        ad_data['Описание'] = ad.find_element(By.CSS_SELECTOR, 'div[class*="descriptionStep"]').text
                    except:
                        ad_data['Описание'] = "Нет описания в объявлении"
                    try:
                        img_url = ad.find_element(By.CSS_SELECTOR, 'img[itemprop="image"]').get_attribute("src")
                        ad_data['Фото'] = requests.get(img_url).content
                    except:
                        ad_data['Фото'] = None

                    seen_ads.add(ad_data['URL'])
                    new_ads_found = True

                    caption = (
                        f"<b>{ad_data['Название']}</b>\n"
                        f"💸<b>{ad_data['Цена']} ₽</b>\n"
                        f"{ad_data['Адрес']}\n"
                        f"🕒<b>{ad_data['Время публикации']}</b>\n"
                        f"{ad_data['URL']}\n\n"
                        f"<b>{ad_data['Описание']}</b>\n"
                    )
                    if ad_data['Фото']:
                        await bot.send_photo(message.chat.id, photo=BytesIO(ad_data['Фото']), caption=caption,
                                             parse_mode='HTML')
                    else:
                        await message.reply(caption, parse_mode='HTML')

                time.sleep(3)  # Refresh the page every 3 seconds

            except Exception as ex:
                await message.reply(f"Произошла ошибка: {ex}")

    except ValueError:
        await message.reply("Нужно указать целое число от 2 до 50 включительно! Попробуй еще раз!")
    except Exception as ex:
        await message.reply(f"Произошла ошибка: {ex}")


if __name__ == '__main__':
    executor.start_polling(dp)
