import os
from flask import Flask, jsonify, session, request, url_for, redirect
from google_auth_oauthlib.flow import Flow
import google.oauth2.credentials
from googleapiclient.discovery import build
import json
import requests

app = Flask(__name__, static_folder='static')
app.secret_key = 'asdfk;;alksjf;skjf;alskjdf;sjdxxxk'

API_NAME = 'photoslibrary'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = 'client_secret_photos_lsstest.json'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
CLIENT_SECRET=None

@app.route("/heartbeat")
def heartbeat():
    return jsonify({"status": "healthy"})

@app.route("/session1")
def session1():
    html = "<h3>session keys & values</h3>"
    x = session
    for key in session:
        print(f"session key: {key} - value: {str(session[key])}")
        html = html + f"session key: {key} - value: {str(session[key])} <br>"
    return html

@app.route("/session2")
def sessio21():
    html = "<h3>session2</h3>"
    if 'rich' not in session:
        session['rich'] = "kempinski"
        html = html + f"setting session['rich']: to kempinski"
    else:
        html = html + f"got session['rich']: {session['rich']}<br>"
    return html


@app.route("/test")
def test_flow():
    print('starting in /test')

    if 'credentials' not in session:
        print('credentials not found in session')
        return redirect('doauth')

    html = '<h3>albums</h3>'
    print('in /test - got credentials')
    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    service = build(API_NAME, API_VERSION, credentials=credentials)
    myAblums = service.albums().list().execute()
    myAblums_list = myAblums.get('albums')
    for alb in myAblums_list:
        html = html + f"<h3>{alb['title']}</h3>"
    img_html='<h3>photo</h3>'
    media_items = service.mediaItems().search(body={'filters': {'dateFilter': {'dates':[{'year':2020, 'month':12, 'day':25}]}}}).execute()['mediaItems']
    for mi in media_items:
        image_url = mi['baseUrl'] + '=w100-h100'
        img_html = img_html + f'<img src={image_url}></img><br>'
        
    return img_html
    # return f'<p>{media_items}</p>'
    # return html

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return app.send_static_file("index.html")

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
    return redirect(url_for('test_flow'))

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

if __name__ == '__main__':
  # When running locally, disable OAuthlib's HTTPs verification.
  # ACTION ITEM for developers:
  #     When running in production *do not* leave this option enabled.
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run('localhost', 8080, debug=True)
