# se_project

### 如何測試

1. 首先建立一個虛擬環境
   ```python
   python3 -m venv env
   ```
2. activate 虛擬環境
   ```sh
   source env/bin/activate
   ```
3. 安裝必要套件
   ```python
   pip3 install -r requirements.txt
   ```
4. run the server
   ```python
   python3 manage.py runserver
   ```

### Windows 版本步驟

1. 建立虛擬環境
   ```python
   pip install virtualenv
   virtualenv proj_venv --python=C://python39
   ```
    - 注: 套件關係必須要 python3.7 以上才能使用，
    可以再多裝 python3.9 到指定目錄，然後透過上面命令來建立python3.9的 venv 

2. activate 虛擬環境 
   ```bash
   source proj_venv/Scripts/activate
   python --version
   ```
3. 安裝必要套件
   ```python
   pip install -r requirements.txt
   ```
4. run the server
   ```python
   python manage.py runserver
   ```   