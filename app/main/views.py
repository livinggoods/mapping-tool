from flask import render_template, redirect, url_for, flash, request, abort, \
    current_app, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func, distinct, select
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm
from .. import db
from ..models import (Permission, Role, User, Geo, UserType, Village,
    Location, Education, EducationLevel, Referral, InterviewScore, Chp,
    SelectedApplication, Application, ApplicationPhone, Branch, Cohort)
from ..decorators import admin_required, permission_required
from flask_googlemaps import Map, icons
from datetime import date


@main.route('/', methods=['GET', 'POST'])
def index():
    page = {'title': 'Home'}
    if current_user.is_anonymous():
        # return redirect(url_for('auth.login'))
        return render_template('index.html', page=page)
    else:
        return render_template('index.html', page=page)

@main.route('/villages')
def add_mapping_details():
    # Add village,
    # villages = Village.query.order_by(Village.name.asc()).all()
    locations = Location.query.all()
    total_locations = len(locations)
    # distinct
    # create an object with all the locations
    village_marker = []
    for record in locations:
        if record.lat != '' and record.lon != '':
            marker = {
                'lat': record.lat,
                'lng': record.lon,
                'icon': icons.dots.blue,
                'infobox': (
                    "<h2>"+record.name+"</h2>"
                    "<img src='/static/images/logo.png'>"
                    "<br>200 New CHPs"
                    "<br><a href='village/"+str(record.id)+"'>More Details </a>"
                )
            }
            village_marker.append(marker)
    village_maps = Map(
        identifier="villages",
        lat=-1.2728, # -1.272898, 36.790095 
        lng=36.7901,
        zoom=8,
        style="height:500px;",
        markers=village_marker,
        cluster = True,
        cluster_gridsize = 10
        )

    page = {'title': 'Locations', 'total_villages': total_locations}
    # return jsonify(markers=village_marker)
    return render_template('villages.html', page=page, clustermap=village_maps, locations=locations)

@main.route('/application/<int:id>', methods=['GET', 'POST'])
def application_details(id):
    if request.method == 'GET':
        a = Application.query.filter_by(id=id).first()
        page = {'title':' '.join([a.l_name, a.m_name, a.f_name]), 'subtitle':'Application details'}
        age = calculate_age(a.date_of_birth)
        qualified = appplication_status(a)
        selected_application = SelectedApplication.query.filter_by(application_id=id).first()
        selected = True if selected_application else False
        phones = ApplicationPhone.query.filter_by(application_id=id)
        return render_template('application.html', phones=phones, selected=selected, qualified=qualified, age=age, page=page, application=a)
    else:
        if request.form.get('action') == 'select':
            # add the application to the selected application
            # the selected application must be alist
            application = request.form.get('application_id')
            selected = SelectedApplication(application_id =application)
            db.session.add(selected)
            db.session.commit()
            return jsonify(status='ok')
    # fetch application details

@main.route('/selected-applications', methods=['GET', 'POST'])
def selected_applications():
    if request.method == 'GET':
        applications = SelectedApplication.query.all()
        page = {'title': 'Selected Applications', 'subtitle':'Applications selected for interview'}
        return render_template('selected-applications.html', page=page, applications=applications)
    else:
        applications = request.form.getlist('applications[]')
        app = []
        if request.form.get('action') == 'select':
            for application_id in applications:
                application = SelectedApplication(
                    application_id = application_id
                )
                db.session.add(application)
                db.session.commit()
                app.append(application.id)
            return jsonify(app)
        else:
            return jsonify(status='no action selected')
        # return jsonify(details=request.form.getlist('applications[]'))

