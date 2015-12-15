from flask import render_template, redirect, url_for, flash, request
from flask.ext.login import login_required, current_user
from sqlalchemy.sql import and_
import datetime
import moment

from . import alarm
from .forms import addAlarmForm, addAlarmForm2
from .. import db
from ..models import Alarm, Music
from ..functions import addcronenvoi, removecron, statealarm
from ..decorators import admin_required


@alarm.route('/', methods=['GET', 'POST'],
             defaults={'action': '0', 'idr': 'N'})
@alarm.route('/<action>/<idr>', methods=['GET', 'POST'])
@login_required
@admin_required
def index(action, idr):
    """Index."""
    alarms = Alarm.query.filter(Alarm.users == current_user.id).all()

    form = addAlarmForm(state=True)
    form2 = addAlarmForm2(state=True)
    monalarme = {}

    if form.submit.data:

        # Fast Form
        # ---------------------------------------------------
        lastid = alarms[-1].id
        if lastid is None:
            monalarme['id'] = 1
        else:
            monalarme['id'] = lastid + 1
        monalarme['heure'] = form.heures.data
        monalarme['minute'] = form.minutes.data
        monalarme['path'] = form.Radio.data.url

        # Complete Form
        # ---------------------------------------------------
        if form.repetition.data:
            monalarme['repetition'] = form.repetition.data
        # else:
        #     monalarme['repetition'] = 0
        if form.jours.data:
            monalarme['jours'] = form.jours.data
        else:  # tomorrow (if date > now --> today else tomorow)
            monalarme['jours'] = moment.now().add(days=1).format("d")

        if form.name.data:
            monalarme['nom'] = form.name.data
        else:
            monalarme['nom'] = 'No-name' + str(monalarme['id'])

        # setting up crontab
        result = addcronenvoi(monalarme)

        # Add alarm in database
        if result == 0:
            alarme = Alarm(
                    namealarme=monalarme['nom'],
                    days=",".join([str(x) for x in monalarme['jours']]),
                    startdate=str(monalarme['heure']) + ':' +
                    str(monalarme['minute']),
                    frequence='dows',
                    users=current_user.id)
            db.session.add(alarme)
            try:
                db.session.commit()
                flash('Your alarm has been programed.')
            except Exception, e:
                errorstring = str(e)
                flash('Error adding your alarm in database. ' + errorstring)
        else:
            flash('Error adding your alarm.')
        return redirect(url_for('.index'))
# ******************************************************************
# ******************************************************************

    elif action == '1':
        # action = 1 delete alarm by id (idr)
        alarmedel = Alarm.query.filter(Alarm.id == idr).first()
        db.session.delete(alarmedel)
        removecron(idr)
        db.session.commit()
        flash('Alarm has been deleted')
        return redirect(url_for('.index'))

    elif action == '2':
        # edit alarm by id (idr)
        alarmeedit = Alarm.query.filter(Alarm.id == idr).first()
        form = addAlarmForm(obj=alarmeedit)
        return render_template("alarm/alarm.html", form=form,
                               user=current_user, alarms=alarms)

    elif action == '3':
        # Call statealarm function which activate / deactivate alarm
        statealarm(idr)
        return render_template("alarm/alarm.html", form=form,
                               user=current_user, alarms=alarms)

    else:
        return render_template("alarm/alarm.html", form=form,
                               user=current_user, alarms=alarms)
