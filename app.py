from flask import Flask, render_template, request, redirect, url_for
from database import init_db, add_transaction, get_all_transactions, return_HTML_table

appp = Flask(__name__)


@appp.route('/')
def house():
    rows = get_all_transactions()
    return render_template('index.html', rows = rows)
if(__name__ == '__main__'):
    init_db()
    appp.run(debug=True)

    #v \Scripts\activate venv  to activate virtual environment