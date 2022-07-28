import time
import requests
from bs4 import BeautifulSoup
from flask import request, flash, render_template, redirect, url_for
from flask_login import login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from parse_olx.robber import app, db
from parse_olx.robber.models import User


@app.route('/', methods=['GET', 'POST'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')

    if login and password:
        user = User.query.filter_by(login=login).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            # next_page = request.args.get('next')

            return redirect(url_for('index'))
        else:
            flash('Login or password is not correct')
    else:
        flash('Please fill login and password fields')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    login = request.form.get('login')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    if request.method == 'POST':
        if not (login or password or password2):
            flash('Please, fill all fields!')
        elif password != password2:
            flash('Passwords are not equal!')
        else:
            hash_pwd = generate_password_hash(password)
            new_user = User(login=login, password=hash_pwd)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login_page'))

    return render_template('register.html')


@app.route('/index')
@login_required
def index():
    return render_template('index.html')


@app.route('/parser_olx', methods=['GET', 'POST'])
@login_required
def parser_olx():
    url = 'https://www.olx.ua/d/uk/nedvizhimost/kvartiry/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    card_with_data = soup.find_all('div', class_='css-19ucd76')
    name = []
    price = []
    image = []

    for n, i in enumerate(card_with_data, start=1):
        itemName = i.find('h6', class_='css-v3vynn-Text eu5v0x0')
        itemPrice = i.find('p', class_='css-wpfvmn-Text eu5v0x0')
        itemImage = i.find('img')
        # каждое 7 объявление на новой странице это реклама которая
        #  подходит по классу, но не подходит по данным поэтому такая проверка
        if itemPrice and itemName and itemImage is not None:
            itemName = itemName.text.strip()
            itemPrice = itemPrice.text
            itemImage = itemImage.get('src')
            name.append(itemName)
            price.append(itemPrice)
            image.append(itemImage)
            time.sleep(5)

    return render_template('parser_data.html', name=name, price=price, image=image)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('hello_world'))


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login_page') + '?next=' + request.url)

    return response