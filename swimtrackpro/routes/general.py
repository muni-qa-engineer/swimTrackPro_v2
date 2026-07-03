"""General authenticated pages and session routes."""

from flask import flash, redirect, render_template, request, session, url_for

from services.settings_service import set_setting
from swimtrackpro.auth import login_required, trainer_required


@login_required
def about_trainer():
    return render_template("about_trainer.html")


@login_required
def help_page():
    return render_template("help.html")


@trainer_required("Only trainer can update the Notice Board.")
def update_notice():
    notice_message = request.form.get("notice_message", "").strip()

    if not notice_message:
        flash("Notice Board message cannot be empty.", "warning")
        return redirect(url_for("index"))

    set_setting("notice_message", notice_message)
    flash("Notice Board updated successfully.", "success")
    return redirect(url_for("index"))


def logout():
    session.clear()
    return redirect(url_for("index"))


def register_general_routes(app):
    """Register routes with their legacy endpoint names unchanged."""

    app.add_url_rule(
        "/about-trainer",
        endpoint="about_trainer",
        view_func=about_trainer,
    )
    app.add_url_rule(
        "/help",
        endpoint="help_page",
        view_func=help_page,
    )
    app.add_url_rule(
        "/update_notice",
        endpoint="update_notice",
        view_func=update_notice,
        methods=["POST"],
    )
    app.add_url_rule(
        "/logout",
        endpoint="logout",
        view_func=logout,
    )
