# **_Foodgram_**
Foodgram, «Продуктовый помощник». Онлайн-сервис и API для него. На этом сервисе пользователи публикуют свои рецепты, подписываются на публикации других пользователей, добавляют понравившиеся рецепты в список «Избранное», могут скачать список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

**_Ссылка на [проект](http://foodgram-study.ddns.net "Гиперссылка к проекту.")_**

**_Ссылка на документацию к [API](http://foodgram-study.ddns.net/api/docs/ "Гиперссылка к API.") с актуальными адресами. Здесь описана структура возможных запросов и ожидаемых ответов._**

### _Развернуть проект на удаленном сервере:_

**_Клонировать репозиторий:_**
```
git@github.com:TatianaSharova/foodgram-project-react.git
```
**_Установить на сервере Docker, Docker Compose:_**
```
sudo apt install curl                                   - установка утилиты для скачивания файлов
curl -fsSL https://get.docker.com -o get-docker.sh      - скачать скрипт для установки
sh get-docker.sh                                        - запуск скрипта
sudo apt-get install docker-compose-plugin              - последняя версия docker compose
```
**_Скопировать на сервер в папку foodgram файл docker-compose.production.yml (команду выполнять, находясь в папке проекта):_**
```
scp -i path_to_SSH/SSH_name docker-compose.production.yml username@server_ip:/home/username/foodgram/docker-compose.production.yml

# SSH_name — имя файла с SSH-ключом (без расширения)
# path_to_SSH — путь к файлу с SSH-ключом
# username - имя пользователя на сервере
# server_ip — IP вашего сервера
```

**_Для работы с GitHub Actions необходимо в репозитории в разделе Secrets > Actions создать переменные окружения:_**
```
DOCKER_PASSWORD         - пароль от Docker Hub
DOCKER_USERNAME         - логин Docker Hub
HOST                    - публичный IP сервера
USER                    - имя пользователя на сервере
SSH_KEY                 - приватный ssh-ключ
SSH_PASSPHRASE          - пароль для ssh-ключа
TELEGRAM_TO             - ID телеграм-аккаунта для посылки сообщения
TELEGRAM_TOKEN          - токен бота, посылающего сообщение
```
**_На сервере в папке foodgram создать файл .env и внести туда следующие данные:_**
```
POSTGRES_DB             - имя бд
POSTGRES_USER           - имя пользователя бд
POSTGRES_PASSWORD       - пароль от бд
DB_HOST                 - db
DB_PORT                 - 5432
SECRET_KEY              - ваш секретный ключ
```
**_Создание Docker-образов:_**

1.  Замените username на ваш логин на DockerHub:

    ```
    Из папки frontend выполнить команду:
    docker build -t username/foodgram_frontend .

    Из папки backend выполнить команду:
    docker build -t username/foodgram_backend .

    Из папки nginx выполнить команду:
    docker build -t username/foodgram_gateway . 
    ```

2. Загрузите образы на DockerHub:

    ```
    docker push username/foodgram_frontend
    docker push username/foodgram_backend
    docker push username/foodgram_gateway
    ```

**_Запустить контейнеры Docker:_**
```
sudo docker compose -f docker-compose.production.yml up -d
```
**_Выполнить миграции:_**
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```
**_Собрать статику:_**
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic

sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
**_Наполнить базу данных содержимым из файла ingredients.json:_**
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_data_ingredients
```
**_Создать суперпользователя:_**
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```
**_Для остановки контейнеров Docker:_**
```
sudo docker compose -f docker-compose.production.yml down -v      - с удалением контейнеров и томов
sudo docker compose -f docker-compose.production.yml stop         - без удаления
```
### После каждого обновления репозитория (push в ветку master) будет происходить:

1. Проверка кода на соответствие стандарту PEP8 (с помощью пакета flake8)
2. Сборка и доставка докер-образов frontend, backend, gateway на Docker Hub
3. Разворачивание проекта на удаленном сервере
4. Отправка сообщения в Telegram в случае успеха

### Локальный запуск проекта:

**_Склонировать репозиторий к себе_**
```
git@github.com:TatianaSharova/foodgram-project-react.git
```

**_В директории проекта создать файл .env и заполнить своими данными:_**
```
SECRET_KEY='ваш секретный ключ'
ALLOWED_HOSTS='localhost'
DEBUG_STATUS=True

```

**_В файле settings.py подключить default local database:_**
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3', }}

```

**_Запустить контейнеры Docker из папки с docker-compose.yml:._**

```
docker compose up
```
```
docker compose exec backend python manage.py migrate
```
```
docker compose exec backend python manage.py createsuperuser
```
```
docker compose exec backend python manage.py load_data_ingredients
```


**_После запуска проект будут доступен по адресу: http://localhost:8888/_**

**_Админка проекта будет доступна по адресу: http://localhost:8888/admin/_**

**_Документация будет доступна по адресу: http://localhost:8888/api/docs/_**


### Автор
Татьяна Шарова
