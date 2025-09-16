# Complete app.py for Misinformation Detection API
# Copy this entire code into your app.py file

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import logging
import traceback
from dotenv import load_dotenv

# Import your custom modules (create these files first as per roadmap)
try:
    from utils.sources import check_source_credibility
    from utils.web_scraper import WebScraper
    from models.text_analyzer import TextAnalyzer
    from models.video_processor import VideoProcessor  
    from models.image_processor import ImageProcessor
except ImportError as e:
    print(f"Warning: Could not import modules - {e}")
    print("Make sure you've created all the required files as per the roadmap")

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for frontend integration

# Configure logging for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize processors (with error handling for missing modules)
web_scraper = None
text_analyzer = None
video_processor = None
image_processor = None

try:
    web_scraper = WebScraper()
    text_analyzer = TextAnalyzer()
    video_processor = VideoProcessor(model_size="base")  # Change to "tiny" for faster testing
    image_processor = ImageProcessor()
    logger.info("All processors initialized successfully")
except Exception as e:
    logger.error(f"Error initializing processors: {e}")
    logger.error("Some endpoints may not work until you create all required files")

# Supported file formats
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'gif'}

# Utility Functions
def allowed_video_file(filename):
    """Check if uploaded file is a supported video format"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_image_file(filename):
    """Check if uploaded file is a supported image format"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def generate_recommendations(credibility_score, source_credibility=None):
    """Generate user recommendations based on credibility analysis"""
    recommendations = []
    
    if credibility_score >= 7:
        recommendations = [
            "✅ Content appears reliable based on our analysis",
            "📝 Still recommended to verify with multiple sources",
            "🔄 Check for recent updates or corrections",
            "🔍 Look for primary sources when possible"
        ]
    elif credibility_score >= 4:
        recommendations = [
            "⚠️ Exercise caution - verify claims independently", 
            "🔍 Look for corroboration from multiple reliable sources",
            "👤 Check the author's credentials and expertise",
            "📋 Look for primary sources or official statements",
            "🕐 Check publication date for relevance"
        ]
    else:
        recommendations = [
            "🚨 High caution advised - likely unreliable content",
            "❌ Do not share without thorough verification",
            "📚 Consult multiple authoritative sources",
            "⚠️ Be aware of potential misinformation",
            "🔍 Fact-check with reputable sources"
        ]
    
    # Add source-specific recommendations
    if source_credibility:
        if source_credibility['credibility'] == 'unknown':
            recommendations.append("❓ Source not recognized - research the publisher's credibility")
        elif source_credibility['credibility'] == 'unreliable':
            recommendations.append("⛔ Known problematic source - seek alternative sources")
        elif source_credibility['credibility'] == 'reliable':
            recommendations.append("✅ Source is generally considered reliable")
    
    return recommendations

def handle_error(error, error_type="Processing"):
    """Standardized error handling"""
    error_id = f"{error_type}_{hash(str(error)) % 10000}"
    logger.error(f"Error {error_id}: {str(error)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return jsonify({
        'error': f'{error_type} error occurred',
        'error_id': error_id,
        'message': str(error) if app.debug else 'Internal server error'
    }), 500

# API Endpoints

@app.route('/', methods=['GET'])
def home():
    """Root endpoint with API information"""
    return jsonify({
        "message": "Misinformation Detection API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/analyze/text": "Analyze text content (POST)",
            "/analyze/url": "Analyze webpage URL (POST)", 
            "/analyze/video": "Analyze video transcript (POST)",
            "/analyze/image": "Analyze image text (POST)"
        },
        "status": "running"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    processor_status = {
        'text_analyzer': text_analyzer is not None,
        'web_scraper': web_scraper is not None,
        'video_processor': video_processor is not None,
        'image_processor': image_processor is not None
    }
    
    return jsonify({
        "status": "healthy",
        "message": "Misinformation Detection API is running",
        "version": "1.0.0",
        "processors": processor_status,
        "upload_folder": app.config['UPLOAD_FOLDER'],
        "max_file_size": f"{app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB"
    })

@app.route('/analyze/text', methods=['POST'])
def analyze_text():
    """Analyze plain text content for misinformation indicators"""
    try:
        if not text_analyzer:
            return jsonify({'error': 'Text analyzer not initialized. Check server logs.'}), 500
        
        # Get JSON data from request
        data = request.get_json()
        
        # Validate input
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing required field: text',
                'example': {'text': 'Your content to analyze here'}
            }), 400
        
        text_content = data['text'].strip()
        if not text_content:
            return jsonify({'error': 'Text content cannot be empty'}), 400
            
        if len(text_content) < 10:
            return jsonify({'error': 'Text must be at least 10 characters long'}), 400
        
        if len(text_content) > 10000:  # Limit text length
            return jsonify({'error': 'Text too long. Maximum 10,000 characters allowed.'}), 400
        
        logger.info(f"Analyzing text content: {len(text_content)} characters")
        
        # Analyze the text
        analysis_result = text_analyzer.analyze_text(text_content)
        
        # Generate recommendations
        recommendations = generate_recommendations(analysis_result['credibility_score'])
        analysis_result['recommendations'] = recommendations
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'input_type': 'text',
            'processing_time': 'instant'
        })
        
    except Exception as e:
        return handle_error(e, "Text Analysis")

