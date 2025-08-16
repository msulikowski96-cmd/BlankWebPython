
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from wtforms.widgets import TextArea
from models import User

class LoginForm(FlaskForm):
    username_or_email = StringField('Nazwa użytkownika lub email', validators=[
        DataRequired(message='To pole jest wymagane'),
        Length(min=3, max=120, message='Nazwa użytkownika/email musi mieć 3-120 znaków')
    ])
    password = PasswordField('Hasło', validators=[
        DataRequired(message='Hasło jest wymagane'),
        Length(min=1, message='Hasło nie może być puste')
    ])
    remember_me = BooleanField('Zapamiętaj mnie')
    submit = SubmitField('Zaloguj się')

class RegistrationForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[
        DataRequired(message='Nazwa użytkownika jest wymagana'), 
        Length(min=3, max=20, message='Nazwa użytkownika musi mieć 3-20 znaków')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email jest wymagany'), 
        Email(message='Podaj prawidłowy adres email')
    ])
    first_name = StringField('Imię', validators=[
        Optional(), 
        Length(max=50, message='Imię nie może być dłuższe niż 50 znaków')
    ])
    last_name = StringField('Nazwisko', validators=[
        Optional(), 
        Length(max=50, message='Nazwisko nie może być dłuższe niż 50 znaków')
    ])
    password = PasswordField('Hasło', validators=[
        DataRequired(message='Hasło jest wymagane'),
        Length(min=6, message='Hasło musi mieć co najmniej 6 znaków')
    ])
    password2 = PasswordField('Potwierdź hasło', validators=[
        DataRequired(message='Potwierdzenie hasła jest wymagane'), 
        EqualTo('password', message='Hasła muszą się zgadzać')
    ])
    submit = SubmitField('Zarejestruj się')
    
    def validate_username(self, username):
        """Check if username is already taken"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ta nazwa użytkownika jest już zajęta. Wybierz inną.')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ten email jest już zarejestrowany. Wybierz inny.')

class UserProfileForm(FlaskForm):
    first_name = StringField('Imię', validators=[
        Optional(), 
        Length(max=50, message='Imię nie może być dłuższe niż 50 znaków')
    ])
    last_name = StringField('Nazwisko', validators=[
        Optional(), 
        Length(max=50, message='Nazwisko nie może być dłuższe niż 50 znaków')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email jest wymagany'), 
        Email(message='Podaj prawidłowy adres email')
    ])
    submit = SubmitField('Zaktualizuj profil')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Obecne hasło', validators=[
        DataRequired(message='Obecne hasło jest wymagane')
    ])
    new_password = PasswordField('Nowe hasło', validators=[
        DataRequired(message='Nowe hasło jest wymagane'),
        Length(min=6, message='Hasło musi mieć co najmniej 6 znaków')
    ])
    new_password2 = PasswordField('Potwierdź nowe hasło', validators=[
        DataRequired(message='Potwierdzenie nowego hasła jest wymagane'),
        EqualTo('new_password', message='Hasła muszą się zgadzać')
    ])
    submit = SubmitField('Zmień hasło')

class CVUploadForm(FlaskForm):
    cv_text = TextAreaField('Tekst CV', validators=[Optional()], widget=TextArea())
    job_title = StringField('Stanowisko (opcjonalne)', validators=[
        Optional(), 
        Length(max=200, message='Nazwa stanowiska nie może być dłuższa niż 200 znaków')
    ])
    job_description = TextAreaField('Opis stanowiska (opcjonalne)', validators=[Optional()], widget=TextArea())
    submit = SubmitField('Prześlij CV')
