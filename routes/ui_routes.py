from flask import Blueprint, render_template, request
from database import get_all_transactions, search_transactions, sort_transactions

main = Blueprint("main", __name__)

@main.route('/')
def house():
    return render_template('index.html', rows=get_all_transactions())


@main.route("/search")
def search():
    return render_template(
        "index.html",
        rows=search_transactions(
            request.args.get("query", ""),
            request.args.get("type", "all")
        )
    )


@main.route("/sort")
def sort():
    return render_template(
        "index.html",
        rows=sort_transactions(
            request.args.get("sort_by", "all"),
            request.args.get("type", "all")
        )
    )