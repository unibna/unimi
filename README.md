Cấu trúc project:
home
----venv
----unimi (workspace)
--------apps
--------unimi (setting folder)
--------manage.py
--------db.sqlite3
--------requirements.txt

- Tài khoản admin
    username: admin
    password: admin

Chạy app:
- tải project về
    git clone
- vào folder chứa workspace
- tải venv: 
    python -m venv venv
- kích hoạt venv
    # Linux
    source venv/bin/activate
    # Window
    source venv/Script/activate
    hoặc
    source venv/Script/activate.ps1
- vào folder workspace
- Tải dependencies
    pip3 install -r requirements.txt
- chạy server
    # 127.0.0.1:8000
    python manage.py runserver
    # xác định port
    python manage.py runserver 0.0.0.0:<port>
