from flask import render_template, redirect, flash, url_for, abort, request, current_app, make_response
from . import main
from ..models import User, Role, Permission, Post, PostComment, Notebook, NotebookComment
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, NotebookForm
from flask_login import login_required, current_user
from .. import db
from ..decorator import admin_required, permission_required
from werkzeug.utils import secure_filename
import time
import os


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['MYBLOG_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, show_followed=show_followed, pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['MYBLOG_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts, pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
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
        db.session.commit()
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


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = PostComment(body=form.body.data,
                              post=post,
                              author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // current_app.config['MYBLOG_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(PostComment.timestamp.asc()).paginate(
        page=page,
        per_page=current_app.config['MYBLOG_COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    # [post] for reuse of _posts.html
    return render_template('post.html', posts=[post], form=form, comments=comments, pagination=pagination)


@main.route('/edit-post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author_id and not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {username}')
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You are not following {username} anymore.')
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page=page,
        per_page=current_app.config['MYBLOG_FOLLOWERS_PER_PAGE'],
        error_out=False)
    # rendering is simpler
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('followers.html', user=user, title='Followers of', endpoint='.followers',
                           pagination=pagination, follows=follows)


@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page=page, per_page=current_app.config['MYBLOG_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)  # 30 days
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = PostComment.query.order_by(PostComment.timestamp.desc()).paginate(
        page=page,
        per_page=current_app.config['MYBLOG_COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    return render_template('moderate.html', comments=comments, pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = PostComment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    return redirect(url_for('.moderate', page=page))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = PostComment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    return redirect(url_for('.moderate', page=page))


@main.route('/notebooks/', methods=['GET', 'POST'])
def notebooks():
    form = NotebookForm()
    if current_user.can(Permission.ADMIN) and form.validate_on_submit():
        author = current_user._get_current_object()
        imagename = None
        if form.image.data:
            imagename = secure_filename(form.image.data.filename)
            full_imagename = os.path.join(current_app.config['MYBLOG_NOTEBOOK_DIR'], imagename)
            if os.path.exists(full_imagename):
                imagename = f's{int(time.time())}_{imagename}'
                full_imagename = os.path.join(current_app.config['MYBLOG_NOTEBOOK_DIR'], imagename)
            form.image.data.save(full_imagename)

        if form.file.data:
            filename = secure_filename(form.file.data.filename)
            full_filename = os.path.join(current_app.config['MYBLOG_NOTEBOOK_DIR'], filename)
            if os.path.exists(full_filename):
                filename = f's{int(time.time())}_{filename}'
                full_filename = os.path.join(current_app.config['MYBLOG_NOTEBOOK_DIR'], filename)
            form.file.data.save(full_filename)
        else:
            flash('File cannot be empty.')
            return redirect(url_for('.notebooks'))
        introduction = None
        if form.introduction.data:
            introduction = form.introduction.data
        if form.file_show_name.data:
            file_show_name = form.file_show_name.data
        else:
            file_show_name = filename
        notebook = Notebook(file=filename, image=imagename, introduction=introduction, author=author,
                            file_show_name=file_show_name)
        db.session.add(notebook)
        db.session.commit()
        return redirect(url_for('.notebooks'))
    page = request.args.get('page', 1, type=int)
    pagination = Notebook.query.order_by(Notebook.file.asc()).paginate(
        page=page, per_page=current_app.config['MYBLOG_NOTEBOOKS_PER_PAGE'], error_out=False
    )
    notebooks = pagination.items
    return render_template('notebooks.html', form=form, notebooks=notebooks, pagination=pagination)


@main.route('/edit-notebook/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_notebook(id):
    notebook = Notebook.query.get_or_404(id)
    if current_user != notebook.author_id and not current_user.can(Permission.ADMIN):
        abort(403)
    form = NotebookForm()
    if form.validate_on_submit():
        if form.image.data:
            imagename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(current_app.config['MYBLOG_NOTEBOOK_DIR'], imagename))
            notebook.image = imagename
        if form.file.data:
            filename = secure_filename(form.file.data.filename)
            form.file.data.save(os.path.join(current_app.config['MYBLOG_NOTEBOOK_DIR'], filename))
            notebook.file = filename
        if form.introduction.data:
            notebook.introduction = form.introduction.data
        if form.file_show_name.data:
            notebook.file_show_name = form.file_show_name.data
        db.session.add(notebook)
        db.session.commit()
        flash('The notebook has been updated.')
        return redirect(url_for('.notebook', id=notebook.id))
    form.image.data = notebook.image
    form.file.data = notebook.file
    form.file_show_name.data = notebook.file_show_name
    form.introduction.data = notebook.introduction
    return render_template('edit_notebook.html', form=form)


@main.route('/notebook/<int:id>', methods=['GET', 'POST'])
def notebook(id):
    notebook = Notebook.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = NotebookComment(body=form.body.data,
                                  notebook=notebook,
                                  author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.')
        return redirect(url_for('.notebook', id=notebook.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (notebook.comments.count() - 1) // current_app.config['MYBLOG_COMMENTS_PER_PAGE'] + 1
    pagination = notebook.comments.order_by(NotebookComment.timestamp.asc()).paginate(
        page=page,
        per_page=current_app.config['MYBLOG_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('notebook.html', notebooks=[notebook], form=form, comments=comments, pagination=pagination)


@main.route('/delete-notebook/<int:id>')
@login_required
def delete_notebook(id):
    notebook = Notebook.query.get_or_404(id)
    if current_user != notebook.author_id and not current_user.can(Permission.ADMIN):
        abort(403)

    # delete files on hardware
    full_filename = os.path.join(current_app.config['MYBLOG_NOTEBOOK_DIR'], notebook.file)
    if os.path.exists(full_filename):
        os.remove(full_filename)
    full_imagename = os.path.join(current_app.config['MYBLOG_NOTEBOOK_DIR'], notebook.image)
    if os.path.exists(full_imagename):
        os.remove(full_imagename)
    db.session.delete(notebook)
    db.session.commit()
    return redirect(url_for('.notebooks'))


@main.route('/about')
def about():
    return render_template('about.html')
