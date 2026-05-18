from flask import Blueprint, render_template

from ..services.analytics_service import get_dashboard_stats
from ..utils import login_required


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    stats = get_dashboard_stats()
    return render_template("dashboard.html", stats=stats)
