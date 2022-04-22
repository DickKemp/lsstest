import os
from flask import Flask, jsonify, session, request, url_for, redirect
from flask import current_app as app

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

import photos_api
from .auth import get_credentials

@app.route("/photos/albums")
def get_albums():

    credentials = get_credentials()
    if not credentials:
        return redirect(url_for('doauth'))

    api = photos_api.PhotosApi()
    result_list = api.get_albums(credentials)
    
    result = dict()
    result['album_list'] = result_list
    return result

@app.route("/photos/<photo_id>")
def get_photo(photo_id):

    credentials = get_credentials()
    if not credentials:
        #return redirect('/doauth')
        return redirect(url_for('doauth'))
    api = photos_api.PhotosApi()
    resp = api.get_photo(photo_id, credentials)
    html = ""
    url = resp['baseUrl'] + '=w200-h200'
    img_html = f'<img src={url}></img><br>'
    if 'image' in resp['mimeType']:
        html = f"""
                <img width="320" height="240" src="{resp['baseUrl']}">
                    """
    else:
        html = f"""
                <video width="320" height="240" controls>
                <source src="{resp['baseUrl']}" type="{resp['mimeType']}">
                </video>    
                """
    return html

@app.route("/photos/albums/<album_id>")
def get_albums_list(album_id):

    credentials = get_credentials()
    if not credentials:
        #return redirect('/doauth')
        return redirect(url_for('doauth'))
    next_page = None
    first_page = True
    api = photos_api.PhotosApi()
    mi_list = []

    while first_page or (next_page is not None):
        resp, next_page = api.get_album_items(album_id, credentials, next_page)
        mi_list = resp +  mi_list
        first_page = False

    return { "items" : mi_list }

