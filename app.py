from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import sqlite3 as sql
import pandas as pd
import hashlib as hl
from search import runner, distance, sql_eval, similar
import setup
import datetime

app = Flask(__name__)
app.secret_key = 'secret'

#average rating of a seller
def generate_address_id():
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT address_ID FROM Address'
    cursor.execute(query)
    result_list = cursor.fetchall()
    connection.close()
    l = []
    for i in result_list:
        l.append(i[0])
    for j in range(10000):
        if j not in l:
            print(j)
            return j

@app.route('/contact/<int:listing_id>', methods=['GET','POST'])
def contact(listing_id):
    session['show_seller'] = not session['show_seller']
    return redirect(url_for('select_product',listing_id=listing_id))

@app.route('/mybids',methods=['GET','POST'])
def mybids():
    #find the list of bids from a username
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT a.* FROM Auction_Listings a JOIN Bids b ON a.Listing_ID = b.Listing_ID WHERE b.Bidder_Email = ? AND b.Bid_price = (SELECT MAX(Bids.Bid_price) FROM Bids WHERE Listing_ID = a.Listing_ID AND b.Bidder_Email=b.Bidder_Email)';
    result = cursor.execute(query, (session['email'],))
    result = result.fetchall()
    connection.close()
    return render_template('Product_listing.html', listings=result, seller=False)

@app.route('/rating-left', methods=['GET', 'POST'])
def rating_left():
    try:
        connection = sql.connect('Users.sqlite')
        cursor = connection.cursor()
        query = 'INSERT INTO Rating(Bidder_Email, Seller_Email, Date, Rating_Desc, Rating) VALUES(?, ?, ?, ?, ?)'
        date = datetime.date.today().strftime('%d/%m/%Y')
        bidder = session['email']
        seller = request.form['email']
        rating = request.form['rating']
        description = request.form['description']
        cursor.execute(query, (bidder,seller,date,description,rating))
        connection.commit()
        connection.close()
        return redirect(url_for('home'))
    except:
        return redirect(url_for('home'))


    return redirect(url_for('home'))

@app.route('/leave-rating', methods=['GET', 'POST'])
def leave_rating():
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'Select Seller_Email From Transactions WHERE Buyer_Email=?'
    result = cursor.execute(query, (session['email'],))
    l=[]
    for i in result:
        l.append(i[0])
    connection.close()
    return render_template('ratings.html',emails=l)

def avg_rating(id):
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    res = cursor.execute("SELECT AVG(Rating) FROM Rating WHERE Seller_Email = ?", (id,))
    avg_rating = res.fetchone()[0]
    connection.close()
    if avg_rating is None:
        avg_rating = 'Not Yet Rated'
    return avg_rating




@app.route('/gohome', methods=['GET', 'POST'])
def home():
    session['show_seller'] = False
    session['seller_email'] = False
    session['bid_button_pressed'] = False
    if session['user_type'] == 'bidder':
        return redirect(url_for('bidder_home'))
    else:
        return redirect(url_for('seller_home'))
    #add helpdesk

@app.route('/bid/<int:listing_id>', methods=['GET', 'POST'])
def place_bid(listing_id):
    session['bid_button_pressed'] = True
    return redirect(url_for('select_product', listing_id=listing_id))