@app.route('/analyze/url', methods=['POST'])
def analyze_url():
    """Analyze content from a webpage URL"""
    try:
        if not web_scraper or not text_analyzer:
            return jsonify({'error': 'URL analyzer not initialized. Check server logs.'}), 500
        
        # Get JSON data from request
        data = request.get_json()
        
        # Validate input
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Missing required field: url',
                'example': {'url': 'https://example.com/article'}
            }), 400
        
        url = data['url'].strip()
        if not url:
            return jsonify({'error': 'URL cannot be empty'}), 400
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            return jsonify({'error': 'URL must start with http:// or https://'}), 400
        
        logger.info(f"Analyzing URL: {url}")
        
        # Check source credibility first
        source_credibility = check_source_credibility(url)
        
        # Fetch webpage content
        content_data = web_scraper.fetch_page_content(url)
        
        if 'error' in content_data:
            return jsonify({
                'error': 'Could not fetch webpage content',
                'details': content_data['error']
            }), 400
        
        if not content_data.get('has_main_content'):
            return jsonify({
                'error': 'Could not extract meaningful content from webpage',
                'suggestions': [
                    'Check if the URL is accessible',
                    'Ensure the page contains readable text content',
                    'Try a different URL'
                ]
            }), 400
        
        # Combine title and main content for analysis
        text_content = f"{content_data.get('title', '')} {content_data.get('main_content', '')}".strip()
        
        if len(text_content) < 50:  # Require substantial content for URL analysis
            return jsonify({
                'error': 'Insufficient content found on webpage for meaningful analysis'
            }), 400
        
        # Analyze the extracted content
        analysis_result = text_analyzer.analyze_text(
            text_content, 
            source_score=source_credibility['score']
        )
        
        # Combine source and content analysis
        combined_result = {
            **analysis_result,
            'source_analysis': source_credibility,
            'webpage_info': {
                'title': content_data.get('title', 'No title found'),
                'author': content_data.get('author', 'Unknown'),
                'publication_date': content_data.get('publication_date', 'Unknown'),
                'word_count': content_data.get('word_count', 0),
                'url': url
            }
        }
        
        # Generate recommendations
        recommendations = generate_recommendations(
            analysis_result['credibility_score'],
            source_credibility=source_credibility
        )
        combined_result['recommendations'] = recommendations
        
        return jsonify({
            'success': True,
            'analysis': combined_result,
            'input_type': 'url'
        })
        
    except Exception as e:
        return handle_error(e, "URL Analysis")

@app.route('/analyze/video', methods=['POST'])
def analyze_video():
    """Analyze video by transcribing speech and checking for misinformation"""
    try:
        if not video_processor or not text_analyzer:
            return jsonify({'error': 'Video processor not initialized. Check server logs.'}), 500
        
        logger.info("Video analysis request received")
        
        # Check if video file was uploaded
        if 'video' not in request.files:
            return jsonify({
                'error': 'No video file provided in request',
                'instructions': 'Send video file with key "video" in form-data'
            }), 400
        
        file = request.files['video']
        
        # Check if a file was actually selected
        if file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
        
        # Validate file type
        if not allowed_video_file(file.filename):
            return jsonify({
                'error': 'Invalid video format',
                'supported_formats': list(ALLOWED_VIDEO_EXTENSIONS),
                'received_format': file.filename.split('.')[-1] if '.' in file.filename else 'unknown'
            }), 400
        
        # Create secure filename and save temporarily
        filename = secure_filename(file.filename)
        if not filename:  # secure_filename might return empty for invalid names
            filename = f"video_{hash(file.filename) % 10000}.mp4"
        
        temp_video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logger.info(f"Saving uploaded video: {filename}")
        file.save(temp_video_path)
        
        try:
            # Validate the saved video file
            is_valid, validation_error = video_processor.validate_video_file(temp_video_path)
            if not is_valid:
                return jsonify({'error': validation_error}), 400
            
            # Process the video (extract audio and transcribe)
            logger.info("Starting video transcription")
            transcript, processing_error = video_processor.process_video_file(temp_video_path)
            
            # Handle processing errors
            if processing_error:
                return jsonify({'error': processing_error}), 500
            
            if not transcript or len(transcript.strip()) < 10:
                return jsonify({
                    'error': 'No meaningful speech could be detected in the video',
                    'transcript': transcript or '',
                    'suggestions': [
                        'Check if video contains clear speech',
                        'Ensure audio quality is sufficient', 
                        'Try a video with longer speech content',
                        'Check if video has audio track'
                    ]
                }), 400
            
            logger.info(f"Transcription successful: {len(transcript)} characters")
            
            # Analyze the transcript for misinformation
            analysis_result = text_analyzer.analyze_text(transcript)
            
            # Generate recommendations
            recommendations = generate_recommendations(analysis_result['credibility_score'])
            analysis_result['recommendations'] = recommendations
            
            return jsonify({
                'success': True,
                'transcript': transcript,
                'analysis': analysis_result,
                'input_type': 'video',
                'video_info': {
                    'original_filename': file.filename,
                    'transcript_length': len(transcript),
                    'word_count': len(transcript.split()),
                    'processing_time': 'variable (depends on video length)'
                }
            })
            
        finally:
            # Always clean up uploaded video file
            try:
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)
                    logger.info("Uploaded video file cleaned up")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up uploaded file: {str(cleanup_error)}")
        
    except Exception as e:
        return handle_error(e, "Video Analysis")

