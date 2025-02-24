import vk_api
from datetime import datetime
import pytz
import csv
import pandas as pd
import time

# Инициализация сессии
vk_session = vk_api.VkApi(
    token='e7e25eb3e7e25eb3e7e25eb3a4e4c832e4ee7e2e7e25eb38054bb4520978ee780e204b4')  # Замените на ваш сервисный ключ
vk = vk_session.get_api()

# Ключевое слово для поиска
search_keyword = "нейромексол"  # Замените на нужное вам слово


# Открываем CSV файл для записи (если его нет, создаем)
def add_post_and_comments_to_csv(search_keyword, post_link, post_date, post_text, likes_count, comments,
                                 filename='vk_posts_and.csv'):
    """
    Добавляет данные о посте и комментариях в CSV файл.

    :param post_date: Дата поста
    :param post_text: Текст поста
    :param likes_count: Количество лайков на пост
    :param comments: Список комментариев, где каждый комментарий — это кортеж (comment_date, comment_text)
    :param search_keyword: Ключевое слово
    :param filename: Имя CSV файла (по умолчанию 'posts_and_comments.csv')
    """
    # Открываем CSV файл для добавления данных
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Записываем данные для каждого комментария
        for comment_date, comment_text in comments:
            writer.writerow([search_keyword, post_link, post_date, post_text, likes_count, comment_date, comment_text])

    print(f"Данные успешно добавлены в '{filename}'")


# Выполняем поиск по постам с ключевым словом
response = vk.newsfeed.search(q=search_keyword,
                              count=100)  # count — максимальное количество постов, которые можно вернуть

for post in response['items']:
    # Если ключевое слово найдено в тексте поста
    if search_keyword.lower() in post['text'].lower():
        # Получаем дату поста и переводим в нормальный формат
        timestamp = post['date']
        post_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        # Получаем количество лайков
        likes = post.get('likes', {}).get('count', 0)
        post_text = post['text']
        post_link = f"https://vk.com/wall{post['owner_id']}_{post['id']}"  # Ссылка на пост

        # Сохраняем комментарии в список кортежей
        comments_list = []

        try:
            # Получаем комментарии для поста
            comments_response = vk.wall.getComments(owner_id=post['owner_id'], post_id=post['id'], count=100)

            for comment in comments_response['items']:
                # Получаем дату и текст комментария
                comment_timestamp = comment['date']
                comment_date = datetime.fromtimestamp(comment_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                comment_text = comment['text']

                # Добавляем комментарий в список
                comments_list.append((comment_date, comment_text))

        except vk_api.exceptions.ApiError as e:
            # Если произошла ошибка при получении комментариев (например, нет доступа к комментариям)
            print(f"Ошибка при получении комментариев для поста {post_link}: {e}")
            # Переходим к следующему посту, игнорируя текущий
            continue

        # Добавляем информацию о посте и комментариях в CSV
        add_post_and_comments_to_csv(search_keyword, post_link, post_date, post_text, likes, comments_list)

    time.sleep(1)  # Задержка между запросами, чтобы избежать блокировки
