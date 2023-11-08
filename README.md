# class-credit-sorter

### Installing requirements
1. Ensure you have a recent copy of Python (3.8+)
2. Run `git clone https://github.com/Bobbyperson12/class-credit-sorter.git`
3. Change directory to class-credit-sorter
4. Run `pip install -r requirements.txt`

### Running backend
1. Ensure you are running from the main directory (`class-credit-sorter`)
2. Run the file:
   - Developing:
      - Windows: `py backend\main.py`
      - Linux: `python3 backend/main.py`
      - MacOS: `python3 backend/main.py`
   - Production:
      - Linux: `gunicorn main:app`