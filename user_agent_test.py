
# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
from flask import Flask, request
 
# Flask constructor takes the name of 
# current module (__name__) as argument.
app = Flask(__name__)
 
# The route() function of the Flask class is a decorator, 
# which tells the application which URL should call 
# the associated function.
@app.route('/')
# ‘/’ URL is bound with hello_world() function.
def hello_world():
    ip_addr = request.remote_addr
    agent = request.user_agent
    return ip_addr + agent.string
 
# main driver function
if __name__ == '__main__':
 
    # run() method of Flask class runs the application 
    # on the local development server.
    app.run(host = '192.168.0.100', port = 5000, debug=False)
