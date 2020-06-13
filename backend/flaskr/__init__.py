import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)


  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={r"/api/*": {"origins": "*"}})
  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
      response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
      return response
  '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''
  # can I remove , methods=["GET"] as the GET methods already set by default?
  @app.route('/categories', methods=['GET'])
  def get_categories():
      page = request.args.get('page', 1, type=int)
      start = (page -1) * 10
      end   = start + 10
      categories = Category.query.all()
      formatted_categories = [category.format() for category in categories]
      return jsonify({
          'success': True,
          'categories': formatted_categories[start:end],
          'total_categories' : len(formatted_categories)
      })

  '''
  @TODO:
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
  @app.route('/questions')
  def get_questions():
      page = request.args.get('page', 1, type=int)
      start = (page-1) * 10
      end = start + 10
      questions = Question.query.all()
      formatted_questions = [question.format() for question in questions]

      categories = Category.query.all()
      formatted_categories = [category.format() for category in categories]

      return jsonify({
          'success': True,
          'questions': formatted_questions[start:end],
          'total_questions': len(formatted_questions),
          'categories': formatted_categories,
          'current_category': None
      })
  '''
  @TODO:
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
      body = request.get_json()

      try:
          question = Question.query.firlter(Question.id == question_id).one_or_none()
          if question is None:
              abort(404)
          question.delete()
          selection = Question.query.order_by(Question.id).all()
          current_questions = paginate_questions(request, selection)

          return jsonify({
              'success': True,
              'deleted': question_id,
              'questions': current_questions,
              'total_questions': len(Question.query.all())
          })
      except:
         abort(422)
  '''
  @TODO:
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''
  @app.route('/questions/<int:book_id>', methods=['POST'])
  def create_question():
      body = request.get_json()

      new_question   = body.get('question', None)
      new_answer     = body.get('answer', None)
      new_difficulty = body.get('difficulty', None)
      new_category   = body.get('category', None)

      try:
          question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
          question.insert()

          selection = Question.query.order_by(Question.id).all()
          current_questions = paginate_questions(request, selection)

          return jsonify({
              'success': True,
              'created': question_id,
              'questions': current_questions,
              'total_questions': len(Question.query.all())
          })
      except:
          abort(422)

  '''
  @TODO:
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_question():
      body = request.get_json()
      search_term = body.get('searchTerm', None)
      print(search_term)
      search = "%{}%".format(search_term)
      questions = Question.query.filter(
          Question.question.ilike(search)).all()

      if(questions is None):
          abort(404)
      formatted_questions = [question.format() for question in questions]

      return jsonify({
          'success': True,
          'questions': formatted_questions,
          'total_questions': len(formatted_questions)
      })
  '''
  @TODO:
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_questions_by_category(category_id):
      try:
          questions = Question.query.filter(
              Question.category == category_id).all()

          if(questions is None):
              abort(404)

          formatted_questions = [question.format() for question in questions]

          return jsonify({
              'success': True,
              'questions': formatted_questions,
              'total_questions': len(formatted_questions)
          })

        except:
             abort(422)

  '''
  @TODO:
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''
  @app.route('/quizzes', methods=['POST'])
  def quiz():
         body = request.get_json()
         quiz_category = body.get('quiz_category', None)
         previous_questions = body.get('previous_questions', None)

         questions = Question.query.filter(~Question.id.in_(previous_questions)).all() \
             if quiz_category['id'] == 0 \
             else Question.query.filter(
             ~Question.id.in_(previous_questions),
             Question.category == quiz_category['id']).all()
         question = None
         if(questions):
             question = random.choice(questions).format()
         return jsonify({
             'success': True,
             'question': question
         })

  '''
  @TODO:
  Create error handlers for all expected errors
  including 404 and 422.
  '''
  @app.errorhandler(404)
      def not_found():
          return jsonify({
              'success': False,
              'error': 404,
              'message': 'resource not found'
          })

  @app.errorhandler(422)
      def not_found():
          return jsonify({
              'success': False,
              'error': 422,
              'message': 'unprocessable'
          })

  return app
