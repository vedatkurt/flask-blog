from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#----------------
# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args,**kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapınız...","danger")
            return redirect(url_for("login",))
    return decorated_function

class ArticleForm(Form):
    title = StringField("Makale başlığı :",validators=[validators.Length(min=5,max=100)])
    content = TextAreaField("Makale içeriği :",validators=[validators.Length(min=10)])

class RegisterForm(Form):
    name = StringField("Isim Soyisim :",validators=[validators.Length(min=4,max=25)])
    username = StringField("Kullanici Adi :",validators=[validators.Length(min=5,max=30)])
    email = StringField("E-Mail : ",validators=[validators.Length(min=10,max=50)])
    password = PasswordField("Parola : ",validators=[
        validators.DataRequired(message = "Lutfen bir parola belirleyin"),
        validators.EqualTo(fieldname="confirm", message = "Parola uyusmuyor")
        ])
    confirm = PasswordField("Parola Dogrula")

class LoginForm(Form):
    username = StringField("Kullanici Adi :",validators=[validators.Length(min=5,max=30)])
    password = PasswordField("Parola : ",validators=[validators.Length(min=5,max=30)])

app = Flask(__name__)
app.secret_key = "ybblog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

#----------
# Ana Sayfa
@app.route("/")
def index():
    return render_template("index.html", answer="hayir")

#---------
# Hakkimda
@app.route("/about")
def about():
    numbers = [1,2,3,4,5]

    articles = [        
        {"id":1,"title":"Article1","content":"Content1"},
        {"id":2,"title":"Article2","content":"Content2"} 
                ]
    return render_template("about.html", warningList=numbers, articles=articles)

#---------------
# Kontrol Paneli
@app.route("/dashboard")
@login_required
def dashboard():
    #-----------------------
    # mysql Cursor olusturma
    sql = "SELECT * FROM articles where author = %s"
    cursor = mysql.connection.cursor()
    result = cursor.execute(sql,(session["username"],))
    
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)

#-------------
# All Articles
@app.route("/articles")
@login_required
def articles():
    #-----------------------
    # mysql Cursor olusturma
    sql = "SELECT * FROM articles "
    cursor = mysql.connection.cursor()
    result = cursor.execute(sql)
    
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")

#---------------
# Article Detail
@app.route("/article/<string:id>")
@login_required
def article(id):
    #-----------------------
    # mysql Cursor olusturma
    sql = "SELECT * FROM articles where id = %s"
    cursor = mysql.connection.cursor()
    result = cursor.execute(sql,(id,))
        
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return redirect(url_for("login"))
        
#------------
# Add Article
@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        #-----------------------
        # mysql Cursor olusturma
        sql = "INSERT INTO articles (title,author,content) values (%s,%s,%s)"
        cursor = mysql.connection.cursor()
        cursor.execute(sql,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        
        flash("Makale başarılı şekilde kaydedildi","success")

        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html", form=form)

#---------------
# Update Article
@app.route("/update/<string:id>",methods=["GET","POST"])
@login_required
def updatearticle(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sql = "SELECT * FROM articles where author = %s and id = %s"
        result = cursor.execute(sql,(session["username"],id))
    
        if result == 0:
            flash("Boyle bir makale yok veya bu isleme yetkiniz yok!","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("updatearticle.html",form=form)
    else:
        # POST REQUEST
        form = ArticleForm(request.form)
        if form.validate():
            newtitle = form.title.data
            newcontent = form.content.data

            #-----------------------
            # mysql Cursor olusturma
            cursor = mysql.connection.cursor()
            sql = "UPDATE articles set title = %s, content=%s where id=%s"
            cursor.execute(sql,(newtitle,newcontent,id))
            mysql.connection.commit()
            cursor.close()
        
            flash("Makale başarılı şekilde güncellendi!","success")

            return redirect(url_for("dashboard"))

#---------------
# Delete Article
@app.route("/delete/<string:id>")
@login_required
def deletearticle(id):
    sql = "SELECT * FROM articles where author = %s and id = %s"
    cursor = mysql.connection.cursor()
    result = cursor.execute(sql,(session["username"],id,))

    if result > 0:
        sql = "DELETE FROM articles where id = %s"
        cursor = mysql.connection.cursor()
        result = cursor.execute(sql,(id,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Boyle bir makale yok veya bu isleme yetkiniz yok!","danger")
        return redirect(url_for("index"))

#--------
# Search
@app.route("/search",methods=["GET","POST"])
def searcharticle():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        #-----------------------
        # mysql Cursor olusturma
        cursor = mysql.connection.cursor()
        sql = "SELECT * from articles where title like '%" + keyword + "%'"
        result = cursor.execute(sql)

        if result == 0:
            flash("Aranan kelimeye uygun bir makale bulunamadı !","warning")
            return redirect(url_for("articles"))
        else:
            searchedArticles = cursor.fetchall()
            return render_template("articles.html",articles = searchedArticles)

#---------
# Register
@app.route("/register",methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email  = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        #-----------------------
        # mysql Cursor olusturma
        cursor = mysql.connection.cursor()
        sql = "INSERT INTO users (name,username,email,password) values (%s,%s,%s,%s)"
        cursor.execute(sql,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()
        
        flash("Kullanıcı başarılı şekilde kaydedildi","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)

#---------
# Login
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST" and form.validate():
        username = form.username.data
        password_entered = form.password.data

        #-----------------------
        # mysql Cursor olusturma
        sql = "SELECT * FROM users where username = %s"
        cursor = mysql.connection.cursor()
        result = cursor.execute(sql,(username,))
        
        if result > 0:
            data = cursor.fetchone()
            passwordFromDB = data["PASSWORD"]
            if sha256_crypt.verify(password_entered,passwordFromDB):
                flash("Başarılı giriş yaptınız.","success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz...","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunamadı !","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html", form=form)

#---------
# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)