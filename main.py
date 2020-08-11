from flask import Flask, render_template, sessions, session, request
from datetime import datetime
import hashlib
import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="domaci78"
)

app = Flask(__name__)

app.secret_key = "nesto"  # kada se radi sa sesijama


@app.route("/register")
def register():
    # provera da li je korisnik ulogovan
    return render_template("register.html")

@app.route("/registracija", methods=["POST"])
def registracija():
    korime = request.form["korime"]
    email = request.form["email"]
    password = request.form["password"]
    potvrda = request.form["potvrda"]
    pol = request.form["pol"]
    godina = request.form["godina"]
    tip = request.form["tip"]

    slika = request.files["slika"]
    slika.save(slika.filename)

    datum = datetime.today().strftime('%y-%m-%d')

    if password == potvrda:  # proveravamo da li se mecuje pass i potvrda
        password = hashlib.sha256(password.encode()).hexdigest()

        mc = mydb.cursor()
        mc.execute("SELECT * FROM korisnici WHERE korime='" + korime + "'")  # prolazimo kroz sve korisnike
        res = mc.fetchall()
        if mc.rowcount == 0:  # ukoliko nema korisnika, tj 0, onda upisujemo u bazu
            # registrovanje korisnika
            mc.execute(
                "INSERT INTO korisnici VALUES(null,'" + korime + "','" + email + "','" + password + "','" + pol + "','" + godina + "','" + tip + "','" + slika.filename + "','" + datum + "')")
            mydb.commit()
            return "registrovani ste"
        else:
            return render_template("register.html", odg="korisnicko ime zauzeto")

    else:
        return render_template("register.html", odg="sifra i potvrda se ne poklapaju")


@app.route("/login")
def login():
    if "korime" in session:  # proveravamo sesiju
        return "vec ste ulogovani"
    # provera da li je korisnik ulogovan
    return render_template("login.html")


@app.route("/logovanje", methods=["POST"])
def logovanje():
    korime = request.form["korime"]
    password = request.form["password"]

    password = hashlib.sha256(password.encode()).hexdigest()

    mc = mydb.cursor()
    mc.execute("SELECT * FROM korisnici WHERE korime='" + korime + "' AND sifra='" + password + "'")
    res = mc.fetchall()
    print(res)
    if mc.rowcount == 0:  # ukoliko je prazno
        return render_template("login.html", odg="korisnik ne postoji, pogresna sifra ili korisnicko ime")
    else:  # u suprotnom uzimam korinicko ime i podatke koji su registrovani
        session["korime"] = korime
        session["podaci"] = res[0]
        print(session["korime"])
        print(session["podaci"])

        return "ulogovali ste se"


@app.route("/logout")
def logout():
    session.pop("korime", None)  # sesion.pop ubijamo sesiju drugi parametar je uvek none
    session.pop("logout", None)
    return "logout"

@app.route("/dodavanje-proizvoda",methods=["POST"])
def dodaj():
    naziv = request.form["naziv"]
    cena = request.form["cena"]
    kolicina = request.form["kolicina"]
    slika = request.files["slika"]
    slika.save(slika.filename)
    print(session["podaci"][0])

    mc = mydb.cursor()
    mc.execute("INSERT INTO proizvodi VALUES(null,'" + naziv + "','" + cena + "','" + kolicina + "','" + slika.filename + "',"+str(session["podaci"][0])+")")
    mydb.commit()

    return render_template("dodajProizvod.html",odg="proizvod uspesno dodat")

@app.route("/dodaj-proizvod")
def dodavanjeProizvoda():
    #print("podaci")
    #print(session["podaci"][6])    ovako uzimamo status korisnika
    #print(session["korime"])
    if "korime" in session:
        if session["podaci"][6] == "prodavac":
            return render_template("dodajProizvod.html")
        else:
            return "admin"
    else:
        return render_template("login.html")