@app.route('/analyze/image', methods=['POST'])
def analyze_image():
    """Analyze image by extracting text and checking for misinformation"""
    try:
        if not image_processor or not text_analyzer:
            return jsonify({'error': 'Image processor not initialized. Check server logs.'}), 500
        
        logger.info("Image analysis request received")
        
        # Check if image file was uploaded
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file provided in request',
                'instructions': 'Send image file with key "image" in form-data'
            }), 400
        
        file = request.files['image']
        
        # Check if a file was actually selected
        if file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        # Validate file type
        if not allowed_image_file(file.filename):
            return jsonify({
                'error': 'Invalid image format',
                'supported_formats': list(ALLOWED_IMAGE_EXTENSIONS),
                'received_format': file.filename.split('.')[-1] if '.' in file.filename else 'unknown'
            }), 400
        
        # Create secure filename and save temporarily
        filename = secure_filename(file.filename)
        if not filename:  # secure_filename might return empty for invalid names
            filename = f"image_{hash(file.filename) % 10000}.jpg"
        
        temp_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logger.info(f"Saving uploaded image: {filename}")
        file.save(temp_image_path)
        
        try:
            # Validate the saved image file
            is_valid, validation_error = image_processor.validate_image_file(temp_image_path)
            if not is_valid:
                return jsonify({'error': validation_error}), 400
            
            # Process the image (extract text using OCR)
            logger.info("Starting text extraction from image")
            extracted_text, processing_error = image_processor.process_image_file(temp_image_path)
            
            # Handle processing errors
            if processing_error:
                return jsonify({'error': processing_error}), 500
            
            if not extracted_text or len(extracted_text.strip()) < 5:
                return jsonify({
                    'message': 'No meaningful text found in image',
                    'extracted_text': extracted_text or '',
                    'suggestions': [
                        'Ensure image contains visible text',
                        'Check if image quality is sufficient',
                        'Try a different image with clearer text',
                        'Ensure text is not too small or blurry'
                    ]
                })
            
            logger.info(f"Text extraction successful: {len(extracted_text)} characters")
            
            # Analyze the extracted text for misinformation
            analysis_result = text_analyzer.analyze_text(extracted_text)
            
            # Generate recommendations
            recommendations = generate_recommendations(analysis_result['credibility_score'])
            analysis_result['recommendations'] = recommendations
            
            return jsonify({
                'success': True,
                'extracted_text': extracted_text,
                'analysis': analysis_result,
                'input_type': 'image',
                'image_info': {
                    'original_filename': file.filename,
                    'text_length': len(extracted_text),
                    'word_count': len(extracted_text.split()),
                    'processing_time': 'variable (depends on image complexity)'
                }
            })
            
        finally:
            # Always clean up uploaded image file
            try:
                if os.path.exists(temp_image_path):
                    os.unlink(temp_image_path)
                    logger.info("Uploaded image file cleaned up")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up uploaded file: {str(cleanup_error)}")
        
    except Exception as e:
        return handle_error(e, "Image Analysis")

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'Check the API documentation for available endpoints'
    }), 404

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'error': 'File too large',
        'message': f'Maximum file size is {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB'
    }), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'Something went wrong on the server'
    }), 500

# Development and Testing Endpoints (remove in production)
@app.route('/test', methods=['POST'])
def test_endpoint():
    """Test endpoint to verify request/response flow"""
    try:
        data = request.get_json()
        logger.info(f"Test endpoint received: {data}")
        
        return jsonify({
            'message': 'Test successful',
            'received_data': data,
            'status': 'ok',
            'timestamp': logger.name
        })
    except Exception as e:
        return jsonify({'error': f'Test failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Development server configuration
    logger.info("Starting Misinformation Detection API...")
    logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"Max file size: {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB")
    
    # Run the Flask development server
    app.run(
        debug=True,          # Enable debug mode for development
        host='0.0.0.0',     # Accept connections from any IP
        port=5000,          # Port number
        threaded=True       # Handle multiple requests concurrently
    )