@main.route('/interview-scores', methods=['POST'])
def interview_score():
    selection = request.form.get('selection_id')
    application = Application.query.filter_by(id=selection).first()
    app = {}
    total = int(request.form.get('motivation')) + int(request.form.get('community_work')) + \
      int(request.form.get('mentality')) + int(request.form.get('selling')) + \
      int(request.form.get('health')) + int(request.form.get('investment')) + \
      int(request.form.get('interpersonal')) + int(request.form.get('commitment')) 
    score = InterviewScore(
        selection_id = selection,
        cohort_id = application.cohort_id,
        interview_id = request.form.get('interview_id'),
        motivation = request.form.get('motivation'),
        community_work = request.form.get('community_work'),
        mentality = request.form.get('mentality'),
        selling = request.form.get('selling'),
        health = request.form.get('health'),
        investment = request.form.get('investment'),
        interpersonal = request.form.get('interpersonal'),
        commitment = request.form.get('commitment'),
        interview_total_score = request.form.get('interview_total_score'),
        user_id = 1, #replace with current_user.id
    )
    db.session.add(score)
    db.session.commit()
    return jsonify(status=score.id)

@main.route('/location/<int:id>', methods=['GET', 'POST'])
def location(id):
    location  = Location.query.filter_by(id=id).first_or_404()
    # get the applications
    applications = Application.query.filter_by(location_id=id)
    referrals = Referral.query.filter_by(location_id=id)
    branches = Branch.query.filter_by(location_id=id)
    chp = Chp.query.filter_by(location_id=id)
    page = {'title': location.name if location is not None else 'No Village found'}
    if current_user.is_anonymous():
        # return redirect(url_for('auth.login'))
        return render_template('location.html', page=page, 
            applications=applications, refferals=refferals, branches = branches,
            chp=chp, selected_applications=applications)

    else:
        return render_template('location.html', page=page, 
            applications=applications, refferals=refferals, branches = branches,
            chp=chp, selected_applications=applications)



@main.route('/interview-score/<int:id>')
def get_interview_score(id):
    selection = SelectedApplication.query.filter_by(id=id).first()
    application = selection.application
    page = {'title': 'applications', 'subtitle': 'manage applications and create new applications'}
    score = InterviewScore.query.filter_by(selection_id=id).first()
    return render_template('interview-score.html', page=page, score=score, application=application)


@main.route('/applications', methods=['GET', 'POST'])
def applications():
    if request.method == 'GET':
        page = {'title': 'applications', 'subtitle': 'manage applications and create new applications'}
        villages = Location.query.all()
        referrals = Referral.query.all()
        educations = Education.query.all()
        edu_level = EducationLevel.query.all()
        cohorts = Cohort.query.all()
        applications = Application.query.all()
        return render_template('applications.html', cohorts=cohorts, applications=applications, page=page, villages=villages, referrals= referrals, educations=educations, edu_level=edu_level)
    else:
        if request.form.get('action') == 'select':
            # add the application to the selected application
            # the selected application must be alist
            for application in request.form.get('applications'):
                selected = SelectedApplication(application_id =application.id)
                db.session.add_all([selected])
                db.session.commit()
            return jsonify(status='ok')
        else:
            # save the records
            application = Application(
            f_name =  request.form.get('f_name').title() if request.form.get('f_name') != '' else None,
            m_name = request.form.get('m_name').title() if request.form.get('m_name') != '' else None,
            l_name = request.form.get('l_name').title() if request.form.get('l_name') != '' else None,
            maths = request.form.get('maths') if request.form.get('maths') != '' else None,
            english = request.form.get('english') if request.form.get('english') != '' else None,
            about_you = request.form.get('about') if request.form.get('about') != '' else None,
            gender = request.form.get('gender').title() if request.form.get('gender') != '' else None,
            date_of_birth = request.form.get('date_of_birth').title() if request.form.get('date_of_birth') != '' else None,
            location_id = request.form.get('village_id').title() if request.form.get('village_id') != '' else None,
            landmark = request.form.get('landmark').title() if request.form.get('landmark') != '' else None,
            date_moved = request.form.get('date_moved').title() if request.form.get('date_moved') != '' else None,
            referral_id = request.form.get('referral_id').title() if request.form.get('referral_id') != '' else None,
            education_id = request.form.get('education_id').title() if request.form.get('education_id') != '' else None,
            edu_level_id = request.form.get('edu_level_id').title() if request.form.get('edu_level_id') != '' else None,
            vht = request.form.get('vht').title() if request.form.get('vht') != '' else None,
            languages = request.form.get('languages').title() if request.form.get('languages') != '' else None,
            worked_brac = request.form.get('worked_brac').title() if request.form.get('worked_brac') != '' else None,
            brac_chp = request.form.get('brac_chp').title() if request.form.get('brac_chp') != '' else None,
            cohort_id = request.form.get('cohort_id') if request.form.get('cohort_id') != '' else None,
            community_membership = request.form.get('community_membership').title() if request.form.get('community_membership') != '' else None,
            read_english = request.form.get('read_english').title() if request.form.get('read_english') != '' else None,
            )
            db.session.add_all([application])
            db.session.commit()
            phones = request.form.getlist('phone[]')
            for phone in phones:
                pid = ApplicationPhone(
                    application_id = application.id,
                    phone = phone
                )
                db.session.add(pid)
                db.session.commit()
            # phone = ApplicationPhone(
            # application_id = application.id,
            # phone = request.form.get('phone').title()
            # )
            # db.session.add_all([phone])
            # db.session.commit()
            return jsonify(status='ok', phone=phones)

