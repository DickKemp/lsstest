import os
from flask import Flask, jsonify, session, request, url_for, redirect
from flask import current_app as app

@app.before_request
def bofore_request():
    print("before request")
    print_request()

@app.route("/commands")
def get_commands():

    print("/commands")
    print_request()

    result = dict()
    result['command_list'] = ['cmd1', 'cmd2', 'cmd3']
    return result

def print_request():
    print(f"request url: {request.url}")
    print(f"request method: {request.method}")
    for (h,v) in request.headers:
        print(f"request header: {h} = {v}")