@app.route('/verify_listing', methods=['GET', 'POST'])
def verify_listing():
    if request.method == 'POST':
        seller_email = session['email']
        listing_id = request.form['Listing-ID']
        category = request.form['category']
        auction_title = request.form['auction-title']
        product_name = request.form['product-name']
        product_description = request.form['product-description']
        quantity = request.form['quantity']
        reserve_price = request.form['reserve-price']
        max_bids = request.form['max-bids']
        status = 1

        # Connect to the database
        connection = sql.connect('Users.sqlite')
        cursor = connection.cursor()
        query = '''INSERT INTO Auction_Listings(Seller_Email, Listing_ID, Category, Auction_Title, Product_Name, 
                   Product_Description, Quantity, Reserve_Price, Max_bids, Status, Remaining_Bids)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        try:
            result = cursor.execute(query, (seller_email, listing_id, category, auction_title, product_name,
                                            product_description, quantity, reserve_price, max_bids, status, max_bids))
            connection.commit()
            connection.close()


        except:

            return redirect(url_for('create_listing'))

        return render_template('Sellers_Home.html')

@app.route('/choose_listing_type', methods = ['GET', 'POST'])
def choose():
    if request.method == 'GET':
        session['listing_type'] = request.args.get('listing-type')
        return redirect(url_for('view_listing'))
    else:
        return render_template('choose_list.html')

@app.route('/view_listings', methods = ['GET','POST'])
def view_listing():
    if session['listing_type'] == 'active':
        status = 1
    elif session['listing_type'] == 'deactivated':
        status = 0
    else:
        status = 2
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT * FROM Auction_Listings WHERE Seller_Email=? and Status=?'
    result = connection.execute(query, (session['email'],status))
    listings = result.fetchall()
    connection.close()
    return render_template('Product_Listing.html', listings=listings, seller=True)

@app.route('/update/<int:listing_id>', methods=['POST','GET'])
def update(listing_id):
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT category_name FROM Categories'
    result = connection.execute(query)
    categories = result.fetchall()
    cat = []
    for i in categories:
        cat.append(i[0])
    connection.close()


    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT * FROM Auction_Listings WHERE Listing_ID=?'
    session['product_id'] = listing_id
    res = cursor.execute(query, (session['product_id'],))
    product_info = res.fetchone()
    connection.close()
    if request.method == 'POST':
        category = request.form['category']
        auction_title = request.form['auction-title']
        product_name = request.form['product-name']
        product_description = request.form['product-description']
        quantity = request.form['quantity']
        reserve_price = request.form['reserve-price']
        max_bids = request.form['max-bids']
        connection = sql.connect('Users.sqlite')
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE Auction_listings SET Category=?, Auction_title=?, Product_Name=?, Product_Description=?, Quantity=?, Reserve_Price=?, Max_Bids=? WHERE Listing_ID=?",
            (category, auction_title, product_name, product_description, quantity, reserve_price, max_bids, listing_id))
        connection.commit()
        connection.close()
        print('passefd')
        return redirect(url_for('home'))

    return render_template('update_listing.html', product_info=product_info, categories=cat)

@app.route('/cancel/<int:listing_id>', methods=['POST', 'GET'])
def cancel(listing_id):

    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()


    # cannot update sold listings

    cursor.execute("UPDATE Auction_Listings SET Status = ? WHERE Listing_ID = ? AND Status = 1", (0, listing_id))
    connection.commit()
    connection.close()
    return render_template('reasoning.html',listing_id=listing_id)

@app.route('/reasoning/<int:listing_id>', methods=['POST', 'GET'])
def reasoning(listing_id):

    r = request.form['reason']
    print(r)

    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()


    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'UPDATE Auction_Listings SET Reasoning =? WHERE Listing_ID =?'
    cursor.execute(query, (r, listing_id))
    connection.commit()
    connection.close()

    return redirect(url_for('home'))



@app.route('/create_listing', methods=['GET', 'POST'])
def create_listing():
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT category_name FROM Categories'
    result = connection.execute(query)
    categories = result.fetchall()
    cat = []
    for i in categories:
        cat.append(i[0])
    connection.close()
    return render_template('create_listing.html', categories=cat)


@app.route('/goback', methods=['GET', 'POST'])
def goback():
    if session['current_category'] == 'Root':
        return render_template('Bidders_home.html', email = session['email'])

    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = "SELECT C.parent_category FROM Categories C WHERE C.category_name=?"

    if not isinstance(session['current_category'], str):
        session['current_category'] = session['current_category'][0]

    result = cursor.execute(query, (session['current_category'],))
    result_val = result.fetchone()
    session['current_category'] = result_val
    connection.close()

    return redirect(url_for('categorical_hierarchy'))


@app.route('/Product', methods=['GET', 'POST'])
def product():
    return render_template('Product.html')


# session['current_category'] = 'Root'

# difficulty routing to this becuase we dont know if we should reroute to this page or not
# possibly need javascript if this is a big problem


# not right
@app.route('/seller_create', methods=['POST', 'GET'])
def seller_create():
    print("hello")
    return redirect(url_for('create_account',user_type=request.form['user-type']))

@app.route('/create_account/<string:user_type>', methods=['POST','GET'])
def create_account(user_type):
    print(user_type)
    if user_type == 'seller':
        print('test')
        seller = True
    else:
        seller = False

    if request.method == 'POST':
        email = request.form['email']
        print(email)
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        gender = request.form['gender']
        age = request.form['age']
        major = request.form['major']
        zipcode = request.form['zipcode']
        street_name = request.form['street_name']
        street_num = request.form['street_num']
        address_id = generate_address_id()
        password = hl.sha256(password.encode()).hexdigest()


        #every user is a bidder, proceed to populate users and bidders, and adress tables regardless of anything else.

        try:

            connection = sql.connect('Users.sqlite')
            cursor = connection.cursor()
            print('email')
            cursor.execute('INSERT INTO Users (email, password) VALUES (?, ?)', (email, password))
            connection.commit()
            connection.close()

            # update the address
            """"
            connection = sql.connect('Users.sqlite')
            cursor = connection.cursor()
            cursor.execute('INSERT INTO Address (address_ID, zipcode, street_num, street_name) VALUES (?, ?, ?, ?)',
                           (address_id, zipcode, street_num, street_name))
                           
    
            connection.commit()
            connection.close()
            """


            #update bidders
            connection = sql.connect('Users.sqlite')
            cursor = connection.cursor()
            connection.execute(
                'INSERT INTO bidders (email, first_name, last_name, gender, age, home_address_id, major) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (email, first_name, last_name, gender, age, address_id, major))
            connection.commit()
            connection.close()



            if user_type == 'seller':
                routing_num = request.form['bank_routing_num']
                account_num = request.form['bank_account_num']
                balance = request.form['balance']
                connection = sql.connect('Users.sqlite')
                cursor = connection.cursor()

                cursor.execute(
                    'INSERT INTO Sellers (email, bank_routing_number, bank_account_number, balance) VALUES (?, ?, ?, ?)',
                    (email, routing_num, account_num, balance))
                connection.commit()
                connection.close()

        except Exception as e:
            return render_template('create_account.html', seller=seller, message=f'Error: {e}')

    print(seller)
    return render_template('create_account.html', seller=seller)




@app.route('/user_type_request', methods=['GET', 'POST'])
def update_usertype():
    desired_type = request.form['user-type']

    if desired_type == session['user_type']:

        if session['user_type'] == 'bidder':

            return redirect(url_for('bidder_home'))

        elif session['user_type'] == 'seller':

            return redirect(url_for('seller_home'))

        else:#heldesk

            return render_template('successful.html')

        #add else

    elif desired_type == 'seller':

        auth = user_type(session['email'], 'seller')
        if auth != 0:
            #authenticated to switch to a seller
            session['user_type'] = 'seller'
            return redirect(url_for('seller_home'))

        else:

            message2 = 'Unauthorized to be a Seller' #render in message
            redirect(url_for('bidder_home', message2=message2))

    elif desired_type == 'bidder':

        #all seller adn helpdesk are bidders
        session['user_type'] = 'bidder'
        return redirect(url_for('bidder_home'))

    else:

        auth = user_type(session['email'], 'helpdesk')
        if auth != 0:

            session['user_type'] = 'helpdesk'
            return render_template('successful.html')

        else:
            message2 = 'Unauthorized to be an Employee'
            if session['user_type'] == 'seller':
                return redirect(url_for('seller_home', message2=message2))

            else:
                return redirect(url_for('bidder_home', message2=message2))
    return None


@app.route('/Bidders_home', methods=['GET', 'POST'])
def bidder_home():
    message2 = request.args.get('message2')
    if message2 is None:
        message2 = ''
    session['current_category'] = 'Root'
    session['product'] = 0
    if request.method == 'POST':
        session['product'] = request.form['search']
        if session['product'] != 0:
            return redirect(url_for('product_listing'))

    return render_template('Bidders_home.html', results=session['results'], message2=message2, name=session['email'])

@app.route('/Sellers_home', methods=['GET','POST'])
def seller_home():
    message2 = request.args.get('message2')
    if message2 is None:
        message2 = ''
    session['current_category'] = 'Root'
    session['product'] = 0
    if request.method == 'POST':
        session['product'] = request.form['search']
        if session['product'] != 0:
            return redirect(url_for('product_listing'))
    return render_template('Sellers_Home.html', results=session['results'], message2=message2, name=session['email'])

# lists products in a table, has different uses

@app.route('/Search_Results', methods=['GET', 'POST'])
def search_results():
    # inp = request.json.get('searchTerm')
    if request.method == 'GET':
        query = request.args.get('query')
        results = runner(query)
        session['results'] = results
        return jsonify(results)
    if session['user_type'] == 'seller':
        return redirect(url_for('seller_home'))
    return redirect(url_for('bidder_home'))


@app.route('/Product_Listing', methods=['GET', 'POST'])
def product_listing():
    if request.method == 'GET':
        connection = sql.connect('Users.sqlite')
        cursor = connection.cursor()
        query = 'SELECT * FROM Auction_Listings WHERE Product_Name = ? AND Status = 1'
        result = cursor.execute(query, (session['product'],))
        result2 = cursor.fetchall()
        connection.close()

    return render_template('Product_listing.html', listings=result2, seller=False)

#returns a list of bids for a given product

def get_bids(listing_id):

    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT b.Bid_price FROM Bids b WHERE b.Listing_ID=? ORDER BY b.Bid_price DESC '
    res = cursor.execute(query, (listing_id,))
    bids = res.fetchall()
    connection.close()
    for i in bids:
        session['product_bid_listings'].append((i[0]))
    return bids


@app.route('/product/<int:listing_id>', methods=['POST', 'GET'])
def select_product(listing_id):
    message2 = ''
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT * FROM Auction_Listings WHERE Listing_ID=?'
    session['product_id'] = listing_id
    res = cursor.execute(query, (session['product_id'],))
    product_info = res.fetchone()
    connection.close()
    rating = avg_rating(product_info[0])



    session['product_bid_listings'] = []
    message = ''

    bids = get_bids(listing_id)



    if request.method == 'POST':
        # obtain the seller email of the product being bidded on
        """
        connection = sql.connect('Users.sqlite')
        cursor = connection.cursor()
        query = 'SELECT l.seller_email FROM Auction_Listings l WHERE Listing_ID=?'
        res = cursor.execute(query, (listing_id,))
        result = res.fetchone()[0]
        connection.close()
        """
        result = product_info[0]


        # sate for determening whether the submit button for a bid being placed is shown


        #may be wrong for second condition i dont know man
        if session['bid_button_pressed'] and request.form.get('bid-price') is not None:
            seller_email = result
            bid_price = float(request.form.get('bid-price'))
            bidder_email = session['email']

            # verification step, bid needs to be above all previous bids on ths product not done
            v = 1

            #check if the bid is higher than all other bids


            for i in session['product_bid_listings']:
                if bid_price < i+1:
                    v = 0

            #bid_count = len(session['product_bid_listings'])

            #check if seller is bidding on own product
            if seller_email == session['email']:
                v = 0


            #check if a user is placing a bid twice in a row.

            #change for debugging


            connection = sql.connect('Users.sqlite')
            cursor = connection.cursor()
            query = 'SELECT Bidder_Email FROM Bids WHERE Listing_ID=? ORDER BY Bid_price DESC LIMIT 1'
            result = cursor.execute(query, (listing_id, ))
            result = result.fetchone()
            connection.close()
            if result is not None and result[0] == session['email']:
                v = 0




            #check the status of the listing may be redundent if you chose to not show the cancelled listings

            connection = sql.connect('Users.sqlite')
            cursor = connection.cursor()
            query = "SELECT * FROM Auction_Listings WHERE listing_id = ? AND status = 1"
            cursor.execute(query, (listing_id, ))
            result = cursor.fetchone()
            print(product_info[9])
            #result = product_info[9]
            if result is None:
                v = 0
            connection.close()



            if v:


                #create bid information
                connection = sql.connect('Users.sqlite')
                cursor = connection.cursor()
                cursor.execute("""
                        INSERT INTO Bids (Seller_Email, Listing_ID, Bidder_Email, Bid_price)
                        VALUES (?, ?, ?, ?)
                        """, (seller_email, listing_id, bidder_email, bid_price))
                connection.commit()
                connection.close()

                #deincrement remaining bids and check if it is a winning bid, if it is a winning, update transactions, maybe bid status, and end auction lsiting
                connection = sql.connect('Users.sqlite')
                cursor = connection.cursor()
                query = "UPDATE Auction_Listings  SET remaining_bids = remaining_bids - 1 WHERE listing_id=?"
                result = cursor.execute(query, (listing_id, ))
                connection.commit()
                connection.close()


                #check if winning bid

                connection = sql.connect('Users.sqlite')
                cursor = connection.cursor()
                query = "SELECT remaining_bids FROM Auction_Listings WHERE listing_id = ?"
                cursor.execute(query, (listing_id, ))
                result = cursor.fetchone()[0]
                connection.close()


                #if remaining bids equals zero, should immediatly make all other bids invalid
                if result == 0:
                    #event handling for winning bid NOT DONE NEED TO HANDLE TRANSACTIO
                    connection = sql.connect('Users.sqlite')
                    cursor = connection.cursor()
                    query = 'UPDATE Auction_Listings SET status = 2 WHERE listing_id = ?'
                    cursor.execute(query, (listing_id, ))
                    connection.commit()
                    connection.close()
                    #check if above reserve price
                    connection = sql.connect('Users.sqlite')
                    cursor = connection.cursor()
                    query = 'SELECT reserve_price FROM Auction_Listings WHERE Listing_id = ?'
                    cursor.execute(query, (listing_id, ))
                    reserve_price = cursor.fetchone()[0]
                    connection.close()
                    if bid_price > float(reserve_price[1:]):
                    #Complete transaction

                    
                    #---------------------------------------------------------------------------------------------------
                    #existing credit cards:
                        connection = sql.connect('Users.sqlite')
                        cursor = connection.cursor()
                        query = 'SELECT card_type FROM Credit_cards WHERE owner_email=?'
                        result = cursor.execute(query, (session['email'],))
                        card_types = result.fetchall()
                        connection.close()
                        session['product_info'] = product_info
                        return render_template('transaction.html', product_info=product_info, user = session['email'], card_types=card_types, bid_price=bid_price, seller_email=session['show_seller'])

                    else:
                        message2 = "Unable to complete this auction. Your bid did not exceed the reserve price. "

                session['bid_button_pressed'] = False

            else:
                message = 'Could not Place Bid'
                session['bid_button_pressed'] = False

        # test code
            """
            connection = sql.connect('Users.sqlite')
            cursor = connection.cursor()
            query = 'SELECT * FROM Auction_Listings WHERE listing_id = ?'
            cursor.execute(query, (listing_id,))
            result = cursor.fetchall()
            connection.close()
            """

    bids = get_bids(listing_id)
    if session['bid_button_pressed']:
        return render_template('Product.html', product_info=product_info, bids=bids, bid=True, message=message, message2=message2, rating=rating, seller_email=session['show_seller'])
    return render_template('Product.html', product_info=product_info, bids=bids, message=message, message2=message2, rating=rating, seller_email=session['show_seller'])

    # write query to calculate the average rating and show it to the user

    # return redirect(url_for('product', listing_id=listing_id))

#checks if a transaction_id has already been used and finds an available transaction id

def generate_transaction_id():
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT TRANSACTION_ID FROM Transactions'
    cursor.execute(query)
    result = cursor.fetchall()
    connection.close()
    l = []
    for j in result:
        l.append(j[0])
    for i in range(1000000):
        if i not in l:
            return i
    return None

@app.route('/complete_transaction/<int:listing_id>/<float:bid_price>', methods = ['GET', 'POST'])
def transaction(listing_id, bid_price):
    if request.method == 'POST':
        if request.form['card_type'] is None:
            card_num = request.form['credit_card_num']
            card_type = request.form['card_type']
            expiration_month = request.form['expire_month']
            expiration_year = request.form['expire_year']
            security_code = request.form['security_code']
            #insert the credit card info into the credit card database
            connection = sql.connect('Users.sqlite')
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO Credit_Cards (credit_card_num, card_type, expire_month, expire_year, security_code, owner_email) VALUES (?, ?, ?, ?, ?, ?)",
                (card_num, card_type, expiration_month, expiration_year, security_code, session['email']))
            connection.commit()

        connection = sql.connect('Users.sqlite')
        cursor = connection.cursor()
        query = 'INSERT INTO Transactions(Transaction_ID, Seller_Email, Listing_ID, Buyer_Email, Date, Payment) VALUES (?,?,?,?,?,?) '
        date = datetime.date.today().strftime('%d/%m/%Y')
        tid = generate_transaction_id()
        cursor.execute(query, (tid, session['product_info'][0], listing_id, session['email'], date, bid_price))
        # transaction is now complete
        connection.commit()
        connection.close()


        return redirect(url_for('home'))

@app.route('/request')
def bidder_request():
    return render_template('bidder_request.html')


# setup.main()

# when a category is actually selected
def get_subcategories(category):
    if category not in session['category_list']:
        session['category_list'].append(category)
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = "SELECT C.category_name FROM Categories C WHERE C.parent_category=?"
    result = cursor.execute(query, (category,))
    result_list = result.fetchall()
    connection.close()
    normalized=[]
    for j in result_list:
        normalized.append(j[0])
    connection.close()
    session['category_list'] = session['category_list'] + normalized
    subcategories = []
    for i in normalized:
        subcategories += get_subcategories(i)
    return subcategories
    
        


# display the sub categories at the top, and also display
@app.route('/categories', methods=['GET', 'POST'])
def categorical_hierarchy():
    session['category_list'] = []
    if request.method == 'POST':
        session['current_category'] = request.form["selected_category"]

    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = "SELECT C.category_name FROM Categories C WHERE C.parent_category=?"
    if not isinstance(session['current_category'], str):
        session['current_category'] = session['current_category'][0]

    result = cursor.execute(query, (session['current_category'],))
    result_list = result.fetchall()
    connection.close()
    d = {}

    for category in result_list:
        if category not in d:
            d[category] = []
        connection = sql.connect('Users.sqlite')
        cursor = connection.cursor()
        query = "SELECT C.category_name FROM Categories C WHERE C.parent_category=?"
        result = cursor.execute(query, category)
        result_list = result.fetchall()
        d[category] = result_list  # subcategories of each listed category listed in a dictionary
        connection.close()

    listings = []

    if session['current_category'] != 'Root':
        connection = sql.connect('Users.sqlite')
        cursor = connection.cursor()
        get_subcategories(session['current_category'])
        print(session['category_list'])
        for j in session['category_list']:
            result_list = []
            connection = sql.connect('Users.sqlite')
            cursor = connection.cursor()
            query = 'SELECT * FROM Auction_Listings WHERE Category=? AND Status=1'
            result = cursor.execute(query, (j,))
            result_list=result.fetchall()
            connection.close()
            listings.extend(result_list)


    return render_template('Categories.html', categories=d, listings=listings)


@app.route('/update-profile', methods=['POST', 'GET'])
def update_profile():
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    res1 = []
    if session['user_type'] == 'seller':
        connection = sql.connect('Users.sqlite')
        cursor = connection.cursor()
        query = 'Select * FROM Sellers WHERE email=?'
        result = cursor.execute(query,(session['email'],))
        res1 = result.fetchall()
        print(res1)
        connection.close()

    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'Select * FROM Bidders WHERE email=?'
    result = cursor.execute(query, (session['email'],))
    res2 = result.fetchall()
    connection.close()
    profile = res2[0]
    if len(res1) != 0:
        profile = profile + res1[0]

    print(profile)

#test

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        gender = request.form['gender']
        major = request.form['major']

        # Update first name

        connection = sql.connect('Users.sqlite')
        cursor = connection.cursor()
        cursor.execute("UPDATE bidders SET first_name=?, last_name=?, gender=? , major=? WHERE email=?",
                       (first_name, last_name, gender, major, session['email']))

        connection.commit()
        connection.close()
        return redirect(url_for('home'))

    return render_template('Update_profile.html',profile=profile)


def authenticate(email, password):
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT * FROM Users WHERE email=? AND password=?'
    result = cursor.execute(query, (email, password))
    a = result.fetchone() is not None
    connection.close()
    return a


def user_type(email, role):

    if role == 'seller':
        connection = sql.connect('Users.sqlite')
        query1 = "SELECT * FROM Sellers WHERE email=?"
        result1 = connection.execute(query1, (email,))
        seller = result1.fetchone()
        connection.close()
        if seller is not None:
            return 'S'

    elif role == 'bidder':
        connection = sql.connect('Users.sqlite')
        query2 = "SELECT * FROM bidders WHERE email=?"
        result2 = connection.execute(query2, (email,))
        bidder = result2.fetchone()
        connection.close()
        if bidder is not None:
            return 'B'

    elif role == 'helpdesk':
        connection = sql.connect('Users.sqlite')
        query3 = "SELECT * FROM Helpdesk WHERE email=?"
        result3 = connection.execute(query3, (email,))
        helpdesk = result3.fetchone()
        connection.close()
        if helpdesk is not None:
            return 'H'
    return 0

@app.route('/logout', methods=['GET','POST'])
def logout():
  session.clear()
  return redirect(url_for('login'))

# @app.route('/')
@app.route('/', methods=['GET', 'POST'])
def login():
    session['show_seller'] = False
    session['product_bid_listings'] = []
    session['bid_button_pressed'] = False
    session['results'] = []
    message = None

    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('username')
        password = hl.sha256(request.form['password'].encode()).hexdigest()
        auth = authenticate(email, password)


        if auth:
            session['email'] = email
            usertype = user_type(email, role)


            if usertype == 'S':
                session['user_type'] = 'aseller'
                return redirect(url_for('seller_home'))

            elif usertype == 'B':
                session['user_type'] = 'bidder'
                return redirect(url_for('bidder_home'))

            elif usertype == 'H':
                session['user_type'] = 'helpdesk'
                return redirect(url_for('bidder_home'))

        else:

            message = "Incorrect Credentials"

    return render_template('login.html', message=message)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
