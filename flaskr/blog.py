from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username,'
        ' (SELECT COUNT(*) FROM upvote u WHERE p.id = u.post_id) AS upvotes,'
        ' (SELECT COUNT(*) FROM downvote d WHERE p.id = d.post_id) AS downvotes'
        ' FROM post p'
        ' JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:id>/upvote', methods=('GET',))
@login_required
def upvote(id):
    db = get_db()

    upvote = get_upvote(id)
    downvote = get_downvote(id)

    if downvote is not None:
        db.execute('DELETE FROM downvote WHERE user_id = ? AND post_id = ?', (g.user['id'], id))
        db.commit()

    if upvote is None:
        db.execute('INSERT INTO upvote (user_id, post_id) VALUES (?, ?)', (g.user['id'], id))
        db.commit()

    return render_template('blog/index.html')


@bp.route('/<int:id>/downvote', methods=('GET',))
@login_required
def downvote(id):
    db = get_db()

    upvote = get_upvote(id)
    downvote = get_downvote(id)

    if upvote is not None:
        db.execute('DELETE FROM upvote WHERE user_id = ? AND post_id = ?', (g.user['id'], id))
        db.commit()

    if downvote is None:
        db.execute('INSERT INTO downvote (user_id, post_id) VALUES (?, ?)', (g.user['id'], id))
        db.commit()

    return render_template('blog/index.html')


def get_upvote(id):
    upvote = get_db().execute(
        'SELECT id, user_id, post_id'
        ' FROM upvote'
        ' WHERE user_id = ? AND post_id = ?',
        (g.user['id'], id)
    ).fetchone()
    return upvote


def get_downvote(id):
    downvote = get_db().execute(
        'SELECT id, user_id, post_id'
        ' FROM downvote'
        ' WHERE user_id = ? AND post_id = ?',
        (g.user['id'], id)
    ).fetchone()
    return downvote
    