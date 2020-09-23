import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db_roll_back, db_session_close
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

## ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route("/drinks")
def query_drinks():
    drinks = Drink.query.all()
    list_drinks = [drink.short() for drink in drinks]
    return jsonify({
        'success':True,
        'drinks':list_drinks
    })

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks-detail")
@requires_auth(permission="get:drinks-detail")
def query_drinks_detail(payload):
    drinks = Drink.query.all()
    list_drinks = [drink.long() for drink in drinks]
    return jsonify({
        'success':True,
        'drinks':list_drinks
    })


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks", methods=['Post'])
@requires_auth(permission='post:drinks')
def insert_drink(payload):
    req = request.get_json()
    if len(req['recipe']) == 0 or req['recipe'] == None:
        abort(400)
    
    title = req['title']
    recipe = req['recipe']
      
    if type(recipe)  is not list:
        recipe = list(recipe)
    recipe = str(recipe).replace("'", '"')
      
    success = True
    result = []
    try:
        drink_insert = Drink(title= title, recipe= recipe)
        drink_insert.insert()
        result.append(drink_insert.long())
    except Exception as e:
        print(str(e))
        success = False
        db_roll_back()
        abort(400)
    
    finally:
        db_session_close()
    
    return jsonify({'success':success,'drinks': result})

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:drink_id>", methods=['PATCH'])
@requires_auth("patch:drinks")
def drink_update(payload, drink_id):
    req = request.get_json()
    drink = Drink.query.get(drink_id)
    if not drink:
        abort(404)
    
    
    success = True
    result = []
    try:
    
        updated_title = req.get('title')
        updated_recipe = req.get('recipe')
    
        if updated_title:
            drink.title = req['title']         
        if updated_recipe:
            drink.recipe = req['recipe']
               
        drink.update()
        result = [drink.long()]    
    except Exception as e:
        print(str(e))
        success = False
        db_roll_back()
        abort(400)
    
    finally:
        db_session_close()
    
    return jsonify({'success':success,'drinks': result})

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:drink_id>", methods=['DELETE'])
@requires_auth("delete:drinks")
def del_drinks(payload, drink_id):
    req = request.get_json()
    drink_del = Drink.query.get(drink_id)
    if not drink_del:
        abort(404)
    success = True
    try:
        drink_del.delete()
    except Exception as e:
        print(str(e))
        success = False
        db_roll_back()
        abort(400)
    
    finally:
        db_session_close()
    
    return jsonify({ 'success':success, 'delete': drink_id})


## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
'''
@TODO implement error handler for 404
    error handler should conform to general task above 
'''
@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above 
'''
@app.errorhandler(AuthError)
def auth_fail(error):
    status_code = error.status_code
    error_msg = error.error
    return jsonify({
        "success":False,
        "error":status_code,
        "message": error_msg['authentification fails'],
    }), status_code

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    "success": False, 
                    "error": 400,
                    "message": "Bad request"
                    }), 400