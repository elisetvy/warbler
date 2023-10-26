import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized

from flask_bcrypt import Bcrypt

from forms import UserAddForm, LoginForm, MessageForm, CSRFProtectForm, EditProfileForm
from models import db, connect_db, User, Message, Like

load_dotenv()
bcrypt = Bcrypt()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


@app.before_request
def do_csrf():
    """Implement CSRF."""
    g.csrf_form = CSRFProtectForm()


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Log out user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and represent form."""

    do_logout()

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
                location=form.location.data or User.location.default.arg
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data,
        )

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.post('/logout')
def logout():
    """Handle logout of user and redirect to homepage."""

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Guarding
    #
    # if form.validate_on_submit():
    do_logout()
    flash("Logged out.")
    return redirect("/login")
    #TODO: what going on here


##############################################################################
# General user routes:

@app.get('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html',
                           users=users)


@app.get('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/show.html',
                           user=user)


@app.get('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html',
                           user=user)


@app.get('/users/<int:user_id>/followers')
def show_followers(user_id):
    """Show list of user's followers."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html',
                           user=user)


@app.get('/users/<int:user_id>/likes')
def show_likes(user_id):
    """Show list of liked messages from this user"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # TODO: don't really need to pass in liked_messages explicitly?
    user = User.query.get_or_404(user_id)
    return render_template('/likes/show.html',
                           user=user,
                           liked_messages=user.liked_messages)


@app.post('/messages/<int:message_id>/like')
def like_message(message_id):
    """Like a message from another user."""

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    liked_message = Message.query.get_or_404(message_id)
    g.user.liked_messages.append(liked_message)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/likes")


@app.post('/messages/<int:message_id>/unlike')
def unlike_message(message_id):
    """Unlike a message"""

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    liked_message = Message.query.get_or_404(message_id)
    g.user.liked_messages.remove(liked_message)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/likes")


@app.post('/users/follow/<int:follow_id>')
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current user."""

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.post('/users/stop-following/<int:follow_id>')
def stop_following(follow_id):
    """Have current user stop following this user.

    Redirect to current user's following page."""

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update current user's profile."""

    if not g.user:
        raise Unauthorized()

    form = EditProfileForm(obj=g.user)

    if form.validate_on_submit():
        if User.authenticate(g.user.username, form.password.data):
            username = form.username.data
            email = form.email.data
            image_url = form.image_url.data
            header_image_url = form.header_image_url.data
            bio = form.bio.data
            location = form.location.data

            is_valid = True

            if User.query.filter(User.username == username).first() and username != g.user.username:
                form.username.errors = ["Username already exists!"]
                is_valid = False

            if User.query.filter(User.email == email).first() and email != g.user.email:
                form.email.errors = [
                    "Email is already associated with a user!"]
                is_valid = False

            if is_valid:
                g.user.username = username or g.user.username
                g.user.email = email or g.user.email
                g.user.image_url = image_url or g.user.image_url
                g.user.header_image_url = header_image_url or g.user.header_image_url
                g.user.bio = bio or g.user.bio
                g.user.location = location or g.user.location

                db.session.commit()

                return redirect(f'/users/{g.user.id}')

    return render_template('/users/edit.html',
                           form=form,
                           user=g.user)



@app.post('/users/delete')
def delete_user():
    """Delete user.

    Redirect to signup page."""
    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    for message in g.user.messages:
        db.session.delete(message)
        db.session.commit()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def add_message():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.""" #TODO: wth am I saying here

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/create.html',
                           form=form)


@app.get('/messages/<int:message_id>')
def show_message(message_id):
    """Show a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)
    return render_template('messages/show.html',
                           message=msg)


@app.post('/messages/<int:message_id>/delete')
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.

    Redirect to user page on success."""
    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.get('/')
def homepage():
    """Show homepage:

    - Anon users: no messages
    - Logged in: 100 most recent messages of self & followed_users."""

    if g.user:
        following = [following.id for following in g.user.following]

        messages = (Message
                    .query
                    # can concat lists
                    .filter((Message.user_id == g.user.id) | (Message.user_id.in_(following)))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html',
                               messages=messages)

    else:
        return render_template('home-anon.html')


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
