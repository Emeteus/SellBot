# bot.py

import telebot
from telebot import types
from sqlalchemy.orm import sessionmaker

from config import TOKEN
from database import engine, RentOffer, SaleOffer

bot = telebot.TeleBot(TOKEN)
Session = sessionmaker(bind=engine)
session = Session()

user_titles = {}
user_prices = {}


@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.reply_to(message, f"Привіт {user_name}! Я бот, створенний найкращим у світі прогером Emeteus))!")
    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAELWjxlxTKJC4JeWCXbCBaT8trFGZPwQQACXhgAAogOKEhUGNKuQ9GUEDQE')
    bot.send_message(message.chat.id, "Щоб почати користуватись ботом, просто натисніть кнопку:",
                     reply_markup=get_keyboard())


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text.startswith('/'):
        bot.reply_to(message, "Прочисти очі чумба, у мене нема такої команди.")
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAELWkJlxTK8tWWiRUXPPrWunF9AgHWo-wAC9QADVp29Cq5uEBf1pScoNAQ')
    else:
        bot.reply_to(message, "Вибач чумба, але я не розумію що ти від мене хочеш.")
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAELWkZlxTLHXzT6BGHbjcm02iAx2NRzmAAC-QADVp29CpVlbqsqKxs2NAQ')


def get_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="Оренда", callback_data="rent_0")
    button2 = types.InlineKeyboardButton(text="Продажа", callback_data="sale_0")
    button3 = types.InlineKeyboardButton(text="Додати", callback_data="create_offer")
    keyboard.row(button1, button2)
    keyboard.row(button3)
    return keyboard


def get_pagination_keyboard(category, page):
    keyboard = types.InlineKeyboardMarkup()
    prev_button = types.InlineKeyboardButton(text="Назад", callback_data=f"{category}_{page - 1}")
    next_button = types.InlineKeyboardButton(text="Далі", callback_data=f"{category}_{page + 1}")
    home_button = types.InlineKeyboardButton(text="На головну", callback_data="home")
    keyboard.row(prev_button, next_button)
    keyboard.row(home_button)
    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data.startswith("rent"):
        handle_offer_pagination(call, "rent")
    elif call.data.startswith("sale"):
        handle_offer_pagination(call, "sale")
    elif call.data == "create_offer":
        bot.answer_callback_query(call.id, "Виберіть тип оголошення:")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                      reply_markup=get_three_buttons_keyboard())
    elif call.data == "back":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_keyboard())
    elif call.data == "add_rent":
        request_rent_information(call.message.chat.id)
    elif call.data == "add_sale":
        request_sale_information(call.message.chat.id)
    elif call.data == "home":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_keyboard())


def request_sale_information(chat_id):
    bot.send_message(chat_id, "Введіть назву оголошення для продажу (наприклад, 'Продається квартира в центрі'):")
    bot.register_next_step_handler_by_chat_id(chat_id, request_sale_price)


def request_sale_price(message):
    chat_id = message.chat.id
    user_title = message.text
    bot.send_message(chat_id, "Введіть ціну продажу в гривнях:")
    bot.register_next_step_handler_by_chat_id(chat_id, request_sale_photo, user_title)


def request_sale_photo(message, user_title):
    chat_id = message.chat.id
    price = message.text
    bot.send_message(chat_id, "Будь ласка, надішліть фотографію вашого житла для продажу.")
    user_titles[chat_id] = user_title
    user_prices[chat_id] = price  # Добавляем сохранение цены в словарь
    bot.register_next_step_handler(message, save_sale_listing)


def request_rent_information(chat_id):
    bot.send_message(chat_id, "Введіть назву оголошення для оренди (наприклад, 'Здається квартира в центрі'):")
    bot.register_next_step_handler_by_chat_id(chat_id, request_rent_price)


def request_rent_price(message):
    chat_id = message.chat.id
    user_title = message.text
    bot.send_message(chat_id, "Введіть ціну оренди в гривнях:")
    bot.register_next_step_handler_by_chat_id(chat_id, request_rent_photo, user_title)


def request_rent_photo(message, user_title):
    chat_id = message.chat.id
    price = message.text
    bot.send_message(chat_id, "Будь ласка, надішліть фотографію вашого житла для оренди.")
    user_titles[chat_id] = user_title
    user_prices[chat_id] = price
    bot.register_next_step_handler(message, save_rent_listing)


def save_rent_listing(message):
    chat_id = message.chat.id
    photo = None
    if message.content_type == 'photo':
        photo = message.photo[-1].file_id
    title = user_titles[chat_id]
    price = user_prices.get(chat_id)  # Modified line
    print(f"Debug: Saving a rental ad: Title - {title}, Price - {price}")
    save_rent_offer(chat_id, title, photo, price, message)


def save_sale_listing(message):
    chat_id = message.chat.id
    photo = None
    if message.content_type == 'photo':
        photo = message.photo[-1].file_id
    title = user_titles[chat_id]
    price = user_prices.get(chat_id)  # Modified line
    print(f"Debug: Сохранение объявления о продаже: Название - {title}, Цена - {price}")
    save_sale_offer(chat_id, title, photo, price, message)


def save_rent_offer(chat_id, title, photo, price, message):
    price_str = str(price) if price is not None else ''
    new_rent_offer = RentOffer(title=title, price=price_str, photo=photo)
    session.add(new_rent_offer)
    session.commit()
    bot.send_message(chat_id, "Дякую! Ваше оголошення про оренду успішно додано.")
    start(message)


def save_sale_offer(chat_id, title, photo, price, message):
    price_str = str(price) if price is not None else ''
    new_sale_offer = SaleOffer(title=title, price=price_str, photo=photo)
    session.add(new_sale_offer)
    session.commit()
    bot.send_message(chat_id, "Дякуємо! Ваше оголошення про продаж успішно додано.")
    start(message)


def handle_offer_pagination(call, category):
    data_parts = call.data.split("_")
    if len(data_parts) == 2:
        page = int(data_parts[1])
        send_offer(call.message.chat.id, category, page)
    elif len(data_parts) == 1:
        page = 0
        send_offer(call.message.chat.id, category, page)
    else:
        bot.send_message(call.message.chat.id, "Error processing pagination")


def get_three_buttons_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="Додати аренду", callback_data="add_rent")
    button2 = types.InlineKeyboardButton(text="Додати продаж", callback_data="add_sale")
    button3 = types.InlineKeyboardButton(text="Назад", callback_data="back")
    keyboard.row(button1, button2, button3)
    return keyboard


def send_offer(chat_id, category, page):
    if category == "rent":
        offers = session.query(RentOffer).all()
    else:
        offers = session.query(SaleOffer).all()

    if not offers:
        bot.send_message(chat_id, f"Поки немає оголошень про {category}.")
        return

    max_page = (len(offers) - 1) // 1
    if page < 0:
        page = max_page
    elif page > max_page:
        page = 0

    offer = offers[page]
    bot.send_photo(chat_id, offer.photo,
                   caption=f"Назва: {offer.title}\nЦіна: {offer.price if offer.price else 'Не вказано'} грн",
                   reply_markup=get_pagination_keyboard(category, page))


if __name__ == '__main__':
    bot.polling(none_stop=True)
