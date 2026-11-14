from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.models.base import db
from app.models.mess import MessMenu, MessSubscription
from app.models.hostel import Hostel
from app.forms.operations import MessMenuForm, MessSubscriptionForm
from app.services.auth_service import role_required, log_audit

mess_bp = Blueprint('mess', __name__, url_prefix='/mess')

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MEAL_TYPES = ['Breakfast', 'Lunch', 'Dinner']

@mess_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Staff', 'Accountant')
def weekly_menu():
    hostel_id = request.args.get('hostel_id', type=int)
    query = MessMenu.query
    if hostel_id:
        query = query.filter_by(hostel_id=hostel_id)

    all_menus = query.all()
    # Build schedule grid: day -> meal -> menu object
    schedule = {day: {meal: None for meal in MEAL_TYPES} for day in DAYS_OF_WEEK}
    for m in all_menus:
        if m.day_of_week in schedule and m.meal_type in schedule[m.day_of_week]:
            schedule[m.day_of_week][m.meal_type] = m

    hostels = Hostel.query.all()
    return render_template(
        'mess/menu_grid.html',
        schedule=schedule,
        days=DAYS_OF_WEEK,
        meals=MEAL_TYPES,
        hostels=hostels,
        selected_hostel=hostel_id
    )


@mess_bp.route('/menu/edit', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def edit_meal_menu():
    day = request.args.get('day', 'Monday')
    meal = request.args.get('meal', 'Breakfast')
    hostel_id = request.args.get('hostel_id', type=int)

    existing = MessMenu.query.filter_by(
        day_of_week=day, meal_type=meal, hostel_id=hostel_id
    ).first()

    form = MessMenuForm(obj=existing)
    hostels = Hostel.query.all()
    form.hostel_id.choices = [(0, 'All Hostels (Default)')] + [(h.id, h.name) for h in hostels]

    if request.method == 'GET':
        form.day_of_week.data = day
        form.meal_type.data = meal
        if hostel_id:
            form.hostel_id.data = hostel_id

    if form.validate_on_submit():
        h_id = form.hostel_id.data if form.hostel_id.data != 0 else None
        target_menu = MessMenu.query.filter_by(
            day_of_week=form.day_of_week.data,
            meal_type=form.meal_type.data,
            hostel_id=h_id
        ).first()

        if not target_menu:
            target_menu = MessMenu(
                day_of_week=form.day_of_week.data,
                meal_type=form.meal_type.data,
                hostel_id=h_id
            )
            db.session.add(target_menu)

        target_menu.menu_items = form.menu_items.data.strip()
        target_menu.timing = form.timing.data.strip() if form.timing.data else ''
        target_menu.special_note = form.special_note.data.strip() if form.special_note.data else ''

        db.session.commit()
        log_audit('UPDATE_MESS_MENU', 'MessMenu', target_menu.id, f"Updated {target_menu.day_of_week} {target_menu.meal_type}")
        flash(f"Menu for {target_menu.day_of_week} {target_menu.meal_type} saved successfully!", 'success')
        return redirect(url_for('mess.weekly_menu', hostel_id=h_id))

    return render_template('mess/edit_meal.html', form=form, day=day, meal=meal)


@mess_bp.route('/subscriptions')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Accountant', 'Warden')
def list_subscriptions():
    subscriptions = MessSubscription.query.order_by(MessSubscription.created_at.desc()).all()
    return render_template('mess/subscriptions.html', subscriptions=subscriptions)
