import os
from shutil import copy2
import sqlite3 as sql
from flask import Flask, render_template, request

repo = Flask(__name__)


def connect():
    conn = sql.connect("images.db")
    cur = conn.cursor()
    return (conn, cur)


"""Buy Product"""
@repo.route("/buy/<product>")
def buy(product):
    return render_template("getval.html", message="Enter the quantity you want to buy")

@repo.route("/buy/<product>", methods=['POST'])
def buy_post(product):
    if not product:
        return render_template("message.html", message="Invalid Product!")

    number = None

    try:
        number = int(request.form['num'])
        if number < 0:
            return render_template("message.html", message="Invalid Amount!")
    except ValueError:
        return render_template("message.html", message="Invalid Amount!")

    (conn, cur) = connect()
    cur.execute("SELECT rowid, buy_price FROM items WHERE rowid = ?", (product,))

    item = cur.fetchone()

    if not item:
        return render_template("message.html", message="Invalid product")
    (rowid, buy_price) = item

    print("Processed transaction of value $%.2f" % (buy_price * number))

    cur.execute("UPDATE items SET amt = amt + ? WHERE rowid = ?", (number, product))
    conn.commit()

    global bought
    bought += number * buy_price
    global money
    money -= number * buy_price

    return render_template("message.html", message="Transaction Complete")

"""Sell Product"""
@repo.route("/sell/<product>")
def sell(product):
    return render_template("getval.html", message="Enter the quantity you want to sell")


@repo.route("/sell/<product>", methods=['POST'])
def sell_post(product):
    if not product:
        return render_template("message.html", message="Invalid Product!")

    number = None

    try:
        number = int(request.form['num'])
        if number < 0:
            return render_template("message.html", message="Invalid Amount!")
    except ValueError:
        return render_template("message.html", message="Invalid Amount!")

    (conn, cur) = connect()
    cur.execute("SELECT rowid, sell_price, amt FROM items WHERE rowid = ?", (product,))

    item = cur.fetchone()

    if not item:
        return render_template("message.html", message="Invalid product")
    (rowid, sell_price, amt) = item

    if amt < number:
        return render_template("message.html", message="Out of Stock!")

    print("Processed transaction of value $%.2f" % (sell_price * number))

    cur.execute("UPDATE items SET amt = amt - ? WHERE rowid = ?", (number, product))
    conn.commit()

    global sold
    sold += number * sell_price
    global money
    money += number * sell_price

    return render_template("message.html", message="Transaction Complete")

"""Edit Product"""
@repo.route("/edit/<product>")
def edit(product):

    (conn, cur) = connect()
    cur.execute("SELECT buy_price, sell_price, amt FROM items WHERE rowid = ?", (product,))
    item = cur.fetchone()

    (buy_price, sell_price, amt) = item

    return render_template("edit.html", buy=buy_price, sell=sell_price, amount=amt)

@repo.route("/edit/<product>", methods=['POST'])
def edit_post(product):

    if not product:
        return render_template("message.html", message="Invalid Product!")

    bprice = 0
    sprice = 0
    amount = 0

    try:
        bprice = float(request.form['buy_price'])
        sprice = float(request.form['sell_price'])
        amount = int(request.form['amount'])

        if amount < 0 or bprice < 0 or sprice < 0:
            return render_template("message.html", message="Invalid Entry!")
    except ValueError:
        return render_template("message.html", message="Invalid Entry!")

    (conn, cur) = connect()
    cur.execute("SELECT rowid FROM items WHERE rowid = ?", (product,))
    item = cur.fetchone()

    if not item:
        return render_template("message.html", message="Invalid product")

    (rowid) = item[0]

    print("Editing prices of {}".format(product))

    if bprice is not None:
        cur.execute("UPDATE items SET buy_price = ? WHERE rowid = ?", (bprice, rowid))

    if sprice is not None:
        cur.execute("UPDATE items SET sell_price = ? WHERE rowid = ?", (sprice, rowid))

    if amount is not None:
        cur.execute("UPDATE items SET amt = ? WHERE rowid = ?", (amount, rowid))

    conn.commit()
    return render_template("message.html", message="Transaction Complete")

