import flask
from flask import jsonify, make_response, request

from data import db_session
from data.user import User

blueprint = flask.Blueprint(
    'user_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/user', methods=['GET', 'POST'])
def users():
    if request.method == 'GET':
        db_sess = db_session.create_session()
        user = db_sess.query(User).all()
        return jsonify(
            {
                'user':
                    [item.to_dict(only=('surname', 'name', 'email', 'is_admin'))
                     for item in user]
            }
        )
    if not request.json:
        return make_response(jsonify({'error': 'Empty request'}), 400)
    elif not all(key in request.json for key in
                 ['surname', 'name', 'email', 'is_admin']):
        return make_response(jsonify({'error': 'Bad request'}), 400)
    elif any(key not in ['surname', 'name', 'email', 'is_admin'] for key in request.json):
        return make_response(jsonify({'error': 'Bad request'}), 400)
    db_sess = db_session.create_session()
    user = User(
        surname=request.json['surname'],
        name=request.json['name'],
        email=request.json['email'],
        is_admin=request.json['is_admin']
    )
    db_sess.add(user)
    db_sess.commit()
    return jsonify({'id': user.id})

@blueprint.route('/api/user/<user_id>', methods=['GET'])
def user_id(user_id):
    db_sess = db_session.create_session()
    if not user_id.isdigit():
        return make_response(jsonify({'error': 'Неверный формат ID пользователя.'}), 400)

    cur_user = db_sess.query(User).filter(User.id == int(user_id)).first()
    if not cur_user:
        return make_response(jsonify({'error': 'Поьзователь не найден.', 'status': 404}), 404)

    return jsonify({
        'user': [{
            'surname': cur_user.surname,
            'name': cur_user.name,
            'email': cur_user.email,
            'is_admin': cur_user.is_admin
        }]
    }), 200

@blueprint.route('/api/del_users/<int:users_id>', methods=['DELETE'])
def delete_users(users_id):
    db_sess = db_session.create_session()
    cur_user = db_sess.query(User).get(users_id)
    if not cur_user:
        return make_response(jsonify({'error': 'Not found'}), 404)
    db_sess.delete(cur_user)
    db_sess.commit()
    return jsonify({'success': 'OK'})