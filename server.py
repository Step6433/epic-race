from functools import wraps  # Импортируем декораторы функций
from os import abort  # Для обработки ошибок
import base64  # Кодирование изображений в Base64
from flask import Flask, render_template, redirect, request, url_for  # Основные модули Flask
from data import db_session  # Модуль для работы с базой данных
from data.user import User  # Модель пользователей
from data.pilot import Pilot  # Модель пилотов
from data.race import Race  # Модель гонок
from data.team import Team  # Модель команд
from data import user_api  # API пользователей
from flask_login import LoginManager, login_user, login_required, logout_user, current_user  # Модули авторизации
from requests import delete  # HTTP-запросы для удаления записей

# Формы добавления и редактирования различных сущностей
from forms.add_res_form import AddResForm
from forms.add_team_form import AddTeamForm
from forms.delete_user_form import DelUserForm
from forms.login_form import LoginForm
from forms.register_form import RegisterForm
from forms.add_pilot_form import AddPilotForm
from forms.add_race_form import AddRaceForm

app = Flask(__name__)  # Создаем приложение Flask
login_manager = LoginManager()  # Менеджер авторизации
login_manager.init_app(app)  # Подключаем менеджер авторизации к приложению
app.config['SECRET_KEY'] = 'epic_race'  # Устанавливаем секретный ключ приложения


# Декоратор проверки прав администратора
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверка, залогинен ли пользователь и имеет ли права администратора
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('index'))  # Перенаправление на главную страницу
        return f(*args, **kwargs)

    return decorated_function


# Загрузка текущего пользователя
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    return db_sess.query(User).get(user_id)  # Получаем пользователя по id


# Главная точка входа приложения
def main():
    db_session.global_init("db/formula.db")  # Инициализируем базу данных
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    app.register_blueprint(user_api.blueprint)  # Регистрируем API пользователей

    # Добавляем двух админов вручную
    adm1 = User(surname='Аульченко', name='Степан', email='s.aulchenko@yandex.ru', is_admin=True)
    adm1.set_password('AulStep')  # Устанавливаем пароль
    db_sess.add(adm1)  # Добавляем первого администратора
    db_sess.commit()  # Сохраняем изменения в БД

    adm2 = User(surname='Сазыкин', name='Степан', email='sazstep@mail.ru', is_admin=True)
    adm2.set_password('SazStep')  # Устанавливаем пароль
    db_sess.add(adm2)  # Добавляем второго администратора
    db_sess.commit()  # Сохраняем изменения в БД
    return


# Маршрут главной страницы сайта
@app.route("/")
@app.route('/index')
def index():
    db_session.global_init('db/formula.db')  # Инициализируем базу данных
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    races = db_sess.query(Race).all()  # Получаем список всех гонок
    return render_template("index.html", races=races)  # Рендерим шаблон главной страницы


# Страница регистрации нового пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()  # Форма регистрации
    if form.validate_on_submit():  # Если форма отправлена и валидирована
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form, message="Пароли не совпадают")

        db_sess = db_session.create_session()  # Создаем сессию базы данных
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже существует")

        new_user = User(email=form.email.data, surname=form.surname.data, name=form.name.data)
        new_user.set_password(form.password.data)  # Устанавливаем пароль
        db_sess.add(new_user)  # Добавляем нового пользователя
        db_sess.commit()  # Сохраняем изменения в БД
        return redirect('/login')  # Переходим на страницу авторизации
    return render_template('register.html', title='Регистрация', form=form)  # Отображаем форму регистрации


