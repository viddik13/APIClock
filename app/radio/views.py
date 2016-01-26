import urllib
import feedparser
import os
import unicodedata

from flask import render_template, redirect, request, url_for, \
                  flash, current_app
from flask.ext.login import login_required, current_user
from sqlalchemy.sql import and_
from werkzeug.utils import secure_filename

from . import radio
from .forms import AddMusicForm, PlayRadio
from .. import db
from ..mympd import player
from ..models import Music
from ..decorators import admin_required

mpd_player = player()


@radio.route('/', methods=['GET', 'POST'], defaults={'action': 0, 'radioe': 0})
@radio.route('/<int:action>/<int:radioe>', methods=['GET', 'POST'])
@login_required
@admin_required
def index(action, radioe):
    """Display user's radio and form to add medias and control radios."""
    radio = Music.query.filter(and_(Music.music_type == '1',
                               Music.users == current_user.id)).all()
    form = AddMusicForm()
    form2 = PlayRadio()

    if form.validate_on_submit() and form.music_type.data == '1':
        """Radio type added in bdd."""
        radio = Music(name=form.name.data,
                      url=form.url.data,
                      description=form.description.data,
                      music_type=form.music_type.data,
                      users=current_user.id)
        db.session.add(radio)
        db.session.commit()
        flash('Radio has been added.')
        return redirect(url_for('.index'))

    elif form.validate_on_submit() and form.music_type.data == '2':
        """ if Feed (podcast) added then redirect to linked shows """
        url = form.url.data
        d = feedparser.parse(url)

        podcast = Music(name=form.name.data,
                        url=form.url.data,
                        img=d['feed']["image"]["url"],
                        description=form.description.data,
                        music_type=form.music_type.data,
                        users=current_user.id)
        db.session.add(podcast)
        db.session.commit()

        flash('Podcast ok')
        return render_template('radio/shows.html', podcast=form.name.data)

    elif action is 1 and radioe is not 0:
        """Action = 1 > Remove media which id = radioe."""
        radiodel = Music.query.filter(Music.id == radioe).first()
        db.session.delete(radiodel)
        db.session.commit()

        if str(radiodel.music_type) == '3':
            try:
                app = current_app._get_current_object()
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], radiodel.name))
                #musics = Music.query.filter(and_(Music.music_type == '3',
                #                            Music.users == current_user.id)).all()
                flash('All right, file deleted.')
                return redirect(url_for('.music'))
            except:
                flash('Something went wrong, file not deleted...')

        flash('Delete successful !')
        return redirect(url_for('.index'))

    elif action is 2:
        """ action = 2 > play radio (MPD) """
        mpd_player.play()
        return redirect(url_for('.index'))

    elif action is 3:
        """ action = 3 > stop radio (MPD) """
        mpd_player.stop()
        return redirect(url_for('.index'))

    return render_template('radio/radio.html',
                           form=form, form2=form2, radios=radio)


@radio.route('/edit/<int:radioedit>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(radioedit):
    """Edit Radio form."""
    radioe = Music.query.filter(Music.id == radioedit).first()
    radio = Music.query.filter(and_(Music.music_type == '1',
                               Music.users == current_user.id)).all()
    form = AddMusicForm()

    if form.validate_on_submit():
        radioe.name = form.name.data
        radioe.url = form.url.data
        radioe.description = form.description.data
        db.session.add(radioe)
        flash('Radio has been updated')

    form.name.data = radioe.name
    form.url.data = radioe.url
    form.description.data = radioe.description
    return render_template('radio/radio.html', form=form, radios=radio)


@radio.route('/podcast/', methods=['GET', 'POST'], defaults={'action': 'rien'})
@radio.route('/podcast/<action>', methods=['GET', 'POST'])
@login_required
@admin_required
def podcast(action):
    """Display podcasts subscription list for current user."""
    podcasts = Music.query.filter(and_(Music.music_type == '2',
                                  Music.users == current_user.id)).all()

    if action == "unsubscribe":
        idmusic = request.args.get('music_id')
        podcast = Music.query.filter(Music.id == idmusic).first()
        db.session.delete(podcast)
        db.session.commit()
        flash('Podcast has been deleted')
        return redirect(url_for('.podcast'))

    elif action == "show":
        idmusic = request.args.get('music_id')
        podcast = Music.query.filter(Music.id == idmusic).first()
        d = feedparser.parse(podcast.url)
        shows = [(d.entries[i]['title'], d.entries[i].enclosures[0]['href'])
                 for i, j in enumerate(d.entries)]
        return render_template('radio/shows.html', shows=shows,
                               titre=podcast.name)

    elif action == "download":
        """Download podcast as music type media in music directory."""
        # Format podcast name
        # http://sametmax.com/transformer-des-caracteres-speciaux-en-ascii/
        base_string = request.args.get('nompodcast')
        urlmusic = request.args.get('urlpodcast')
        name_podcast = 'PODCAST_' + unicodedata.normalize('NFKD', base_string)\
                       .encode('ascii', 'ignore') + '.mp3'

        try:
            app = current_app._get_current_object()
            filename = secure_filename(name_podcast)
            url_file = (os.path.join(app.config['UPLOAD_FOLDER'], filename))
            urllib.urlretrieve(urlmusic, url_file)

            # TO ADD : check the disk space
            addmusic = Music(
                    name=filename,
                    url=url_file,
                    music_type=3,
                    users=current_user.id)
            db.session.add(addmusic)
            db.session.commit()
            flash('Your podcast has been download in your Music')
        except IOError as e:
            flash('Error adding your podcast to your music ({0}): {1}'
                  .format(e.errno, e.strerror))
        return redirect(url_for('.music'))

    elif action == "Upload":
        file = request.files['file']
        if file.filename:
            filename = secure_filename(file.filename)
            filename = 'UPLOAD_'+str(filename)
            app = current_app._get_current_object()

            file_path = os.path.join(app.config['BASE_APP_DIR'], app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            file_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            addmusic2 = Music(
                    name=filename,
                    url=file_url,
                    music_type=3,
                    users=current_user.id)
            db.session.add(addmusic2)
            db.session.commit()
            musics1 = Music.query.filter(and_(Music.music_type == '3',
                                         Music.users == current_user.id)).all()
            flash('Your music has been upload in your Music')
            return render_template('radio/music.html', radios=musics1)

        return render_template('radio/music.html', radios=musics1)

    return render_template('radio/podcast.html', podcasts=podcasts)


@radio.route('/music', methods=['GET', 'POST'])
@login_required
@admin_required
def music():
    """Display user's music."""
    musics = Music.query.filter(and_(Music.music_type == '3',
                                Music.users == current_user.id)).all()

    return render_template('radio/music.html', radios=musics)


@radio.route('/local/<path:radio>')
@login_required
@admin_required
def local(radio):
    """Play arg "radio" in local HTML player."""
    return render_template('radio/player.html', music=radio)


@radio.route('/distant/<path:radio>')
@login_required
@admin_required
def distant(radio):
    """Play arg "radio" in MPD (distant player)."""
    if radio == 'stop':
        mpd_player.stop()
        return redirect(url_for('.index'))

    mpd_player.play(radio)
    return render_template('radio/distant.html')
