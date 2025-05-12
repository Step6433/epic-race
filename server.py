from functools import wraps
from os import abort
import base64
from flask import Flask, render_template, redirect, request, url_for
from data import db_session
from data.user import User
from data.pilot import Pilot
from data.race import Race
from data.team import Team
from data import user_api
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from requests import delete

from forms.add_res_form import AddResForm
from forms.add_team_form import AddTeamForm
from forms.delete_user_form import DelUserForm
from forms.login_form import LoginForm
from forms.register_form import RegisterForm
from forms.add_pilot_form import AddPilotForm
from forms.add_race_form import AddRaceForm

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'epic_race'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверяем, залогинился ли пользователь и является ли он администратором
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('index'))  # перенаправляем обратно на главную страницу
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

def main():
    db_session.global_init("db/formula.db")
    db_sess = db_session.create_session()
    app.register_blueprint(user_api.blueprint)
    app.run()

    adm1 = User()
    adm1.surname = 'Аульченко'
    adm1.name = 'Степан'
    adm1.email = 's.aulchenko@yandex.ru'
    adm1.is_admin = True
    adm1.set_password('AulStep')
    db_sess.add(adm1)
    db_sess.commit()

    adm2 = User()
    adm2.surname = 'Сазыкин'
    adm2.name = 'Степан'
    adm2.email = 'sazstep@mail.ru'
    adm2.is_admin = True
    adm2.set_password('SazStep')
    db_sess.add(adm2)
    db_sess.commit()
    return

@app.route("/")
@app.route('/index')
def index():
    db_session.global_init('db/formula.db')
    db_sess = db_session.create_session()
    races = db_sess.query(Race).all()
    return render_template("index.html", races=races)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            email=form.email.data,
            surname=form.surname.data,
            name=form.name.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/delete_user', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user():
    form = DelUserForm()
    if request.method == 'POST' and form.validate_on_submit():
        ans = delete(f'http://127.0.0.1:5000/api/del_users/{form.id.data}').json()
        if ans['success'] == 'OK':
            return redirect(url_for('index'))
    return render_template('delete_user.html', title='Удалить пользователя', form=form)

@app.route('/add_pilot', methods=['GET', 'POST'])
@login_required
@admin_required
def add_pilot():
    db_sess = db_session.create_session()
    teams = db_sess.query(Team).all()
    data = [(i.id, i.title) for i in teams]
    form = AddPilotForm()
    form.team_id.choices = data
    if request.method == 'POST' and form.validate_on_submit():
        pilot = Pilot(
            name=form.name.data,
            photo=form.photo.data.read(),
            team_id=form.team_id.data
        )
        db_sess.add(pilot)
        db_sess.commit()
        return redirect(url_for('index'))
    return render_template('add_pilot.html', title='Добавить пилота', form=form)

@app.route('/pilot')
def pilot():
    db_sess = db_session.create_session()
    pilots = db_sess.query(Pilot).all()
    teams = db_sess.query(Team).all()
    return render_template("pilots.html", pilots=pilots, teams=teams)

@app.route('/pilot/<pilot_id>')
@login_required
def one_pilot(pilot_id):
    db_sess = db_session.create_session()
    pilot = db_sess.query(Pilot).filter(Pilot.id == pilot_id).first()
    team = db_sess.query(Team).filter(Team.id == pilot.team_id).first()
    image = base64.b64encode(pilot.photo).decode('utf-8')
    return render_template("one_pilot.html", pilot=pilot, image=f'data:image/png;base64,{image}', team=team.title)

@app.route('/race/<race_id>')
@login_required
def one_race(race_id):
    db_sess = db_session.create_session()
    race = db_sess.query(Race).filter(Race.id == race_id).first()
    image1 = base64.b64encode(race.image1).decode('utf-8')
    image2 = base64.b64encode(race.image2).decode('utf-8')
    return render_template("one_race.html", race=race, image1=f'data:image/png;base64,{image1}',
                           image2=f'data:image/png;base64,{image2}')

@app.route('/add_race', methods=['GET', 'POST'])
@login_required
@admin_required
def add_race():
    form = AddRaceForm()
    if request.method == 'POST' and form.validate_on_submit():
        db_sess = db_session.create_session()
        race = Race(
            title=form.title.data,
            race_date=form.race_date.data,
            description=form.description.data,
            image1=form.image1.data.read(),
            image2=form.image2.data.read()
        )

        db_sess.add(race)
        db_sess.commit()
        return redirect(url_for('index'))
    return render_template('add_race.html', title='Добавить гонку', form=form)

@app.route('/edit_race/<race_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_race(race_id):
    form = AddRaceForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        race = db_sess.query(Race).filter(Race.id == race_id).first()
        if race:
            form.title.data = race.title
            form.race_date.data = race.race_date
            form.description.data = race.description
            form.image1.data = race.image1
            form.image2.data = race.image2
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        race = db_sess.query(Race).filter(Race.id == race_id).first()
        if race:
            race.title = form.title.data
            race.race_date = form.race_date.data
            race.description = form.description.data
            race.image1 = form.image1.data.read()
            race.image2 = form.image2.data.read()
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('add_race.html', title='Изменение гонки', form=form)

@app.route('/del_race/<race_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_race(race_id):
    db_sess = db_session.create_session()
    race = db_sess.query(Race).filter(Race.id == race_id).first()
    if race:
        db_sess.delete(race)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/add_team', methods=['GET', 'POST'])
@login_required
@admin_required
def add_team():
    db_sess = db_session.create_session()
    form = AddTeamForm()
    if request.method == 'POST' and form.validate_on_submit():
        team = Team(
            title=form.title.data,
            sponsor=form.sponsor.data,
            description=form.description.data,
        )
        db_sess.add(team)
        db_sess.commit()
        return redirect(url_for('index'))
    return render_template('add_team.html', title='Добавить команду', form=form)

@app.route('/teams')
def teams():
    db_sess = db_session.create_session()
    teams = db_sess.query(Team).all()
    return render_template("teams.html", teams=teams)

@app.route('/teams/<team_id>')
@login_required
def one_team(team_id):
    db_sess = db_session.create_session()
    team = db_sess.query(Team).filter(Team.id == team_id).first()
    return render_template("one_team.html", team=team)

@app.route('/add_results/<race_id>')
@login_required
@admin_required
def add_results(race_id):
    db_sess = db_session.create_session()
    form = AddResForm()
    if request.method == 'POST' and form.validate_on_submit():
        team = Team(
            title=form.title.data,
            sponsor=form.sponsor.data,
            description=form.description.data,
        )
        db_sess.add(team)
        db_sess.commit()
        return redirect(url_for('index'))
    return render_template('add_team.html', title='Добавить команду', form=form)


if __name__ == '__main__':
    main()