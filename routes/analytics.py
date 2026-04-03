from flask import Blueprint, jsonify, request
from database import get_summary, get_insights

analytics = Blueprint("analytics", __name__)


@analytics.route("/api/summary")
def summary():
    data = get_summary()
    return jsonify({
        "labels": [d[0] for d in data],
        "values": [d[1] for d in data]
    })


@analytics.route("/api/make_graph")
def make_graph():
    rows = get_summary(
        request.args.get("metric", "income"),
        request.args.get("timeFrame", "Monthly"),
        request.args.get("timeRange")
    )

    return jsonify({
        "labels": [r[0] for r in rows],
        "values": [float(r[1]) for r in rows]
    })


@analytics.route("/api/insights")
def insights():
    return jsonify({"insights": get_insights()})