"""Get Money"""
@repo.route("/money")
def get_money():

    return render_template("getval.html", message="Enter the amount of money you want to add or remove")

@repo.route('/money', methods=['POST'])
def money_post():
    msg = None
    global money

    if request.method == 'POST':

        try:
            cost = float(request.form['num'])
            money += round(cost, 2)
            msg = "You now have ${:.2f}".format(money)
        except ValueError:
            msg = "Invalid entry!"

    return render_template('message.html', message=msg)

@repo.route("/clear")
def clear():
    initialize()
    return render_template("message.html", message="Database Cleared.")


"""Instantiate DB"""
def initialize():
    (conn, cur) = connect()

    cur.execute("DROP TABLE IF EXISTS items")
    cur.execute("CREATE TABLE items (name TEXT, path TEXT, buy_price REAL, sell_price REAL, amt INTEGER)")
    cur.execute("""INSERT INTO items (name, path, buy_price, sell_price, amt) VALUES \
        ('Starry Night', 'images/starry_night.jpg', 50.00, 120.00, 8), \
        ('Last Supper', 'images/supper.jpg', 100.00, 270.00, 3), \
        ('American Gothic', 'images/gothic.jpg', 15.00, 18.50, 34), \
        ('Mona Lisa', 'images/monalisa.jpg', 600.00, 850.00, 1), \
        ('Great Waves', 'images/wave.jpg', 3.00, 4.79, 3129)
    """)

    # Commit the db changes
    conn.commit()
    print("Initialized database")
    global bought, sold, money

    bought = 0
    sold = 0
    money = 1000

@repo.route("/")
def home_page():
    (_, cur) = connect()
    cur.execute("SELECT rowid, * FROM items")

    rows = cur.fetchall()

    items = []
    for row in rows:
        items.append({
            "id":    row[0],
            "name":  row[1],
            "src":   "/static/%s" % (row[2]),
            "buy_price": "$%.2f" % (row[3]),
            "sell_price": "$%.2f" % (row[4]),
            "amt": "%d left" % (row[5])
        })



    return render_template("index.html", items=items, bought="$%.2f" % bought, sold="$%.2f" % sold, cost="$%.2f" % money)


@repo.route("/add")
def add():
    return render_template("add.html")

@repo.route("/add", methods=['POST'])
def add_post():

    try:
        name = str(request.form['name'])
        path = os.path.expanduser(str(request.form['path']))
        buy_price = float(request.form['buy_price'])
        sell_price = float(request.form['sell_price'])
        amt = int(request.form['amt'])

        if amt < 0 or buy_price < 0 or sell_price < 0 or not os.path.isfile(path):
            return render_template("message.html", message="Invalid Entry!")

    except ValueError:
        return render_template("message.html", message="Invalid Entry!")

    if os.path.basename(path) in os.listdir("./static/images"):
        return render_template("message.html", message="This image has the same name as an existing one.")
    else:
        copy2(path, "./static/images")

    path = "images/" + os.path.basename(path)
    (conn, cur) = connect()

    cur.execute("INSERT INTO items (name, path, buy_price, sell_price, amt) VALUES \
        (?, ?, ?, ?, ?)", (name, path, buy_price, sell_price, amt))

    conn.commit()
    return render_template("message.html", message="The item was added")

@repo.route("/remove/<product>")
def remove(product):

    if not product:
        return render_template("message.html", message="Invalid Product!")

    (conn, cur) = connect()

    cur.execute("SELECT path FROM items WHERE rowid = ?", (product,))
    item = cur.fetchone()

    if not item:
        return render_template("message.html", message="Invalid product")
    (path) = item[0]
    path = "./static/" + path

    cur.execute("DELETE FROM items WHERE rowid = ?", (product,))
    conn.commit()
    os.remove(path)

    return render_template("message.html", message="Item removed")

if __name__ == '__main__':
    initialize()
    repo.run(debug = True)