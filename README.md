**Flask weather gathering website!**

DO NOT RUN db_fill.py! Token is restricted for 1000 calls per day

Installation instructions for GNU/Linux:
1. (crontab -l ; echo "0 0/6 * * * db_refresh.py") | sort - | uniq - | crontab -
2. pip install -r requirements.txt
3. db_fill.py
4. export FLASK_APP=main.py
5. flask run

Installation instructions for Windows:
1. pip install -r requirements.txt
2. set FLASK_APP=main.py
3. db_fill.py
4. flask run