@app.route("/")
def index():
    mc = mydb.cursor()

    if "korime" in session:#ovde se proverava da li je korisnik uopste ulogovan, ako korisnik nije ulogovan session["podaci"] ne postoji

        if session["podaci"][6] == "prodavac":
            mc.execute("SELECT * FROM proizvodi WHERE prodavacId=" + str(session["podaci"][0]))
            res = mc.fetchall()

        if mc.rowcount == 0:
            return render_template("indexProdavac.html", odg="nema proizvoda")
        else:
            return render_template("indexProdavac.html", odg="proizvodi", lista=res)

    else:
        mc.execute("SELECT * FROM proizvodi ")
        res = mc.fetchall()
        if mc.rowcount == 0:
            return render_template("index.html", odg="nema proizvoda")
        else:
            return render_template("index.html", odg="proizvodi", lista=res)



@app.route("/deleteProizvod",methods=["POST"])
def brisanjeProizvod():
    id = request.form["id"]

    mc = mydb.cursor()
    mc.execute("DELETE FROM proizvodi WHERE id = "+id)
    mydb.commit()

    mc = mydb.cursor()
    if session["podaci"][6] == "prodavac":
        mc.execute("SELECT * FROM proizvodi WHERE prodavacId=" + str(session["podaci"][0]))
    else:
        mc.execute("SELECT * FROM proizvodi ")

    res = mc.fetchall()
    return render_template("indexProdavac.html", odg="proizvod uklonjen", lista=res)

@app.route("/updateProizvod/<id>")
def updateProizvod(id):
    mc = mydb.cursor()
    mc.execute("SELECT * FROM proizvodi WHERE id = "+str(id))
    res = mc.fetchall()

    return render_template("updateProizvod.html",proizvod=res[0])

@app.route("/sacuvaj",methods=["POST"])
def sacuvaj():
    id = request.form["id"]
    naziv = request.form["naziv"]
    cena = request.form["cena"]
    kolicina = request.form["kolicina"]


    #print(naziv+" "+cena+" "+kolicina+" "+id)

    mc = mydb.cursor()
    mc.execute("UPDATE proizvodi SET naziv='"+naziv+"',cena="+cena+",kolicina="+kolicina+" WHERE id = " + id)
    mydb.commit()

    mc = mydb.cursor()
    if session["podaci"][6] == "prodavac":
        mc.execute("SELECT * FROM proizvodi WHERE prodavacId=" + str(session["podaci"][0]))
    else:
        mc.execute("SELECT * FROM proizvodi ")

    res = mc.fetchall()

    if "korime" in session:
        if mc.rowcount == 0:
            return render_template("indexProdavac.html", odg="izmene sacuvane")
        else:
            return render_template("indexProdavac.html", odg="izmene sacuvane", lista=res)
    return "ok"

@app.route("/administracija")
def admin():
    if "korime" in session:
        if session["podaci"][6] == "administrator":

            mc = mydb.cursor()
            mc.execute("SELECT * FROM korisnici ")
            res = mc.fetchall()

            return render_template("admin.html",korisnici=res)
        else:
            return "nemate prava pristupa <a href='/'>nazad</a>"
    else:
        return render_template("login.html")

@app.route("/obrisiKorisnika",methods=["POST"])
def obrisi():
    id = request.form["id"]

    mc = mydb.cursor()
    mc.execute("DELETE FROM korisnici WHERE id="+str(id))
    mydb.commit()

    if "korime" in session:
        if session["podaci"][6] == "administrator":

            mc = mydb.cursor()
            mc.execute("SELECT * FROM korisnici ")
            res = mc.fetchall()

            return render_template("admin.html",korisnici=res)
        else:
            return "nemate prava pristupa <a href='/'>nazad</a>"
    else:
        return render_template("login.html")

#id korime email godina tip
@app.route("/izmeniKorisnika",methods=["POST"])
def izmeni():
    id = request.form["id"]
    korime = request.form["korime"]
    email = request.form["email"]
    godina = request.form["godina"]
    tip = request.form["tip"]

    mc = mydb.cursor()
    mc.execute("UPDATE korisnici SET korime='"+korime+"',email='"+email+"',godina='"+godina+"',tip='"+tip+"' WHERE id=" + str(id))
    mydb.commit()

    if "korime" in session:
        if session["podaci"][6] == "administrator":

            mc = mydb.cursor()
            mc.execute("SELECT * FROM korisnici ")
            res = mc.fetchall()

            return render_template("admin.html",korisnici=res)
        else:
            return "nemate prava pristupa <a href='/'>nazad</a>"
    else:
        return render_template("login.html")

app.run()
