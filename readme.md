# Запуск ТОЛЬКО ОТ ИМЕНИ АДМИНИСТРАТОРА!
Запустить можно через ```main.exe```. Надеюсь оно запустится :).
Конфиг тянется из ````./.env```` 

Другой вариант - запуск ```python backend/main.py``` - это запустит 2 приложения на портах 8005 и 8006.

http://localhost:8005/ - WebSocket application.

http://localhost:8006/ - REST API application ("/" - тестовая страница).

http://localhost:8006/docs - SwaggerUI

PostgreSQL можно запустить в Docker: ```docker compose up -d```

Перегенерировать nuitka:

```
python -m nuitka --standalone --onefile backend/main.py
```

На фронте включено логирование, я не успел отдебажить отрисовку, но по логам видно завершённые процессы. 
Отрисовка активных процессов полностью работает.

Пример .env:
```
POSTGRES_PASSWORD=postgres
POSTGRES_USER=postgres
POSTGRES_DB=visionero_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5435
STATIC_ROOT=D:/Projects/Visionero/front/simple-test-app/build
ALEMBIC_INI=D:\Projects\Visionero\backend\alembic.ini
```
