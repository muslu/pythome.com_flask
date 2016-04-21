# -*- coding: utf-8 -*-

import MySQLdb
import memcache

from flask import Flask, render_template, request, url_for, redirect, session, send_from_directory
from flask.ext.github import GitHub

app = Flask(__name__)
app.secret_key = 'cem_emir_yuksektepe'

memc = memcache.Client(['127.0.0.1:11211'], debug=1)

app.config['GITHUB_CLIENT_ID'] = ''
app.config['GITHUB_CLIENT_SECRET'] = ''

github = GitHub(app)

import logging, sys

logging.basicConfig(stream=sys.stderr)


def connection():
    conn = MySQLdb.connect(host="", user="", passwd="", db=", charset="utf8",
                           use_unicode=True)
    c = conn.cursor()
    return c, conn


@app.route('/')
def anasayfa():
    c, conn = connection()

    ipadresi = request.remote_addr

    kayitlar = memc.get("anasayfa_" + str(ipadresi).encode('utf8'))

    if not kayitlar:
        c.execute("SELECT * FROM Hatalar order by turkce desc")

        kayitlar = c.fetchall()

        memc.set("anasayfa_" + str(ipadresi).encode('utf8'), kayitlar, 60)

    c.execute("select id, HataEng from Hatalar order by HataTuru")
    hataarama = c.fetchall()

    return render_template("index.html", kayitlar=kayitlar, ipadresi=ipadresi, hataarama=hataarama)


@app.route('/ara/', methods=['GET'])
def arama():

    ipadresi = request.remote_addr

    qq = request.args.get('q')

    c, conn = connection()

    c.execute("select * from Hatalar where HataEng like %s", ["%" + qq + "%"])
    kayitlar = c.fetchall()

    c.execute("select id, HataEng from Hatalar order by HataTuru")
    hataarama = c.fetchall()

    return render_template("index.html", kayitlar=kayitlar, ipadresi=ipadresi, hataarama=hataarama)


@app.route('/<path:modul>/<path:tur>/<path:slug>')
def detay(modul, tur, slug):
    if 'githubid' in session:
        githubid_session = True
    else:
        githubid_session = False

    c, conn = connection()

    slug = slug[:-1]

    detay = memc.get(slug.encode('utf8'))

    if not detay:
        c.execute("select * from Hatalar where Slug = %s", [slug])
        detay = c.fetchone()

        memc.set(slug.encode('utf8'), detay, 60)

        c.execute("select * from Hatalar where HataTuru = %s", [tur])
        digerhataturu = c.fetchall()

    else:
        digerhataturu = {}

    return render_template("detay.html", detay=detay, digerhataturu=digerhataturu, githubid_session=githubid_session)


@app.route('/cevir/<path:slug>')
def cevir(slug):
    if 'githubid' in session:

        c, conn = connection()

        slug = slug[:-1]

        c.execute("SELECT HataEng, id, turkce, german, hindi, slug FROM Hatalar where  Slug = %s", [slug])

        detay = c.fetchone()

        return render_template("cevir.html", detay=detay)

    else:
        return redirect(url_for('anasayfa'))


@app.route('/cevirmen/', methods=['POST'])
def cevirmen():
    if request.method == 'POST':
        c, conn = connection()

        id = request.form['id']
        turkce = request.form['turkce']
        hindi = request.form['hindi']
        german = request.form['german']
        slug = request.form['slug']

        c.execute("UPDATE HataBull.Hatalar SET turkce = %s, german = %s, hindi = %s WHERE  id = %s;", (
            [turkce, german, hindi, id]))

        conn.commit()

        return redirect('/cevir/' + slug + '/', 301)
        # return redirect(url_for('anasayfa'))


@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/login')
def login():
    gelen_url = request.referrer
    return github.authorize(scope="user:email", redirect_uri="http://www.pythome.com/github?next=" + gelen_url)


@app.route('/github')
@github.authorized_handler
def authorized(oauth_token):
    gidilecek_url = request.args.get('next')

    if oauth_token is None:
        redirect(url_for("login"))
    else:
        session['githubid'] = oauth_token

    return redirect(gidilecek_url)


@app.route('/logout')
def logout():
    session.pop('githubid', None)
    return redirect(url_for('anasayfa'))


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')