@main.route('/countries', methods=['GET', 'POST'])
@main.route('/regions', methods=['GET', 'POST'])
@main.route('/counties', methods=['GET', 'POST'])
@main.route('/districts', methods=['GET', 'POST'])
@main.route('/sub-counties', methods=['GET', 'POST'])
@main.route('/parishes', methods=['GET', 'POST'])
@main.route('/wards', methods=['GET', 'POST'])
@main.route('/villages', methods=['GET', 'POST'])
@main.route('/locations', methods=['GET', 'POST'])
def create_location():
    # if request.method == 'POST':
    if request.method == 'POST':
        parent = request.form.get('parent')  if request.form.get('parent') != '0' else None
        location = Location(
            name = request.form.get('name').title(),
            parent = parent,
            lat = request.form.get('lat'),
            lon = request.form.get('lon'),
            country_code = request.form.get('country_code'),
            admin_name = request.form.get('admin_name').title()
        )
        db.session.add(location)
        db.session.commit()
        return jsonify(status='ok', parent=parent)
    else:
        param = request.path.strip('/')
        all_locations = Location.query.all()
        if param is None or param == 'locations':
            locations = Location.query.all()
        else:
            locations = Location.query.filter_by(admin_name=param)
        page = {'title': param, 'subtitle': 'mapped '+param}
        inputmap = Map(
            identifier="view-side",
            lat=-1.2728, # -1.272898, 36.790095 
            lng=36.7901,
            zoom=8,
            markers=[(-1.2728, 36.7901)]
        )

        return render_template('mappings.html', page=page, map=inputmap,
         all_locations=all_locations,  locations=locations)


@main.route('/branches', methods=['GET', 'POST'])
def branches():
    if request.method == 'POST':
        branch = Branch(
            name = request.form.get('name').title(),
            location_id  = request.form.get('location_id'),
            lat = request.form.get('lat'),
            lon = request.form.get('lon')
        )
        db.session.add(branch)
        db.session.commit()
        return jsonify(status='ok', data=request.form)
    else:
        branches = Branch.query.all()
        branch_markers = []
        for record in branches:
            if record.lat != '' and record.lon != '':
                marker = {
                    'lat': record.lat,
                    'lng': record.lon,
                    'icon': icons.dots.blue,
                    'infobox': (
                        "<h2>"+record.name.title()+"</h2>"
                        "<br>200 New CHPs"
                        "<br><a href='village/"+str(record.id)+"'>More Details </a>"
                    )
                }
                branch_markers.append(marker)
        branch_maps = Map(
            identifier="branches",
            lat=-1.2728, # -1.272898, 36.790095
            lng=36.7901,
            zoom=8,
            style="height:500px;",
            markers=branch_markers,
            cluster = True,
            cluster_gridsize = 10
            )
        page = {'title': 'Branches', 'subtitle': 'List of branches'}
        
        locations = Location.query.all()
        return render_template('branches.html', branches=branches, clustermap=branch_maps, locations=locations, page=page)

