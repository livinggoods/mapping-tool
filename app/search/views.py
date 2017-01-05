from flask import Response, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from . import search
from .forms import SearchForm
import json


@search.route('/', methods=['GET', 'POST'])
@login_required
def search_app():
    query = request.form['query'].lower()

    # # query for results
    # firms = Firm.query.join(FirmType).join(FirmTier)\
    #     .with_entities(Firm, FirmType, FirmTier)\
    #     .filter(Firm.name.ilike('{}%'.format(query)))\
    #     .order_by(Firm.name.asc()).all()
    # companies = Company.query\
    #     .filter(Company.name.ilike('{}%'.format(query)))\
    #     .order_by(Company.name.asc()).all()
    #
    # # if only one search result then return detail page
    # if len(firms) + len(companies) == 1:
    #     if firms:
    #         return redirect(url_for('main.firm', id=firms[0].Firm.id))
    #     else:
    #         return redirect(url_for('main.company', id=companies[0].id))
    #
    # # parse firms
    # vc_firms = []
    # ai_firms = []
    # su_firms = []
    # for firm in firms:
    #     if firm.FirmType.firm_type_code == 'vc':
    #         vc_firms.append(firm)
    #     if firm.FirmType.firm_type_code == 'ai':
    #         ai_firms.append(firm)
    #     if firm.FirmType.firm_type_code == 'su':
    #         su_firms.append(firm)

    return render_template('search/results.html', vc_firms=[],
                           ai_firms=[], su_firms=[],
                           companies=[])


@search.route('/_ta_prefetch')
@login_required
def prefetch():
    # firms = Firm.query.with_entities(Firm.name)\
    #     .filter(Firm.user_id == current_user.id)
    # companies = Company.query.with_entities(Company.name)\
    #     .filter(Company.user_id == current_user.id)
    # results = firms.union(companies).order_by(Firm.name.asc()).all()
    # json_results = [{'name': item.name} for item in results]
    return Response(json.dumps([], indent=4),
                    mimetype='application/json')


@search.route('/_ta_remote/<query>')
@login_required
def remote(query):
    # firms = Firm.query.with_entities(Firm.name)\
    #     .filter(Firm.user_id != current_user.id)
    # companies = Company.query.with_entities(Company.name)\
    #     .filter(Company.user_id != current_user.id)
    # results = firms.union(companies)\
    #     .filter(Firm.name.ilike('{}%'.format(query)))\
    #     .order_by(Firm.name.asc()).all()
    # json_results = [{'name': item.name} for item in results]
    return Response(json.dumps([], indent=4),
                    mimetype='application/json')
