from flask import Flask
from flask import Flask, render_template, request
import sqlite3 as sql
import pandas as pd
import hashlib as hl

app = Flask(__name__)

def secure(filename):
    df = pd.read_csv(filename)
    for index, row in df.iterrows():
        hashed_password = hl.sha256(row['password'].encode()).hexdigest()
        df.at[index, 'password'] = hashed_password
    df.to_csv('secure2.csv', index=False)
    return df

def main():
    #email_files=['Bids.csv','Bidders.csv','Helpdesk.csv','Sellers.csv','Local_Vendors.csv','Ratings.csv','Requests.csv','Credit_Cards.csv','Auction_Listings.csv','Transactions']
    print("used")
    secure('Users2.csv')
    """
    for i in email_files:
        df=pd.read_csv(i)
        email_columns=[]
        for j in df.columns():
            if ('email' in j) or ('Email' in j):
                email_columns.append(i)
        secure_users(df,email_columns)
    """

    return 0





if __name__ == '__main__':
    main()
