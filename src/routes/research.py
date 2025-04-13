from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from bson import ObjectId
from config.database import research_data
import logging

research_bp = Blueprint('research', __name__)
logger = logging.getLogger(__name__)

@research_bp.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        
        # Extract parameters from request
        research_topic = data.get('research_topic')
        related_topic = data.get('related_topic', '')
        field_of_study = data.get('field_of_study', '-- Not Specified --')
        type_of_publication = data.get('type_of_publication', '-- Not Specified --')
        date_range = data.get('date_range', [2000, datetime.now().year])
        keywords = data.get('keywords', '')
        citation_format = data.get('citation_format', 'APA')
        open_access_site = data.get('open_access_site', '-- Not Specified --')

        if not research_topic:
            return jsonify({
                'error': 'Research topic is required',
                'status': 'error'
            }), 400

        # Get the app context
        app = current_app._get_current_object()
        
        from search_function import search_articles
        from chatgpt_functions import get_chatgpt_response
        from document_functions import create_research_summary

        search_results = search_articles(research_topic, date_range, open_access_site)
        logger.info(f"Search results count: {len(search_results)}")
        
        response = get_chatgpt_response(
            research_topic, 
            related_topic, 
            field_of_study, 
            type_of_publication, 
            date_range, 
            keywords, 
            citation_format,
            open_access_site,
        )

        if not response or not response.get('response'):
            return jsonify({
                'error': 'Unable to generate research report',
                'status': 'error',
                'suggestions': {
                    'modify_search': [
                        'Broaden your keywords',
                        'Extend the date range',
                        'Remove specific filters'
                    ],
                    'alternative_actions': [
                        'Try a different database',
                        'Rephrase your research topic',
                        'Check spelling'
                    ]
                }
            }), 400

        summary = create_research_summary(response)

        return jsonify({
            'status': 'success',
            'research_summary': summary,
            'search_results_count': len(search_results)
        })

    except Exception as e:
        logger.error(f"Unexpected error in report generation: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'suggestions': {
                'troubleshooting': [
                    'Check your internet connection',
                    'Verify API keys are correctly set'
                ],
                'alternative_actions': [
                    'Try a different research topic',
                    'Restart the application'
                ]
            }
        }), 500

@research_bp.route('/save_research', methods=['POST'])
@jwt_required()
def save_research():
    try:
        current_user_id = get_jwt_identity()
        if isinstance(current_user_id, str):
            current_user_id = ObjectId(current_user_id)
            
        data = request.json
        
        required_fields = ['title', 'research_topic', 'summary', 'citations']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required_fields': required_fields,
                'status': 'error'
            }), 422
        
        research_doc = {
            'user_id': current_user_id,
            'created_at': datetime.utcnow(),
            'title': data['title'],
            'research_topic': data['research_topic'],
            'summary': data['summary'],
            'citations': data['citations'],
            'search_params': data.get('search_params', {})
        }
        
        result = research_data.insert_one(research_doc)
        
        return jsonify({
            'message': 'Research saved successfully',
            'research_id': str(result.inserted_id),
            'status': 'success'
        }), 201
        
    except Exception as e:
        logger.error(f"Error saving research: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@research_bp.route('/saved_researches', methods=['GET'])
@jwt_required()
def get_saved_researches():
    try:
        current_user_id = get_jwt_identity()
        if isinstance(current_user_id, str):
            current_user_id = ObjectId(current_user_id)
            
        researches = list(research_data.find({'user_id': current_user_id}))
        
        # Convert all ObjectId fields to strings for JSON serialization
        for research in researches:
            research['_id'] = str(research['_id'])
            research['user_id'] = str(research['user_id'])
            
            # Convert created_at to ISO format string
            research['created_at'] = research['created_at'].isoformat()
        
        return jsonify({
            'researches': researches,
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving researches: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@research_bp.route('/research/<id>', methods=['GET'])
@jwt_required()
def get_research(id):
    try:
        current_user_id = get_jwt_identity()
        if isinstance(current_user_id, str):
            current_user_id = ObjectId(current_user_id)
            
        research = research_data.find_one({
            '_id': ObjectId(id),
            'user_id': current_user_id
        })
        
        if not research:
            return jsonify({
                'error': 'Research not found',
                'status': 'error'
            }), 404
            
        # Convert all MongoDB-specific fields to JSON-serializable formats
        research['_id'] = str(research['_id'])
        research['user_id'] = str(research['user_id'])
        research['created_at'] = research['created_at'].isoformat()
        
        return jsonify({
            'research': research,
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving research: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@research_bp.route('/<research_id>', methods=['DELETE'])
@jwt_required()
def delete_research(research_id):
    try:
        current_user_id = get_jwt_identity()
        if isinstance(current_user_id, str):
            current_user_id = ObjectId(current_user_id)
            
        # Convert research_id to ObjectId
        research_id = ObjectId(research_id)
        
        # Delete the research document
        result = research_data.delete_one({
            '_id': research_id,
            'user_id': current_user_id
        })
        
        if result.deleted_count == 0:
            return jsonify({
                'error': 'Research not found or unauthorized to delete',
                'status': 'error'
            }), 404
            
        return jsonify({
            'message': 'Research deleted successfully',
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting research: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
