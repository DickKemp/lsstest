import os
from flask import Flask, session, request, url_for, redirect
from flask import current_app as app

from google_auth_oauthlib.flow import Flow
import google.oauth2.credentials
from googleapiclient.discovery import build

import json
import requests

CLIENT_SECRET_FILE = 'client_secret_photos_lsstest.json'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
CLIENT_SECRET=None

@app.route('/doauth')
def doauth():
    print('in /doauth')

    client_config_str = os.getenv('GOOGLE_CLIENT_SECRETS', None)
    if client_config_str:
        client_config = json.loads(client_config_str)
        flow = Flow.from_client_config(client_config=client_config, scopes=SCOPES)
    else:
        # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
        flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = url_for('auth', _scheme='https', _external=True)
    if 'localhost' in flow.redirect_uri:
        flow.redirect_uri = url_for('auth', _scheme='http', _external=True)
    
    authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    return redirect(authorization_url)

@app.route("/logged-in")
def logged_in():

    credentials = get_credentials()
    if credentials:
        return "<H2>Logged in</H2>"
    else:
        return "<H2>NOT Logged in</H2>"


@app.route('/auth')
def auth():
    print('in /auth')
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    client_config_str = os.getenv('GOOGLE_CLIENT_SECRETS', None)
    if client_config_str:
        client_config = json.loads(client_config_str)
        flow = Flow.from_client_config(client_config=client_config, scopes=SCOPES, state=state)
    else:
        flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes= SCOPES, state=state)
    
    flow.redirect_uri = url_for('auth', _scheme='https', _external=True)
    if 'localhost' in flow.redirect_uri:
        flow.redirect_uri = url_for('auth', _scheme='http', _external=True)

    url = request.url
    if 'localhost' not in flow.redirect_uri:
        if request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)

    authorization_response = url
    flow.fetch_token(authorization_response=authorization_response)

    # Store the credentials in the session.
    # ACTION ITEM for developers:
    #     Store user's access and refresh tokens in your data store if
    #     incorporating this code into your real app.
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}
    # return redirect(url_for('test_flow'))
    return redirect(url_for('logged_in'))

@app.route('/logout')
@app.route('/revoke')
def revoke():
    if 'credentials' not in session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials( **session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
        params={'token': credentials.token},
        headers = {'content-type': 'application/x-www-form-urlencoded'})
    
    if 'credentials' in session:
        del session['credentials']
    if 'state' in session:
        del session['state']

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return('Credentials successfully revoked.')
    else:
        return('An error occurred.')

def get_credentials():
    if 'credentials' in session:
        return google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        print('credentials not found in session')
        return None