@main.route('/cohort', methods=['GET', 'POST'])
def cohort():
    if request.method == 'GET':
        page = {'title': 'Cohort', 'subtitle': 'List of all cohorts in all branches'}
        branches = Branch.query.all()
        cohorts = Cohort.query.all()
        return render_template('cohort.html', cohorts=cohorts, branches=branches, page=page)
    else:
        cohort = Cohort(
            cohort_number = request.form.get('name'),
            branch_id  = request.form.get('branch')
        )
        db.session.add(cohort)
        db.session.commit()
        return jsonify(status='ok', data=request.form)


@main.route('/educations', methods=['GET', 'POST'])
def educations():
    if request.method == 'GET':
        page = {'title': 'Education', 'subtitle': 'List of all education levels'}
        educations = Education.query.all()
        return render_template('educations.html', educations=educations, page=page)
    else:
        educations = Education(
            name = request.form.get('name')
        )
        db.session.add(educations)
        db.session.commit()
        return jsonify(status='ok', data=request.form)


@main.route('/education-level', methods=['GET', 'POST'])
def education_levels():
    if request.method == 'GET':
        page = {'title': 'Education Level', 'subtitle': 'List of all education levels'}
        educations = Education.query.all()
        education_levels = EducationLevel.query.all()
        return render_template('education-level.html', education_levels=education_levels, educations=educations, page=page)
    else:
        educations = EducationLevel(
            level_name = request.form.get('name'),
            education_id = request.form.get('education')
        )
        db.session.add(educations)
        db.session.commit()
        return jsonify(status='ok', data=request.form)



@main.route('/refferals', methods=['GET', 'POST'])
def refferals():
    if request.method == 'GET':
        page = {'title': 'Refferals', 'subtitle': 'List of persons who have reffered others'}
        refferals = Referral.query.all()
        locations = Location.query.all()
        return render_template('refferals.html', refferals=refferals, page=page, locations=locations)
    else:
        referral = Referral(
            name = request.form.get('name'),
            phone = request.form.get('phone'),
            title = request.form.get('title'),
            location_id = request.form.get('location')
        )
        db.session.add(referral)
        db.session.commit()
        return jsonify(status='ok', id=referral.id, data=request.form)

@main.route('/gmap-test')
def test_route():
    return render_template('gmap.html')

@main.route('/video-test')
def video_route():
    return render_template('video-bg.html')

@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.outerjoin(Geo).outerjoin(UserType)\
        .with_entities(User, Geo, UserType)\
        .filter(User.username==username).first_or_404()

    # query for firms
    # firms = Firm.query.join(FirmType).join(FirmTier).join(User)\
    #     .with_entities(Firm, FirmType, FirmTier, User)\
    #     .filter(User.username == username)\
    #     .order_by(FirmTier.firm_tier.asc(), Firm.name.asc()).all()
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

    return render_template('user.html', user=user, vc_firms=[],
                           ai_firms=[], su_firms=[])


@main.route('/users/<username>')
@login_required
def users(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'error')
        return redirect(url_for('main.index'))

    # get request arguments
    followed = request.args.get('followed', 1, type=int)

    # query for users
    if followed:
        results = user.followed.order_by(Follow.timestamp.desc()).all()
        users = [{'user': item.followed, 'timestamp': item.timestamp}
                 for item in results]
    else:
        results = User.query.order_by(User.username.asc()).all()
        users = [{'user': item, 'timestamp': None}
                 for item in results]

    return render_template('user_list.html', user=user, users=users,
                           followed=followed)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        # change values based on form input
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        current_user.geo = Geo.query.get(form.geo.data)
        current_user.user_type = UserType.query.get(form.user_type.data)
        db.session.add(current_user)
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.user', username=current_user.username))
    # set inital values
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    form.geo.data = current_user.geo_id
    form.user_type.data = current_user.user_type_id
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.geo = Geo.query.get(form.geo.data)
        user.user_type = UserType.query.get(form.user_type.data)
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.', 'success')
        return redirect(url_for('main.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.geo.data = user.geo_id
    form.user_type.data = user.user_type_id
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>')
@login_required
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', posts=[post])


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.', 'success')
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'error')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('You are already following this user.', 'error')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username, 'success')
    return redirect(url_for('main.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'error')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.', 'error')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username, 'success')
    return redirect(url_for('main.user', username=username))


