from . import api
from flask_login import login_required, current_user
from flask import Response, request, jsonify
import json
from sqlalchemy import func, distinct, select, and_
from .. import db
from ..models import (Permission, Role, User, Geo, UserType, Village, LocationTargets,
    Location, Education, EducationLevel, Referral, InterviewScore, Chp, Recruitments,
    SelectedApplication, Application, ApplicationPhone, Branch, Cohort)


@api.route('/firm_summary')
@login_required
def firm_summary():
    summary = current_user.firm_summary()
    return Response(json.dumps(summary, indent=4), mimetype='application/json')

@api.route('/recruitments.json')
def recruitments_json():
  if request.method == 'GET':
    page={'title':'Recruitments', 'subtitle':'Recruitments done so far'}
    recruitments = Recruitments.query.filter_by(archived=0)
    result_dict = [u.name for u in recruitments]
    return jsonify(recruitments=result_dict)
  else:
    recruitments = Recruitments(name=request.form.get('name'))
    db.session.add(recruitments)
    db.session.commit()
    return jsonify(status='ok')