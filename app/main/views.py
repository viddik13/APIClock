# coding: utf-8
import os

from flask import render_template, redirect, url_for, flash, request
from flask.ext.login import login_required, current_user
from flask.ext.mail import Message
from mpd import MPDClient

from . import main
from .forms import EditProfileForm, EditProfileAdminForm, playerForm,\
                   ContactForm, snoozeForm
from .. import db
from ..mympd import player
from ..email import send_email
from ..models import Role, User, Alarm, Music
from ..decorators import admin_required
from ..functions import snooze, connectMPD, jouerMPD, stopMPD
from ..login_nav import LoginFormNav

# ========================================
# ============= PUBLIC PAGES  ============
# ========================================


@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()

    form2 = LoginFormNav()
    form2.validateFormNav()

    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('public/contact.html', form=form)
        else:
            msg = Message(form.subject.data,
                          sender='[Contact] - Apiclock',
                          recipients=['j_fiot@hotmail.com'])
            msg.body = """
            From: %s &lt; %s &gt; %s """ % (form.name.data,
                                            form.email.data,
                                            form.message.data)
            send_email(current_user.email,
                       'APICLOCK MAIL from '+form.email.data,
                       'auth/email/contact',
                       msg.body)
            return render_template('public/contact.html', success=True)

    elif request.method == 'GET':
        return render_template('public/contact.html', form=form, form2=form2)


@main.route('/apiclock')
def apiclock():
    return render_template('index.html')


@main.route('/presentation')
def presentation():
    return render_template('public/presentation.html')


@main.route('/installation')
def installation():

    form2 = LoginFormNav()
    form2.validateFormNav()

    return render_template('public/installation.html', form2=form2)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@main.route('/', methods=['GET', 'POST'])
def index():
    """Index."""
    form2 = LoginFormNav()
    if form2.validateFormNav():
        form1 = playerForm(prefix="form1")
        formsnooze = snoozeForm()
        return render_template('dashboard.html',
                               form1=form1, formsnooze=formsnooze)
    else:
        return render_template('index.html', form2=form2)

# ========================================
# ============= PRIVATE PAGES ============
# ========================================


@main.route('/dashboard', methods=['GET', 'POST'], defaults={'action': 4})
@main.route('/dashboard/<action>/<musique>', methods=['GET', 'POST'])
@login_required
@admin_required
def dashboard(action,
      musique="http://audio.scdn.arkena.com/11010/franceculture-midfi128.mp3"):

    """Get and Print MPD state."""
    MPDstatut = None
    # TEST jerome import mympd
    player1 = player()
    #player1.is_playing()
    # -
    #connectMPD()
    # FIN

    alarms = Alarm.query.filter_by(users=current_user.id).all()
    form1 = playerForm(prefix="form1")
    formsnooze = snoozeForm()

    if formsnooze.submitsnooze.data:
        """ Get radio by id and return url for jouerMPD()"""
        radiosnooze = formsnooze.radiosnooze.data
        radiosnooze = Music.query.filter(Music.id == radiosnooze).first()
        radiosnooze = radiosnooze.url
        minutessnooze = int(formsnooze.minutessnooze.data)
        snooze(radiosnooze, minutessnooze)
        return redirect(url_for('.dashboard'))

    elif form1.submit.data:
        """ Depending on media type get id and then request for url """

        if form1.radio.data != "0":
            mediaid = form1.radio.data
            choosen_media = Music.query.filter(Music.id == mediaid).first()
            # TEST jerome
            player1.play(choosen_media.url)
            #jouerMPD(choosen_media.url)

        elif form1.radio.data == "0" and form1.music.data != "0":
            mediaid = form1.music.data
            choosen_media = Music.query.filter(Music.id == mediaid).first()
            # TEST jerome
            player1.play(choosen_media.name)
            #jouerMPD(choosen_media.name)

        elif form1.radio.data == "0" and form1.music.data == "0":
            mediaid = "0"
            flash("No media selected, please select a radio or music !")
        else:
            flash("No media selected, please select a radio or music !")

        return redirect(url_for('.dashboard', MPDstatut=MPDstatut))

    # get in GET the action's param
    elif action == '1':
        """ Verify MPD connexion and play the urlmedia in args with volum """
        os.system('amixer sset PCM,0 94%')
        # TEST jerome
        player1.play()
        # -
        #connectMPD()
        #jouerMPD()
        # FIN
        return redirect(url_for('.dashboard', MPDstatut=MPDstatut))

    elif action == '0':
        """ Verify MPD connection and stop and clear MPD playlist """
        # TEST jerome
        player1.stop()
        # -
        #connectMPD()
        #stopMPD()
        # FIN
        return redirect(url_for('.dashboard', MPDstatut=MPDstatut))

    elif action == '2':
        """ Increase volume by 3dB """
        # TEST jerome
        player1.volup()
        # -
        #os.system('amixer sset PCM,0 3dB+')
        # FIN
        return redirect(url_for('.dashboard', MPDstatut=MPDstatut))

    elif action == '3':
        """ Decrease volume by 3dB """
        # TEST jerome
        player1.voldown()
        # -
        #os.system('amixer sset PCM,0 3dB-')
        # FIN
        return redirect(url_for('.dashboard', MPDstatut=MPDstatut))

    else:
        return render_template('dashboard.html', form1=form1,
                               formsnooze=formsnooze, alarms=alarms,
                               MPDstatut=MPDstatut)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()

    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))

    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me

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
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))

    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    user = User.query.all()
    if request.args.get('id'):
        userid = request.args.get('id')
        userd = User.query.filter(User.id == userid).first()
        db.session.delete(userd)
        db.session.commit()
        flash('The user has been deleted.')
        return redirect(url_for('.users', users=user))
    return render_template('admin/users.html', users=user)
