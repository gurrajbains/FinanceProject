from flask import Flask, render_template, request, redirect, url_for
from database import init_db, add_transaction, get_all_transactions

appp = Flask(__name__)


@appp.route('/')
def house():
    return render_template('index.html')
if(__name__ == '__main__'):
    init_db()
    appp.run(debug=True)