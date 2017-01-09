from flask import render_template
from . import main


@main.app_errorhandler(404)
def page_not_found(e):
    page = {'title': 'Not Found', 'subtitle':'The page was not found'}
    return render_template('page_404.html', page=page), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    page = {'title': 'Internal Error', 'subtitle':'Internal Error encountered'}
    return render_template('page_500.html', page=page), 500
