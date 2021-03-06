from flask import flash, redirect, render_template, url_for, current_app, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app import db
from . import main
from .forms import PostCreationForm, TagCreationForm, CommentCreationForm
from ..models import Post, Tag, Comment, User


@main.route('/')
def frontpage():
	page = request.args.get('page', 1, type=int)
	pagination = Post.query.order_by(Post.created_on.desc()).paginate(
		page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False
	)
	return render_template("main/frontpage.html", posts=pagination.items, tags=Tag.query.all(), pagination=pagination,
	                       prevpage=url_for('main.frontpage', page=pagination.prev_num),
	                       nextpage=url_for('main.frontpage', page=pagination.next_num))


@main.route('/post/<post_slug>', methods=['GET', 'POST'])
def post_detail(post_slug):
	post = Post.query.filter_by(slug=post_slug).first_or_404()
	form = CommentCreationForm()
	if form.validate_on_submit():
		comment = Comment(body=form.content.data, user=current_user, post=post)
		db.session.add(comment)
		try:
			db.session.commit()
		except IntegrityError:
			db.session.rollback()
			flash("There was an error while posting your comment")
	return render_template('main/postdetail.html', post=post, tags=Tag.query.all(), form=form)


@main.route('/tag/<tag_slug>')
def tagged_posts(tag_slug):
	page = request.args.get('page', 1, type=int)
	tag = Tag.query.filter_by(slug=tag_slug).first_or_404()
	pagination = tag.posts.order_by(Post.created_on.desc()).paginate(
		page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False
	)
	return render_template("main/frontpage.html", posts=pagination.items, tags=Tag.query.all(),
	                       blog_title="Tagged as " + tag.name, blog_subtitle="", title="Tagged as " + tag.name,
	                       pagination=pagination,
	                       prevpage=url_for('main.tagged_posts', tag_slug=tag_slug, page=pagination.prev_num),
	                       nextpage=url_for('main.tagged_posts', tag_slug=tag_slug, page=pagination.next_num))


@main.route('/create/post', methods=['GET', 'POST'])
@login_required
def create_post():
	post_form = PostCreationForm()
	post_form.tags.choices = [(tag.name, tag.name) for tag in Tag.query.all()]
	tag_form = TagCreationForm()

	if post_form.validate_on_submit():
		post = Post.query.filter_by(title=post_form.title.data).first()
		if post is None:
			p = Post(title=post_form.title.data, body=post_form.body.data, user=current_user)
			p.generate_slug()
			for tag_name in post_form.tags.data:
				tag = Tag.query.filter_by(name=tag_name).first()
				if tag is not None:
					p.tags.append(tag)
			db.session.add(p)
			try:
				db.session.commit()
			except IntegrityError:
				flash("There was an error creating the post")
				db.session.rollback()
		else:
			flash("There was an error creating the post")
		return redirect(url_for('main.frontpage'))
	elif tag_form.validate_on_submit():
		tag = Tag.query.filter_by(name=tag_form.name.data).first()

		if tag is None:
			t = Tag(name=tag_form.name.data)
			t.generate_slug()
			db.session.add(t)
			db.session.commit()
			post_form.tags.choices.append((t.name, t.name))
			flash("Tag created")
		else:
			flash("The tag already existed")
	return render_template("main/postcreate.html", post_form=post_form, tag_form=tag_form, blog_title="Post something!",
	                       blog_subtitle="Hope you're inspired")


@main.route('/user')
@login_required
def my_user():
	return render_template('main/account_info.html', user=current_user)


@main.route('/user/<username>')
def user_posts(username):
	page = request.args.get('page', 1, type=int)
	user = User.query.filter_by(username=username).first_or_404()
	pagination = user.posts.order_by(Post.created_on.desc()).paginate(
		page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False
	)
	return render_template("main/frontpage.html", posts=pagination.items, tags=Tag.query.all(),
	                       blog_title="Posts by " + user.username, blog_subtitle="", title="Posts by " + user.username,
	                       pagination=pagination,
	                       prevpage=url_for('main.user_posts', username=username, page=pagination.prev_num),
	                       nextpage=url_for('main.user_posts', username=username, page=pagination.next_num))
