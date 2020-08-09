import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    cors = CORS(app, resources={r"/api/*": {"origin": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    @app.route("/categories", methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        categories_listed = list(map(Category.format, categories))
        return jsonify({
            "success": True,
            "categories": categories_listed
        })

    @app.route('/questions', methods=['GET'])
    def retrieve_questions():
        selected_questions = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selected_questions)
        categories = Category.query.all()
        categories_listed = list(map(Category.format, categories))

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'questions': current_questions,
            'total_questions': len(categories),
            'categories': categories_listed,
            'current_category': None,
            'success': True
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).first()
            question.delete()

            return jsonify({
                'deleted': question_id,
                'success': True
            })

        except:
            abort(422)

    @app.route("/questions", methods=['POST'])
    def post_question():
        request_body = request.get_json(force=True)

        question = request_body.get('question', None)
        answer = request_body.get('answer', None)
        category = request_body.get('category', None)
        difficulty = request_body.get('difficulty', None)
        try:

            new_question = Question(question=question,
                                    answer=answer,
                                    category=category,
                                    difficulty=difficulty)
            new_question.insert()

            return jsonify({
                'success': True,
                'created': new_question.id,
                'total questions': len(Question.query.all())
            })

        except Exception:
            abort(422)

    @app.route("/searchQuestions", methods=['POST'])
    def search_questions():
        if request.data:
            current_page = int(request.args.get('page'))
            data = json.loads(request.data.decode('utf-8'))
            if 'searchTerm' in data:
                questions_query = Question.query.filter(
                    Question.question.like(
                        '%' +
                        data['searchTerm'] +
                        '%')).paginate(
                    current_page,
                    QUESTIONS_PER_PAGE,
                    False)
                questions = list(map(Question.format, questions_query.items))
                if len(questions) > 0:
                    return jsonify({
                        "success": True,
                        "all questions": questions,
                        "total questions": questions_query.total
                    })
            abort(404)
        abort(422)

    @app.route("/categories/<int:category_id>/questions")
    def get_question_by_category(category_id):
        page = int(request.args.get('page'))
        questions_query = Question.query.filter_by(
            category=category_id).paginate(
            page, QUESTIONS_PER_PAGE, False)
        questions = list(map(Question.format, questions_query.items))
        if len(questions) > 0:
            return jsonify({
                "success": True,
                "all questions": questions,
                "total questions": questions_query.total
            })
        abort(404)

    @app.route("/quizzes", methods=['POST'])
    def get_question_for_quiz():
        data = json.loads(request.data.decode('utf-8'))
        if (('quiz_category' in data
             and 'id' in data['quiz_category'])
                and 'previous_questions' in data):
            questions_query = Question.query.filter_by(
                category=data['quiz_category']['id']
            ).filter(
                Question.id.notin_(data["previous_questions"])
            ).all()
            length_of_available_question = len(questions_query)
            if length_of_available_question > 0:
                return jsonify({
                    "success": True,
                    "question": Question.format(
                        questions_query[random.randrange(
                            0,
                            length_of_available_question
                        )]
                    )
                })
            else:
                return jsonify({
                    "success": True,
                    "all questions": "no question found"
                })
        abort(404)

    '''
    @TODO: 
    Create error handlers for all expected errors 
    including 404 and 422. 
    '''

    @app.errorhandler(422)
    def unprocessable(error):
      return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
      }), 422

    @app.errorhandler(404)
    def not_found(error):
      return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
      }), 404

    @app.errorhandler(422)
    def not_found(error):
      return jsonify({
        "success": False,
        "error": 422,
        "message": "Unprocessable Entity response"
      }), 422

    return app