# Страница авторизации пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Форма авторизации
    if form.validate_on_submit():  # Если форма отправлена и валидирована
        db_sess = db_session.create_session()  # Создаем сессию базы данных
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)  # Авторизуем пользователя
            return redirect("/")  # Возвращаемся на главную страницу
        return render_template('login.html', message="Неверный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)  # Отображаем форму авторизации


# Обработчик выхода пользователя из системы
@app.route('/logout')
@login_required  # Требуется авторизация
def logout():
    logout_user()  # Выполняем выход пользователя
    return redirect("/")  # Возвращаемся на главную страницу


# Удаление пользователя (для администратора)
@app.route('/delete_user', methods=['GET', 'POST'])
@login_required
@admin_required  # Доступ только для администраторов
def delete_user():
    form = DelUserForm()  # Форма удаления пользователя
    if request.method == 'POST' and form.validate_on_submit():
        response = delete(f'http://127.0.0.1:5000/api/del_users/{form.id.data}').json()
        if response.get('success') == 'OK':  # Успешное удаление
            return redirect(url_for('index'))
    return render_template('delete_user.html', title='Удалить пользователя', form=form)


# Добавление нового пилота (для администратора)
@app.route('/add_pilot', methods=['GET', 'POST'])
@login_required
@admin_required  # Доступ только для администраторов
def add_pilot():
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    teams = db_sess.query(Team).all()  # Получаем список всех команд
    choices = [(team.id, team.title) for team in teams]  # Формируем варианты выбора команды
    form = AddPilotForm()  # Форма добавления пилота
    form.team_id.choices = choices  # Устанавливаем доступные команды
    if request.method == 'POST' and form.validate_on_submit():
        pilot = Pilot(name=form.name.data, photo=form.photo.data.read(), team_id=form.team_id.data)
        db_sess.add(pilot)  # Добавляем пилота в базу данных
        db_sess.commit()  # Сохраняем изменения
        return redirect(url_for('index'))  # Возвращаемся на главную страницу
    return render_template('add_pilot.html', title='Добавить пилота', form=form)


# Список всех пилотов
@app.route('/pilot')
def pilot():
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    pilots = db_sess.query(Pilot).all()  # Получаем список всех пилотов
    teams = db_sess.query(Team).all()  # Получаем список всех команд
    return render_template("pilots.html", pilots=pilots, teams=teams)  # Рендерим шаблон списка пилотов


# Информация о конкретном пилоте
@app.route('/pilot/<pilot_id>')
@login_required
def one_pilot(pilot_id):
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    pilot = db_sess.query(Pilot).filter(Pilot.id == pilot_id).first()  # Получаем конкретного пилота
    team = db_sess.query(Team).filter(Team.id == pilot.team_id).first()  # Получаем команду пилота
    image = base64.b64encode(pilot.photo).decode('utf-8')  # Преобразование фото пилота в Base64
    return render_template("one_pilot.html", pilot=pilot, image=f'data:image/png;base64,{image}', team=team.title)


# Информация о конкретной гонке
@app.route('/race/<race_id>')
@login_required
def one_race(race_id):
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    race = db_sess.query(Race).filter(Race.id == race_id).first()  # Получаем конкретную гонку
    image1 = base64.b64encode(race.image1).decode('utf-8')  # Преобразование первой фотографии гонки в Base64
    image2 = base64.b64encode(race.image2).decode('utf-8')  # Преобразование второй фотографии гонки в Base64
    return render_template("one_race.html", race=race, image1=f'data:image/png;base64,{image1}',
                           image2=f'data:image/png;base64,{image2}')


# Добавление новой гонки (для администратора)
@app.route('/add_race', methods=['GET', 'POST'])
@login_required
@admin_required  # Доступ только для администраторов
def add_race():
    form = AddRaceForm()  # Форма добавления гонки
    if request.method == 'POST' and form.validate_on_submit():
        db_sess = db_session.create_session()  # Создаем сессию базы данных
        race = Race(title=form.title.data, race_date=form.race_date.data, description=form.description.data,
                    image1=form.image1.data.read(), image2=form.image2.data.read())
        db_sess.add(race)  # Добавляем новую гонку
        db_sess.commit()  # Сохраняем изменения
        return redirect(url_for('index'))  # Возвращаемся на главную страницу
    return render_template('add_race.html', title='Добавить гонку', form=form)


# Редактирование существующей гонки (для администратора)
@app.route('/edit_race/<race_id>', methods=['GET', 'POST'])
@login_required
@admin_required  # Доступ только для администраторов
def edit_race(race_id):
    form = AddRaceForm()  # Форма редактирования гонки
    if request.method == "GET":  # Заполнение формы существенными значениями
        db_sess = db_session.create_session()  # Создаем сессию базы данных
        race = db_sess.query(Race).filter(Race.id == race_id).first()
        if race:
            form.title.data = race.title
            form.race_date.data = race.race_date
            form.description.data = race.description
            form.image1.data = race.image1
            form.image2.data = race.image2
        else:
            abort(404)  # Гонка не найдена

    if form.validate_on_submit():  # Если форма отправлена и валидирована
        db_sess = db_session.create_session()  # Создаем сессию базы данных
        race = db_sess.query(Race).filter(Race.id == race_id).first()
        if race:
            race.title = form.title.data
            race.race_date = form.race_date.data
            race.description = form.description.data
            race.image1 = form.image1.data.read()
            race.image2 = form.image2.data.read()
            db_sess.commit()  # Сохраняем изменения
            return redirect('/')  # Возвращаемся на главную страницу
        else:
            abort(404)  # Гонка не найдена
    return render_template('add_race.html', title='Редактирование гонки', form=form)


# Удаление гонки (для администратора)
@app.route('/del_race/<race_id>', methods=['GET', 'POST'])
@login_required
@admin_required  # Доступ только для администраторов
def delete_race(race_id):
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    race = db_sess.query(Race).filter(Race.id == race_id).first()
    if race:
        db_sess.delete(race)  # Удаляем гонку
        db_sess.commit()  # Сохраняем изменения
    else:
        abort(404)  # Гонка не найдена
    return redirect('/')


# Добавление новой команды (для администратора)
@app.route('/add_team', methods=['GET', 'POST'])
@login_required
@admin_required  # Доступ только для администраторов
def add_team():
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    form = AddTeamForm()  # Форма добавления команды
    if request.method == 'POST' and form.validate_on_submit():
        team = Team(title=form.title.data, sponsor=form.sponsor.data, description=form.description.data)
        db_sess.add(team)  # Добавляем новую команду
        db_sess.commit()  # Сохраняем изменения
        return redirect(url_for('index'))  # Возвращаемся на главную страницу
    return render_template('add_team.html', title='Добавить команду', form=form)


# Список всех команд
@app.route('/teams')
def teams():
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    teams = db_sess.query(Team).all()  # Получаем список всех команд
    return render_template("teams.html", teams=teams)  # Рендерим шаблон списка команд


# Информация о конкретной команде
@app.route('/teams/<team_id>')
@login_required
def one_team(team_id):
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    team = db_sess.query(Team).filter(Team.id == team_id).first()  # Получаем конкретную команду
    return render_template("one_team.html", team=team)  # Рендерим шаблон одной команды


# Добавление результатов гонки (не реализовано должным образом)
@app.route('/add_results/<race_id>')
@login_required
@admin_required  # Доступ только для администраторов
def add_results(race_id):
    db_sess = db_session.create_session()  # Создаем сессию базы данных
    form = AddResForm()  # Форма добавления результата
    if request.method == 'POST' and form.validate_on_submit():
        pass  # Тут должна быть логика добавления результатов гонки
    return render_template('add_team.html', title='Добавить команду', form=form)


if __name__ == '__main__':
    main()  # Запуск основного приложения