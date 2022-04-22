import os
from flask import Flask

def create_app(test_config=None):

    app = Flask(__name__, static_folder='static')
    app.secret_key = 'asdfk;;alksjf;skjf;alskjdf;sjdxxxk'
    # app.config["TEST_ENV_VARIABLE"] = os.environ['TEST_ENV_VARIABLE']
    # app.register_blueprint(home_api, url_prefix='/api')
    with app.app_context():
        import routes
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def catch_all(path):
            return app.send_static_file("index.html")

    return app

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=8080, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    
    # only When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    app = create_app()
    app.run(host='localhost', port=port)

