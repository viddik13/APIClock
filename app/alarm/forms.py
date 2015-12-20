import feedparser

from flask.ext.wtf import Form
from flask.ext.login import current_user
from wtforms import SubmitField, SelectMultipleField, IntegerField, \
                    SelectField, StringField, RadioField, BooleanField
from wtforms.validators import Required, NumberRange, Length
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from sqlalchemy.sql import and_
from ..models import Music, getradios


class addAlarmForm(Form):
    """Adding Form alarm."""

    name = StringField('Nom', validators=[Length(1, 120)])
    state = BooleanField('Active')
    # duration = SelectField('Duree', choices=[('5', '5 mn'), ('10', '10 mn'),
    # ('15', '15 mn'), ('30', '30 mn'), ('45', '45 mn'), ('59', '1 h')])
    #Radio = QuerySelectField('Radios', query_factory=getradios,
    #                         get_label='name')
    Radio = SelectField('Radio')
    musics = SelectField('Music')
    heures = IntegerField('Heures', validators=[NumberRange(min=0, max=23),
                                                Required()])
    minutes = IntegerField('Minutes', validators=[NumberRange(min=0, max=59),
                                                  Required()])
    repetition = SelectField('frequence',
                             choices=[('1', 'Days'),
                                      ('2', 'Weeks'), ('3', 'Month'),
                                      ('4', 'Year')])
    # TODO Add repetittion = 0 with a date picker in this case
    jours = SelectMultipleField('jours',
                                choices=[('1', 'Lundi'), ('2', 'Mardi'),
                                         ('3', 'Mercredi'), ('4', 'Jeudi'),
                                         ('5', 'Vendredi'), ('6', 'Samedi'),
                                         ('0', 'Dimanche')],)
    submit = SubmitField('valider')

    def __init__(self, *args, **kwargs):
        """
        Query for form list.
        Inset all radios/music, append 'Choose ...'
        and reverse all to have 'Choose..' first position
        """
        super(addAlarmForm, self).__init__(*args, **kwargs)
        self.Radio.choices = [(g.id, g.name) for g in
                              Music.query.filter(and_(
                                    Music.music_type == '1',
                                    Music.users == current_user.id)).all()]
        self.Radio.choices.append(('0', 'Choose radio'))
        self.Radio.choices.reverse()

        self.musics.choices = [(g.id, g.name) for g in
                              Music.query.filter(and_(
                                  Music.music_type == '3',
                                  Music.users == current_user.id)).all()]
        self.musics.choices.append(('0', 'Choose music'))
        self.musics.choices.reverse()

    def validate(self):
        if not self.heures.data:
            self.heures.errors.append('Hours Needed')


class addAlarmForm2(Form):
    """Testing new form for adding alarm."""

    name = StringField('Nom', validators=[Length(1, 120)])
    state = BooleanField('Active')
    # duration = SelectField('Duree', choices=[('5', '5 mn'), ('10', '10 mn'),
    # ('15', '15 mn'), ('30', '30 mn'), ('45', '45 mn'), ('59', '1 h')])
    media = SelectField('', choices=[('1', 'Radio'), ('2', 'Podcast'),
                                     ('3', 'Musique')])
    radio = SelectField('')
    podcast = SelectField('')
    music = SelectField('')
    heures = IntegerField('')
    minutes = IntegerField('')
    repetition = RadioField('List', choices=[('Repeter ? ',
                                             'Repeter l\'alarme')])
    jours = SelectMultipleField('jours',
                                choices=[('1', 'Lundi'), ('2', 'Mardi'),
                                         ('3', 'Mercredi'), ('4', 'Jeudi'),
                                         ('5', 'Vendredi'), ('6', 'Samedi'),
                                         ('0', 'Dimanche')],
                                validators=[Required()])
    submit = SubmitField('Valider')

    def __init__(self, *args, **kwargs):
        """Query for form list."""
        super(addAlarmForm2, self).__init__(*args, **kwargs)
        self.radio.choices = [(g.id, g.name) for g in
                              Music.query.filter(and_(
                                    Music.music_type == '1',
                                    Music.users == current_user.id)).all()]
        self.music.choices = [(g.id, g.name) for g in
                              Music.query.filter(and_(
                                  Music.music_type == '3',
                                  Music.users == current_user.id)).all()]
        podcasts = Music.query.filter(and_(
                                  Music.music_type == '2',
                                  Music.users == current_user.id)).all()
        lemissions = []
        # Get every emissions for a given podcast (url)
        for emission in podcasts:
            d = feedparser.parse(emission.url)
            emissions = [(d.entries[i].enclosures[0]['href'],
                         emission.name + ' - ' + d.entries[i]['title'])
                         for i, j in enumerate(d.entries)]
            lemissions.extend(emissions)
        self.podcast.choices = lemissions

        # Hours in a day
        hourstot = list(range(0, 23))
        self.heures.choices = [(str(g), str(g)) for g in hourstot]

        # Min. by 5 in hour
        minutes5 = list(range(0, 60, 5))
        self.minutes.choices = [(str(g), str(g)) for g in minutes5]
