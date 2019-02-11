import os, argparse
from dotenv import load_dotenv

# Things in the Class object are config options we will likely never want to change from the database.
class Config(object):

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASEDIR, '.env'))

    # We aren't storing this in the database because it wouldn't be a very good secret then
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-should-set-a-secret-key'

    # This isn't in the database because it doesn't _really_ matter.
    PREFERRED_URL_SCHEME = 'https'

    # This isn't in the database because this is where we find the database.
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'sqlite:///' + os.path.join(BASEDIR, 'metadata.db')

    # This isn't in the database because we'll never want to change it
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# run as standalone to populate the config items into the database using environment or default values
def populate_defaults(verbose=False):
                    # NAME,             TYPE, DEFAULT
    defaultConfig = [("LOGIN_REQUIRED","bool","False"),
                 ("REGISTER_ALLOWED","bool","False"),
                 ("ELASTICSEARCH_URL","string","http://localhost:9200"),
                 ("MAIL_SERVER","string","localhost"),
                 ("MAIL_PORT","int","25"),
                 ("MAIL_USE_TLS","bool","False"),
                 ("MAIL_USERNAME","string",""),
                 ("MAIL_PASSWORD","string",""),
                 ("MAIL_FROM","string","")
                ]
    
    from app import create_app, db
    from app.models import ConfigItem
    app = create_app(load_config=False)
    with app.app_context():
        for item in defaultConfig:
            conf = ConfigItem.query.filter_by(name=item[0]).first()
            if conf:
                conf.type = item[1]
                conf.value = os.environ.get(item[0]) or item[2]
                if verbose:
                    print("[+] Item named %s already existed. Setting type to '%s' and value to '%s'" % (item[0], item[1], conf.value))
            else:
                if verbose:
                    print("[+] Adding config item named '%s', of type '%s', with value '%s'." % (item[0], item[1], item[2]))
                conf = ConfigItem(name=item[0], type=item[1], value=os.environ.get(item[0]) or item[2])
            db.session.add(conf)
        print("[+] Committing config changes to database")
        db.session.commit()

def main():
    parser_desc = '''
    Utility for initially populating the database from the environment. Flask will automatically try to populate the database if no config items are found.
    Only run this if you want to reset the config settings to default or to environment variables.
    '''
    parser_epil = "Be sure that you're running this from within the virtual environment for the server."
    parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    args = parser.parse_args()
    populate_defaults(args.verbose)

if __name__ == "__main__":
    main()