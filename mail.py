from flask import Flask
from flask_mail import Mail, Message
from dotenv import dotenv_values



config = dotenv_values("mail.env")
print(config)

app = Flask(__name__)
app.config['MAIL_SERVER']=config['MAIL_SERVER']
app.config['MAIL_PORT']=int(config['MAIL_PORT'])
app.config['MAIL_USERNAME']=config['MAIL_USERNAME']
app.config['MAIL_PASSWORD']=config['MAIL_PASSWORD']
app.config['MAIL_USE_TLS']=True
app.config['SECRET_KEY']=config['SECRET_KEY']



mail = Mail(app)

@app.route("/")
def index():
    return "Mail sent"

if __name__ == "__main__":
	app.run(debug=True)