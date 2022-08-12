import os
import telebot
from telebot import types
from csv import writer
# from dbase import engine, session, Users, Stats, Reasons, add_data
from dbase import new_session, engine, Users, Stats, Reasons, add_data
from sqlalchemy import select, and_
from datetime import datetime, timezone, timedelta
import time
import pandas as pd
import plotly.express as px

API_KEY = os.getenv("TELEGRAM_API_KEY")


def main():
    bot = telebot.TeleBot(API_KEY)

    def msg_datetime(message):
        # Дата и время
        utc_date = datetime.fromtimestamp(message.date, timezone.utc)
        msk_date = utc_date + timedelta(hours=3)
        # msk_date = msk_date.strftime('%d.%m.%Y %H:%M:%S')
        return msk_date

    def main_menu(message):
        # Главное меню
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        item1 = types.KeyboardButton("Хочу курить")
        item2 = types.KeyboardButton("Посмотреть статистику")
        item3 = types.KeyboardButton("Скачать статистику")
        markup.add(item1, item2, item3)
        bot.send_message(message.chat.id, "Выбери в меню:", reply_markup=markup)

    @bot.message_handler(commands=["start"])
    def start(message):
        session = new_session()
        user_exists = session.query(Users).filter(Users.user_id == message.from_user.id).first()
        if not user_exists:
            new_user = Users(
                user_id=message.from_user.id,
                user_firstname=message.from_user.first_name,
                user_lastname=message.from_user.last_name,
                username=message.from_user.username
            )
            add_data(new_user)
            bot.send_message(message.chat.id, "Привет, жми /help чтобы узнать что умеет этот бот")
        main_menu(message)
        session.close()

    @bot.message_handler(commands=["help"])
    def help_command(message):
        bot.send_message(
            message.chat.id,
            "Этого бота я написал для того чтобы он помог мне бросить курить.\n"
            "Мне нужна статистика когда у меня появляется желание курить.\n"
            "Так мне будет проще понять от каких сигарет отказываться.\n\n"
            "Мне лень это записывать в блокнот или Excel, проще через бота пару кнопок "
            "нажать и он сам заполняет дату, время и причину (по которой захотелось курить).\n\n"
            "Как этим пользоваться: каждый раз когда появляется желание курить, жми Хочу курить.\n"
            "Дальше бот спрашивает: 'Идешь курить?' - если идешь, то жми Иду курить и выбирай причину.\n"
            "В начале причины нужно писать вручную - они будут добавляться в базу и в следующий раз "
            "предлагаться как кнопки. Со временем большинство твоих причин будут как кнопки.\n"
            "Но если ты сдержался и не пошёл курить то жми Не иду курить - тогда в статистику это запишется "
            "как Сдержался.\n"
            "Вот можешь поставить себе цель чтобы Сдержался было чаще других причин.\n\n"
            "Также бот умеет показывать 3 графика:\nСигарет в день, Частота причин, По часам.\n\n"
            # "Нажми на /examples чтобы посмотреть примеры графиков.\n\n"
            "И если нужна статистика в виде csv файла то жми Скачать статистику.\n\n"
            "Чтобы начать жми /start")

    @bot.message_handler(commands=["examples"])
    def examples(message):
        # TODO через эту команду отправлять 3 картинки с примерами графиков
        pass

    @bot.message_handler(content_types=["text"])
    def sub_menus(message):
        # Подменю
        # 1.
        if message.text == "Хочу курить":
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            item1 = types.KeyboardButton("Иду курить")
            item2 = types.KeyboardButton("Не иду курить")
            markup.add(item1, item2)
            bot.send_message(message.chat.id, "Идешь курить?", reply_markup=markup)

        # 1.1
        elif message.text == "Иду курить":
            # Причина
            # Вытаскиваю причины пользователя с прошлых записей
            session = new_session()
            reasons = [reason.reason for reason in
                       session.query(Reasons).filter(Reasons.user_id == message.from_user.id)]
            reasons.sort()
            reasons.append("Отмена")

            # Выдаю причины как кнопки под чатом
            # TODO ограничить количество причин на топ10. Остальные спрятать под кнопку Показать все
            markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
            for reason in reasons:
                itembtn = types.KeyboardButton(reason)
                markup.add(itembtn)
            choose_reason = bot.send_message(message.chat.id, "Выбери причину или напиши новую:", reply_markup=markup)
            bot.register_next_step_handler(choose_reason, add_to_stats)
            session.close()

        # 1.2
        elif message.text == "Не иду курить":
            add_to_stats(message)

        # Назад в главное меню
        elif message.text == "Отмена" or message.text == "Назад":
            main_menu(message)

        # Посмотреть статистику
        elif message.text == "Посмотреть статистику":
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            item1 = types.KeyboardButton("Сигарет в день")
            item2 = types.KeyboardButton("Частота причин")
            item3 = types.KeyboardButton("По часам")
            item4 = types.KeyboardButton("Назад")
            markup.add(item1, item2, item3, item4)
            bot.send_message(message.chat.id, "Выбери статистику:", reply_markup=markup)

        # 2.1
        elif message.text == "Сигарет в день":
            counter_start = time.perf_counter()

            bot.send_message(message.chat.id, "Пару секунд")

            stats_query = select(Stats.date_time, Reasons.reason) \
                .where(Stats.user_id == message.from_user.id) \
                .join_from(Stats, Reasons)
            stats_df = pd.read_sql(stats_query, engine)
            if not stats_df.empty:
                stats_df["date_time"] = stats_df["date_time"].dt.date

                cig_per_day = stats_df.groupby("date_time").count()
                line_graph = px.line(cig_per_day,
                                     title="Сигарет в день",
                                     labels={"date_time": "День",
                                             "value": "Количество"}
                                     )
                line_graph.update(layout_showlegend=False)
                image_out = line_graph.to_image(format="png")
                bot.send_photo(message.chat.id, image_out)
            else:
                bot.send_message(message.chat.id, "Нет данных для графика.\n"
                                                  "Сначала добавь несколько записей когда ты шёл курить.")

            counter_end = time.perf_counter()
            print(f"{datetime.now():%Y.%m.%d %H:%M:%S:%f} График 'Сигарет в день': {(counter_end - counter_start):.3f} сек.")

        # 2.2
        elif message.text == "Частота причин":
            counter_start = time.perf_counter()
            bot.send_message(message.chat.id, "Пару секунд")

            stats_query = select(Stats.reason_id, Reasons.reason) \
                .where(Stats.user_id == message.from_user.id) \
                .join_from(Stats, Reasons)
            stats_df = pd.read_sql(stats_query, engine)
            if not stats_df.empty:
                freq_reason = stats_df["reason"].value_counts()
                bar = px.bar(
                    freq_reason,
                    title="Частота причин",
                    labels={"index": "Причина", "value": "Количество"},
                    color=freq_reason.values,
                    color_continuous_scale="agsunset"
                )
                bar.update_layout(xaxis_tickangle=45)
                bar.update(layout_coloraxis_showscale=False)

                image_out = bar.to_image(format="png")
                bot.send_photo(message.chat.id, image_out)
            else:
                bot.send_message(message.chat.id, "Нет данных для графика.\n"
                                                  "Сначала добавь несколько записей когда ты шёл курить.")

            counter_end = time.perf_counter()
            print(f"{datetime.now():%Y.%m.%d %H:%M:%S:%f} График 'Частота причин': {(counter_end - counter_start):.3f} сек.")

        # 2.3
        elif message.text == "По часам":
            counter_start = time.perf_counter()
            bot.send_message(message.chat.id, "Пару секунд")

            stats_query = select(Stats.date_time) \
                .where(Stats.user_id == message.from_user.id)
            stats_df = pd.read_sql(stats_query, engine)

            if not stats_df.empty:
                stats_df["date_time"] = stats_df["date_time"].dt.hour

                hourly = stats_df["date_time"].value_counts()
                bar = px.bar(
                    hourly,
                    title="По часам",
                    labels={"index": "Час", "value": "Количество"},
                    color=hourly.values,
                    color_continuous_scale="agsunset"
                )
                bar.update(layout_coloraxis_showscale=False)

                image_out = bar.to_image(format="png")
                bot.send_photo(message.chat.id, image_out)
            else:
                bot.send_message(message.chat.id, "Нет данных для графика.\n"
                                                  "Сначала добавь несколько записей когда ты шёл курить.")

            counter_end = time.perf_counter()
            print(f"{datetime.now():%Y.%m.%d %H:%M:%S:%f} График 'Сигарет в день': {(counter_end - counter_start):.3f} сек.")

        # 3
        elif message.text == "Скачать статистику":
            session = new_session()
            stats_query = session.query(Stats) \
                .filter(Stats.user_id == message.from_user.id) \
                .join(Reasons, Stats.reason_id == Reasons.id).all()

            with open("stats.csv", "w", newline="", encoding="cp1251") as file:
                csvwriter = writer(file, delimiter=",")
                csvwriter.writerow(["sep=,"])
                csvwriter.writerow(["Дата и время", "Причина"])
                for r in stats_query:
                    csvwriter.writerow([r.date_time, r.reason.reason])
            bot.send_document(message.chat.id,
                              document=open("stats.csv", "rb"),
                              visible_file_name="Статистика.csv")
            session.close()

    # Добавление новой записи
    def add_to_stats(message):
        msk_date = msg_datetime(message)
        reason = message.text
        if reason == "Не иду курить":
            reason = "Сдержался"
        elif reason == "Отмена":
            return main_menu(message)

        # Проверяю существует ли уже такая Причина
        session = new_session()
        reason_exists = session.query(Reasons) \
            .filter(and_(Reasons.reason == reason, Reasons.user_id == message.from_user.id)) \
            .first()
        # Добавляю новую Причину если её не существует
        if not reason_exists:
            new_reason = Reasons(
                user_id=message.from_user.id,
                reason=reason
            )
            session.add(new_reason)
            session.flush()
            reason_id = new_reason.id
            session.commit()
        # Беру id существующей
        else:
            reason_id = reason_exists.id

        # Добавляю новую строку в Статистику
        new_to_stats = Stats(
            date_time=msk_date,
            user_id=message.from_user.id,
            reason_id=reason_id
        )
        add_data(new_to_stats)

        bot.send_message(message.chat.id, text=f"Ок, записал")
        main_menu(message)
        session.close()

    bot.polling(none_stop=True)


if __name__ == "__main__":
    main()
