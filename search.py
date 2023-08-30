import sqlite3 as sql
from difflib import SequenceMatcher
from flask import Flask, render_template, request, session, redirect, url_for

# This entire file is meant to find the edit distance betweeen what is being typed
#In the search box and the actual products themselves. Whichever 10 products have
#The shortest edit distance will be displayed on the screen

test_str = 'el'

def sql_eval():
    connection = sql.connect('Users.sqlite')
    cursor = connection.cursor()
    query = 'SELECT p.Product_Name FROM Auction_Listings p WHERE p.Status=1'
    res = cursor.execute(query)
    result = res.fetchall()
    connection.close()
    lis = []
    for i in result:
        lis.append(i[0])
    return list(set(lis))


def distance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def runner(inp):
    products = sql_eval()
    d = {}
    for i in products:
        d[i] = similar(inp, i)
    smallest_keys = sorted(d, key=lambda k: d[k])
    return smallest_keys




