# -*- coding: utf-8 -*-
import telebot
from telebot import types
from tinydb import TinyDB, Query

# Базы данных
db_products = TinyDB('../data/products.json')
db_history = TinyDB('../data/history.json')

# Токен бота
TOKEN = "ВАШ_ТОКЕН_ТЕЛЕГРАМ"  # <- вставьте свой токен
bot = telebot.TeleBot(TOKEN)

# Главное меню с Inline кнопками
def main_menu_inline():
    markup = types.InlineKeyboardMarkup()
    
    btn_add = types.InlineKeyboardButton("Добавить товар", callback_data="add_product")
    btn_delete = types.InlineKeyboardButton("Удалить товар", callback_data="delete_product")
    btn_update = types.InlineKeyboardButton("Пополнение/Списание", callback_data="update_stock")
    btn_history = types.InlineKeyboardButton("История транзакций", callback_data="history")
    
    markup.row(btn_add, btn_delete)
    markup.row(btn_update, btn_history)
    return markup

# /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать в кассу!", reply_markup=main_menu_inline())

# Обработка нажатий на Inline кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_inline(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "add_product":
        bot.send_message(chat_id, "Введите название и цену товара через запятую (например: Молоко,50)")
        bot.register_next_step_handler_by_chat_id(chat_id, add_product)

    elif data == "delete_product":
        bot.send_message(chat_id, "Введите название товара для удаления")
        bot.register_next_step_handler_by_chat_id(chat_id, delete_product)

    elif data == "update_stock":
        bot.send_message(chat_id, "Введите: название, количество (например: Молоко,5 или Молоко,-3)")
        bot.register_next_step_handler_by_chat_id(chat_id, update_stock)

    elif data == "history":
        show_history_by_chat(chat_id)

# Функции операций

# Добавление товара
def add_product(message):
    try:
        parts = [x.strip() for x in message.text.split(",")]
        if len(parts) != 2:
            raise ValueError("Неверный формат")
        name, price_str = parts
        price = float(price_str.replace(",", "."))  # поддержка запятой и точки
        db_products.insert({"name": name, "price": price, "stock": 0})
        bot.send_message(message.chat.id, f"Товар '{name}' добавлен! Остаток: 0")
        add_history("Добавление товара", name, price)
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка ввода! Введите в формате: Название,Цена (например: Молоко,50)")

# Удаление товара
def delete_product(message):
    try:
        name = message.text.strip()
        Product = Query()
        removed = db_products.remove(Product.name == name)
        if removed:
            bot.send_message(message.chat.id, f"Товар '{name}' удален!")
            add_history("Удаление товара", name)
        else:
            bot.send_message(message.chat.id, f"Товар '{name}' не найден!")
    except Exception:
        bot.send_message(message.chat.id, "Ошибка удаления товара!")

# Пополнение/Списание товара
def update_stock(message):
    try:
        parts = [x.strip() for x in message.text.split(",")]
        if len(parts) != 2:
            raise ValueError("Неверный формат")
        name, amount_str = parts
        amount = int(amount_str)
        Product = Query()
        item = db_products.search(Product.name == name)
        if not item:
            bot.send_message(message.chat.id, f"Товар '{name}' не найден!")
            return
        item = item[0]
        new_stock = item['stock'] + amount
        db_products.update({'stock': new_stock}, Product.name == name)
        action = "Пополнение" if amount > 0 else "Списание"
        bot.send_message(message.chat.id, f"{action} выполнено! Новый остаток: {new_stock}")
        add_history(action, name, amount)
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка ввода! Введите в формате: Название,Количество (например: Молоко,5)")
    except Exception:
        bot.send_message(message.chat.id, "Произошла ошибка при обновлении остатка!")

# Показ истории
def show_history_by_chat(chat_id):
    history = db_history.all()
    text = "\n".join([f"{h['action']} — {h['product']} ({h['amount']})" if h.get('amount') is not None else f"{h['action']} — {h['product']}" for h in history])
    if not text:
        text = "История пуста."
    bot.send_message(chat_id, text)

# Сохранение истории
def add_history(action, product_name, amount=None):
    if amount is not None:
        try:
            amount = float(amount)
        except:
            amount = str(amount)
    db_history.insert({"action": str(action), "product": str(product_name), "amount": amount})

# Запуск бота
bot.infinity_polling()