@main.route('/followers/<username>')
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'error')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='main.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
@login_required
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='main.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/company/<int:id>')
@login_required
def company(id):
    company = Company.query.join(User).filter(Company.id == id).first()
    if company is None:
        flash('Company Does Not Exist.', 'error')
        return redirect(url_for('main.index'))
    vc_firms = company.related_firms('vc')
    ai_firms = company.related_firms('ai')
    su_orgs = company.related_firms('su')
    return render_template('startup.html', company=company, vc_firms=vc_firms,
                           ai_firms=ai_firms, su_orgs=su_orgs)


@main.route('/companies/<username>')
@login_required
def companies(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'error')
        return redirect(url_for('main.index'))

    # get request arguments
    filter_user = request.args.get('filter_user', 1, type=int)

    # query for companies
    query = Company.query
    if filter_user:
        query = query.filter(Company.user_id == user.id)
    query = query.order_by(Company.name.asc())

    # build response dataset
    company_list = query.all()
    companies = [{'id': item.id,
                  'name': item.name,
                  'owner': item.owner,
                  'city': item.city,
                  'state': item.state,
                  'country': item.country}
                 for item in company_list]
    return render_template('startup_list.html', user=user,
                           filter_user=filter_user, companies=companies)


@main.route('/firm/<int:id>')
@login_required
def firm(id):
    firm = Firm.query\
        .join(FirmType).join(FirmTier).join(User)\
        .filter(Firm.id == id).first()
    if firm is None:
        flash('Relationship Does Not Exist.', 'error')
        return redirect(url_for('main.index'))
    companies = firm.related_companies()
    return render_template('firm.html', firm=firm, companies=companies)


@main.route('/firms/<username>')
@login_required
def firms(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'error')
        return redirect(url_for('main.index'))

    # get request arguments
    firm_type_code = request.args.get('firm_type_code', 'vc', type=str)
    filter_user = request.args.get('filter_user', 1, type=int)

    # format firm type
    firm_type = FirmType.query.filter_by(firm_type_code=firm_type_code).first()
    from inflect import engine
    p = engine()
    firm_type_full = firm_type.firm_type
    firm_type_code = firm_type.firm_type_code
    firm_type_p = p.plural(firm_type_full)

    # query for firms
    query = Firm.query\
        .join(FirmType, FirmType.id == Firm.firm_type_id)\
        .join(FirmTier, FirmTier.id == Firm.firm_tier_id)\
        .filter(FirmType.firm_type == firm_type_full)
    if filter_user:
        query = query.filter(Firm.user_id == user.id)
    query = query.order_by(FirmTier.firm_tier.asc(), Firm.name.asc())

    # build response dataset
    firm_list = query.all()
    firms = [{'id': item.id,
              'name': item.name,
              'type': item.type.firm_type,
              'tier': item.tier.firm_tier,
              'owner': item.owner,
              'city': item.city,
              'state': item.state,
              'country': item.country}
             for item in firm_list]
    return render_template('firm_list.html', user=user,
                           title=firm_type_p, type_code=firm_type_code,
                           filter_user=filter_user, endpoint='main.firms',
                           firms=firms)


# def appplication_status(application):
#     status = 'Y'
#     if application.age < 30 or application.age > 55:
#         status = 'N'
#     elif !application.speak_english:
#         status = 'N'
#     elif application.residence_years < 2:
#         status = 'N'
#     elif application.brac_chp:
#         status = 'N'
#     elif application.education < 'primary' or > 'Tertiary':
#         status = 'N'
#     elif application.maths = 0 or application.english == 0 or application.about_you == 0:
#         status = 'N'
#     elif (application.english + application.maths + application.about_you) < 30:
#         status = 'N'
#     return status

def appplication_status(app):
    status = True
    if calculate_age(app.date_of_birth) < 12 or calculate_age(app.date_of_birth) > 55:
        status = False
    if app.read_english == 0:
        status = False
    if calculate_age(app.date_moved) < 2:
        status = False
    if app.brac_chp == 1:
        status = False
    if app.maths == 0 or app.english == 0 or app.about_you == 0:
        status = False
    if (app.maths + app.english + app.about_you) < 30:
        status = False
    return status
def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
