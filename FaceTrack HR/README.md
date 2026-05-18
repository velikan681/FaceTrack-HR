# FaceTrack HR (MVP)

Веб-приложение на Flask для:
- автоматического учета посещаемости сотрудников по лицу,
- аналитики присутствия/отсутствия,
- базового кадрового администрирования.

Проект сделан как студенческий MVP: код модульный, читаемый и пригодный для демонстрации на защите диплома/курсовой.

## 1. Стек

- Backend: Python, Flask
- ORM/DB: SQLAlchemy + SQLite
- Computer Vision: OpenCV + `face_recognition`
- Frontend: Jinja2, Bootstrap 5, JavaScript, Chart.js

## 2. Функциональность

- Авторизация администратора (сессии, logout)
- CRUD сотрудников (ФИО, отдел, должность, контакты, фото)
- Генерация и хранение face-encoding при добавлении/обновлении фото
- Страница посещаемости с веб-камерой и авто-логикой:
  - check-in (если сотрудник еще не отмечен сегодня)
  - check-out (если есть check-in и прошло минимальное время)
  - защита от слишком частых дублей
- Дашборд:
  - всего сотрудников
  - присутствуют сегодня
  - отсутствуют сегодня
  - опоздали сегодня
  - графики
- Отчеты:
  - дневной
  - месячный
  - опоздания
  - отсутствия
  - отработанные часы
  - фильо сотруднику и дате

## 3. Структура проекта

```text
FaceTrack HR/
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ extensions.py
│  ├─ models.py
│  ├─ utils.py
│  ├─ routes/тр п
│  │  ├─ __init__.py
│  │  ├─ auth.py
│  │  ├─ dashboard.py
│  │  ├─ employees.py
│  │  ├─ attendance.py
│  │  └─ reports.py
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ face_service.py
│  │  ├─ attendance_service.py
│  │  └─ analytics_service.py
│  ├─ templates/
│  │  ├─ base.html
│  │  ├─ login.html
│  │  ├─ dashboard.html
│  │  ├─ employees/
│  │  │  ├─ list.html
│  │  │  └─ form.html
│  │  ├─ attendance/
│  │  │  └─ live.html
│  │  └─ reports/
│  │     └─ index.html
│  └─ static/
│     ├─ css/style.css
│     ├─ js/attendance.js
│     ├─ js/dashboard.js
│     └─ uploads/
├─ instance/
├─ run.py
├─ init_db.py
├─ requirements.txt
├─ requirements-face.txt
└─ README.md
```

## 4. Установка и запуск (Windows)

### Шаг 1: создать виртуальное окружение

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
```

Если путь проекта содержит кириллицу (например `D:\проект\...`), для face-модуля лучше создать venv в ASCII-пути:

```powershell
python -m venv D:\ftvenv311
D:\ftvenv311\Scripts\activate
```

### Шаг 2: установить базовые зависимости (без dlib)

```powershell
pip install -r requirements.txt
```

### Шаг 3 (опционально): установить face-recognition (вариант без Visual Studio Build Tools)

```powershell
pip install -r requirements-face.txt
pip install face-recognition --no-deps
```

Если установка прошла успешно, будет доступен модуль распознавания лиц.
Если не прошла, приложение все равно можно запустить (без face-модуля).

### Шаг 4: инициализировать БД и seed-данные

```powershell
python init_db.py
```

Будет создано:
- админ-пользователь `admin / admin123`,
- отделы,
- тестовые сотрудники,
- демо-записи посещаемости для отчётов.

### Шаг 5: запустить приложение

```powershell
python run.py
```

Откройте в браузере: `http://127.0.0.1:5000`

## 5. Важно про face_recognition на Windows

`face_recognition` зависит от `dlib`, и на некоторых Windows-системах установка может быть сложной.

Если `pip install -r requirements-face.txt` + `pip install face-recognition --no-deps` не проходит:

1. Проверьте, что виртуальное окружение находится в ASCII-пути (без кириллицы/иероглифов), например `D:\ftvenv311`.
2. Убедитесь, что `setuptools` ниже 81:
   ```powershell
   pip install "setuptools<81"
   ```
3. Повторите команды установки face-модуля:
   ```powershell
   pip install -r requirements-face.txt
   pip install face-recognition --no-deps
   ```
4. Проверка импорта:
   ```powershell
   python -c "import dlib, face_recognition; print('face-recognition OK')"
   ```

Если хотите устанавливать классический `dlib` из исходников, тогда уже нужны Build Tools (C++).

### Fallback-поведение

Если библиотека `face_recognition` не загрузилась:
- приложение всё равно запустится,
- CRUD/дашборд/отчёты будут работать,
- модуль распознавания лиц покажет понятную ошибку о недоступной библиотеке.

## 6. Логика посещаемости

- При первом успешном распознавании сотрудника за день создается запись с `check_in`.
- При повторном успешном распознавании:
  - если прошло слишком мало времени, событие игнорируется как дубликат,
  - если прошло достаточно времени, заполняется `check_out` и считаются часы.
- Для одного сотрудника в MVP хранится одна запись на день.

## 7. Примечания для защиты

- Проект использует `Flask app factory` и Blueprint-архитектуру.
- Бизнес-логика вынесена в `services`.
- Ошибки веб-камеры/пустого кадра/нераспознанного лица/БД обрабатываются явно.
- UI реализован как простой админ-панельный интерфейс с боковым меню.
