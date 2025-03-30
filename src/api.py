from flask import Flask, request, jsonify
from datetime import datetime
from chatgpt_functions import get_chatgpt_response
from document_functions import create_word_doc_from_json
from search_function import search_articles
import json
import os
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the absolute path to the assets directory
current_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(os.path.dirname(current_dir), 'assets')
json_path = os.path.join(assets_dir, 'languages.json')

@app.route('/generate_report', methods=['POST'])
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

        with app.app_context():
            # Search for articles
            search_results = search_articles(research_topic, date_range, open_access_site)
            logger.info(f"Search results count: {len(search_results)}")
            
            # Save search results to JSON file
            try:
                json_dir = os.path.join(os.path.dirname(__file__), '..', 'search_results')
                os.makedirs(json_dir, exist_ok=True)
                
                safe_topic = ''.join(c if c.isalnum() or c in [' ', '_'] else '_' for c in research_topic)
                safe_topic = safe_topic[:50]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                json_filename = os.path.join(json_dir, f"search_results_{safe_topic}_{timestamp}.json")
                
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(search_results, f, ensure_ascii=False, indent=4)
                
                logger.info(f"Saved search results to {json_filename}")
            except Exception as e:
                logger.error(f"Error saving search results to JSON: {e}")

            # Generate response
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

            # Create Word doc
            doc_path = create_word_doc_from_json(response)

            return jsonify({
                'status': 'success',
                'research_summary': response['response'],
                'document_path': doc_path,
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

if __name__ == '__main__':
    app.run(debug=True)
