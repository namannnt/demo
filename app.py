# Complete app.py - Misinformation Detection API with Phase 1 Enhancements
# Copy this entire file to replace your existing app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import logging
import traceback
from dotenv import load_dotenv

# Import your custom modules
try:
    from utils.sources import check_source_credibility
    from utils.web_scraper import WebScraper
    from utils.fact_checker import FactCheckAPI
    from utils.news_verifier import NewsVerifier
    from models.text_analyzer import TextAnalyzer
    from models.video_processor import VideoProcessor
    from models.image_processor import ImageProcessor
except ImportError as e:
    print(f"Warning: Could not import some modules - {e}")
    print("Make sure you've created all the Phase 1 files")

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
CORS(app)

# Configure logging
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

# Initialize all processors with error handling
processors_status = {}

try:
    web_scraper = WebScraper()
    processors_status['web_scraper'] = True
    logger.info("✅ WebScraper initialized")
except Exception as e:
    web_scraper = None
    processors_status['web_scraper'] = False
    logger.error(f"❌ WebScraper failed: {e}")

try:
    text_analyzer = TextAnalyzer()
    processors_status['text_analyzer'] = True
    logger.info("✅ TextAnalyzer initialized")
except Exception as e:
    text_analyzer = None
    processors_status['text_analyzer'] = False
    logger.error(f"❌ TextAnalyzer failed: {e}")

try:
    fact_checker = FactCheckAPI()
    processors_status['fact_checker'] = True
    logger.info("✅ FactCheckAPI initialized")
except Exception as e:
    fact_checker = None
    processors_status['fact_checker'] = False
    logger.error(f"❌ FactCheckAPI failed: {e}")

try:
    news_verifier = NewsVerifier()
    processors_status['news_verifier'] = True
    logger.info("✅ NewsVerifier initialized")
except Exception as e:
    news_verifier = None
    processors_status['news_verifier'] = False
    logger.error(f"❌ NewsVerifier failed: {e}")

try:
    video_processor = VideoProcessor(model_size="base")
    processors_status['video_processor'] = True
    logger.info("✅ VideoProcessor initialized")
except Exception as e:
    video_processor = None
    processors_status['video_processor'] = False
    logger.error(f"❌ VideoProcessor failed: {e}")

try:
    image_processor = ImageProcessor()
    processors_status['image_processor'] = True
    logger.info("✅ ImageProcessor initialized")
except Exception as e:
    image_processor = None
    processors_status['image_processor'] = False
    logger.error(f"❌ ImageProcessor failed: {e}")

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

def generate_recommendations(credibility_score, source_credibility=None, has_fact_check=False, has_news_verification=False):
    """Generate enhanced user recommendations based on all analysis results"""
    recommendations = []
    
    # Base recommendations based on credibility score
    if credibility_score >= 7:
        recommendations = [
            "✅ Content appears reliable based on our analysis",
            "📝 Still recommended to verify with multiple sources",
            "🔄 Check for recent updates or corrections"
        ]
    elif credibility_score >= 4:
        recommendations = [
            "⚠️ Exercise caution - verify claims independently", 
            "🔍 Look for corroboration from multiple reliable sources",
            "👤 Check the author's credentials and expertise",
            "📋 Look for primary sources or official statements"
        ]
    else:
        recommendations = [
            "🚨 High caution advised - likely unreliable content",
            "❌ Do not share without thorough verification",
            "📚 Consult multiple authoritative sources",
            "⚠️ Be aware of potential misinformation"
        ]
    
    # Add source-specific recommendations
    if source_credibility:
        if source_credibility['credibility'] == 'unknown':
            recommendations.append("❓ Source not recognized - research the publisher's credibility")
        elif source_credibility['credibility'] == 'unreliable':
            recommendations.append("⛔ Known problematic source - seek alternative sources")
        elif source_credibility['credibility'] == 'reliable':
            recommendations.append("✅ Source is generally considered reliable")
    
    # Add fact-check specific recommendations
    if has_fact_check:
        recommendations.append("🔍 Content has been cross-referenced with fact-checking databases")
    
    if has_news_verification:
        recommendations.append("📰 Content has been verified against recent news sources")
    
    return recommendations

def handle_error(error, error_type="Processing"):
    """Standardized error handling with logging"""
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
        "message": "🔍 AI-Powered Misinformation Detection API",
        "version": "2.0.0",
        "features": {
            "text_analysis": "✅ Advanced pattern detection with fact-checking",
            "url_analysis": "✅ Web scraping with source credibility verification",
            "video_analysis": "✅ Whisper-powered speech transcription",
            "image_analysis": "✅ TrOCR-powered text extraction",
            "fact_checking": "✅ Google Fact Check Tools integration",
            "news_verification": "✅ NewsAPI cross-referencing"
        },
        "endpoints": {
            "/health": "Health check and system status",
            "/analyze/text": "Analyze text content (POST)",
            "/analyze/url": "Analyze webpage URL (POST)", 
            "/analyze/video": "Analyze video transcript (POST)",
            "/analyze/image": "Analyze image text (POST)"
        },
        "status": "running"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Misinformation Detection API v2.0.0",
        "processors": processors_status,
        "capabilities": {
            "basic_analysis": processors_status.get('text_analyzer', False),
            "web_scraping": processors_status.get('web_scraper', False),
            "fact_checking": processors_status.get('fact_checker', False),
            "news_verification": processors_status.get('news_verifier', False),
            "video_processing": processors_status.get('video_processor', False),
            "image_processing": processors_status.get('image_processor', False)
        },
        "api_keys_configured": {
            "google_fact_check": bool(os.getenv('GOOGLE_FACT_CHECK_API_KEY')),
            "news_api": bool(os.getenv('NEWSAPI_API_KEY'))
        },
        "upload_folder": app.config['UPLOAD_FOLDER'],
        "max_file_size": f"{app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB"
    })

@app.route('/analyze/text', methods=['POST'])
def analyze_text():
    """Enhanced text analysis with fact-checking and news verification"""
    try:
        if not text_analyzer:
            return jsonify({'error': 'Text analyzer not available. Check server configuration.'}), 500
        
        # Get and validate input
        data = request.get_json()
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
        if len(text_content) > 10000:
            return jsonify({'error': 'Text too long. Maximum 10,000 characters allowed.'}), 400
        
        logger.info(f"🔍 Analyzing text content: {len(text_content)} characters")
        
        # Step 1: Basic text analysis
        analysis_result = text_analyzer.analyze_text(text_content)
        
        # Step 2: Enhanced fact-checking (if available)
        fact_check_enhanced = False
        if fact_checker:
            try:
                logger.info("🔍 Running fact-check analysis...")
                fact_check_data = fact_checker.check_claims_with_google(text_content)
                analysis_result = fact_checker.integrate_with_analysis(analysis_result, fact_check_data)
                fact_check_enhanced = True
                logger.info("✅ Fact-check analysis completed")
            except Exception as e:
                logger.error(f"⚠️ Fact checking failed: {e}")
                analysis_result['fact_check_status'] = 'failed'
        
        # Step 3: News verification (if available)
        news_verification_enhanced = False
        if news_verifier:
            try:
                logger.info("📰 Running news verification...")
                news_data = news_verifier.verify_news_claims(text_content)
                analysis_result = news_verifier.integrate_with_analysis(analysis_result, news_data)
                news_verification_enhanced = True
                logger.info("✅ News verification completed")
            except Exception as e:
                logger.error(f"⚠️ News verification failed: {e}")
                analysis_result['news_verification'] = 'failed'
        
        # Step 4: Generate enhanced recommendations
        recommendations = generate_recommendations(
            analysis_result['credibility_score'],
            has_fact_check=fact_check_enhanced,
            has_news_verification=news_verification_enhanced
        )
        analysis_result['recommendations'] = recommendations
        
        # Step 5: Return comprehensive results
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'input_type': 'text',
            'enhanced_features': {
                'fact_checking': fact_check_enhanced,
                'news_verification': news_verification_enhanced,
                'advanced_pattern_detection': True
            },
            'processing_info': {
                'text_length': len(text_content),
                'word_count': len(text_content.split()),
                'processing_time': 'real-time'
            }
        })
        
    except Exception as e:
        return handle_error(e, "Enhanced Text Analysis")

@app.route('/analyze/url', methods=['POST'])
def analyze_url():
    """Enhanced URL analysis with source checking and content verification"""
    try:
        if not web_scraper or not text_analyzer:
            return jsonify({'error': 'URL analyzer not available. Check server configuration.'}), 500
        
        # Get and validate input
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Missing required field: url',
                'example': {'url': 'https://example.com/article'}
            }), 400
        
        url = data['url'].strip()
        if not url:
            return jsonify({'error': 'URL cannot be empty'}), 400
        if not (url.startswith('http://') or url.startswith('https://')):
            return jsonify({'error': 'URL must start with http:// or https://'}), 400
        
        logger.info(f"🌐 Analyzing URL: {url}")
        
        # Step 1: Check source credibility
        source_credibility = check_source_credibility(url)
        logger.info(f"📊 Source credibility: {source_credibility.get('credibility', 'unknown')}")
        
        # Step 2: Fetch and analyze content
        content_data = web_scraper.fetch_page_content(url)
        if 'error' in content_data:
            return jsonify({
                'error': 'Could not fetch webpage content',
                'details': content_data['error'],
                'source_analysis': source_credibility
            }), 400
        
        if not content_data.get('has_main_content'):
            return jsonify({
                'error': 'Could not extract meaningful content from webpage',
                'suggestions': [
                    'Check if the URL is accessible',
                    'Ensure the page contains readable text content',
                    'Try a different URL'
                ],
                'source_analysis': source_credibility
            }), 400
        
        # Step 3: Analyze extracted content
        text_content = f"{content_data.get('title', '')} {content_data.get('main_content', '')}".strip()
        analysis_result = text_analyzer.analyze_text(
            text_content, 
            source_score=source_credibility['score']
        )
        
        # Step 4: Enhanced analysis (if available)
        enhanced_features = {'fact_checking': False, 'news_verification': False}
        
        if fact_checker:
            try:
                fact_check_data = fact_checker.check_claims_with_google(text_content)
                analysis_result = fact_checker.integrate_with_analysis(analysis_result, fact_check_data)
                enhanced_features['fact_checking'] = True
            except Exception as e:
                logger.error(f"Fact checking failed for URL: {e}")
        
        if news_verifier:
            try:
                news_data = news_verifier.verify_news_claims(text_content)
                analysis_result = news_verifier.integrate_with_analysis(analysis_result, news_data)
                enhanced_features['news_verification'] = True
            except Exception as e:
                logger.error(f"News verification failed for URL: {e}")
        
        # Step 5: Combine all results
        combined_result = {
            **analysis_result,
            'source_analysis': source_credibility,
            'webpage_info': {
                'title': content_data.get('title', 'No title found'),
                'author': content_data.get('author', 'Unknown'),
                'publication_date': content_data.get('publication_date', 'Unknown'),
                'word_count': content_data.get('word_count', 0),
                'url': url,
                'domain': source_credibility.get('domain', 'Unknown')
            }
        }
        
        # Step 6: Generate recommendations
        recommendations = generate_recommendations(
            analysis_result['credibility_score'],
            source_credibility=source_credibility,
            has_fact_check=enhanced_features['fact_checking'],
            has_news_verification=enhanced_features['news_verification']
        )
        combined_result['recommendations'] = recommendations
        
        return jsonify({
            'success': True,
            'analysis': combined_result,
            'input_type': 'url',
            'enhanced_features': enhanced_features
        })
        
    except Exception as e:
        return handle_error(e, "Enhanced URL Analysis")

@app.route('/analyze/video', methods=['POST'])
def analyze_video():
    """Enhanced video analysis with Whisper transcription"""
    try:
        if not video_processor or not text_analyzer:
            return jsonify({'error': 'Video processor not available. Check server configuration.'}), 500
        
        logger.info("🎥 Video analysis request received")
        
        # Validate file upload
        if 'video' not in request.files:
            return jsonify({
                'error': 'No video file provided',
                'instructions': 'Send video file with key "video" in form-data'
            }), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
        
        if not allowed_video_file(file.filename):
            return jsonify({
                'error': 'Invalid video format',
                'supported_formats': list(ALLOWED_VIDEO_EXTENSIONS),
                'received_format': file.filename.split('.')[-1] if '.' in file.filename else 'unknown'
            }), 400
        
        # Save and validate file
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"video_{hash(file.filename) % 10000}.mp4"
        
        temp_video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"💾 Saving video: {filename}")
        file.save(temp_video_path)
        
        try:
            # Validate video file
            is_valid, validation_error = video_processor.validate_video_file(temp_video_path)
            if not is_valid:
                return jsonify({'error': validation_error}), 400
            
            # Process video with Whisper
            logger.info("🎤 Starting Whisper transcription...")
            transcript, processing_error = video_processor.process_video_file(temp_video_path)
            
            if processing_error:
                return jsonify({'error': processing_error}), 500
            
            if not transcript or len(transcript.strip()) < 10:
                return jsonify({
                    'error': 'No meaningful speech detected in video',
                    'transcript': transcript or '',
                    'suggestions': [
                        'Ensure video contains clear speech',
                        'Check audio quality and volume',
                        'Try a video with longer speech content',
                        'Verify video has an audio track'
                    ]
                }), 400
            
            logger.info(f"✅ Transcription successful: {len(transcript)} characters")
            
            # Analyze transcript
            analysis_result = text_analyzer.analyze_text(transcript)
            
            # Enhanced analysis (if available)
            enhanced_features = {'fact_checking': False, 'news_verification': False}
            
            if fact_checker:
                try:
                    fact_check_data = fact_checker.check_claims_with_google(transcript)
                    analysis_result = fact_checker.integrate_with_analysis(analysis_result, fact_check_data)
                    enhanced_features['fact_checking'] = True
                except Exception as e:
                    logger.error(f"Fact checking failed for video: {e}")
            
            if news_verifier:
                try:
                    news_data = news_verifier.verify_news_claims(transcript)
                    analysis_result = news_verifier.integrate_with_analysis(analysis_result, news_data)
                    enhanced_features['news_verification'] = True
                except Exception as e:
                    logger.error(f"News verification failed for video: {e}")
            
            # Generate recommendations
            recommendations = generate_recommendations(
                analysis_result['credibility_score'],
                has_fact_check=enhanced_features['fact_checking'],
                has_news_verification=enhanced_features['news_verification']
            )
            analysis_result['recommendations'] = recommendations
            
            return jsonify({
                'success': True,
                'transcript': transcript,
                'analysis': analysis_result,
                'input_type': 'video',
                'enhanced_features': enhanced_features,
                'video_info': {
                    'original_filename': file.filename,
                    'transcript_length': len(transcript),
                    'word_count': len(transcript.split()),
                    'model_used': video_processor.get_model_info() if hasattr(video_processor, 'get_model_info') else 'Whisper'
                }
            })
            
        finally:
            # Always clean up uploaded file
            try:
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)
                    logger.info("🧹 Cleaned up video file")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Could not clean up file: {str(cleanup_error)}")
        
    except Exception as e:
        return handle_error(e, "Enhanced Video Analysis")

@app.route('/analyze/image', methods=['POST'])
def analyze_image():
    """Enhanced image analysis with TrOCR text extraction"""
    try:
        if not image_processor or not text_analyzer:
            return jsonify({'error': 'Image processor not available. Check server configuration.'}), 500
        
        logger.info("🖼️ Image analysis request received")
        
        # Validate file upload
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file provided',
                'instructions': 'Send image file with key "image" in form-data'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        if not allowed_image_file(file.filename):
            return jsonify({
                'error': 'Invalid image format',
                'supported_formats': list(ALLOWED_IMAGE_EXTENSIONS),
                'received_format': file.filename.split('.')[-1] if '.' in file.filename else 'unknown'
            }), 400
        
        # Save and validate file
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"image_{hash(file.filename) % 10000}.jpg"
        
        temp_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"💾 Saving image: {filename}")
        file.save(temp_image_path)
        
        try:
            # Validate image file
            is_valid, validation_error = image_processor.validate_image_file(temp_image_path)
            if not is_valid:
                return jsonify({'error': validation_error}), 400
            
            # Extract text with TrOCR
            logger.info("🔤 Starting TrOCR text extraction...")
            extracted_text, processing_error = image_processor.process_image_file(temp_image_path)
            
            if processing_error:
                return jsonify({'error': processing_error}), 500
            
            if not extracted_text or len(extracted_text.strip()) < 5:
                return jsonify({
                    'message': 'No meaningful text found in image',
                    'extracted_text': extracted_text or '',
                    'suggestions': [
                        'Ensure image contains visible text',
                        'Check image quality and resolution',
                        'Try an image with clearer, larger text',
                        'Ensure text is not too small or blurry'
                    ]
                })
            
            logger.info(f"✅ Text extraction successful: {len(extracted_text)} characters")
            
            # Analyze extracted text
            analysis_result = text_analyzer.analyze_text(extracted_text)
            
            # Enhanced analysis (if available)
            enhanced_features = {'fact_checking': False, 'news_verification': False}
            
            if fact_checker:
                try:
                    fact_check_data = fact_checker.check_claims_with_google(extracted_text)
                    analysis_result = fact_checker.integrate_with_analysis(analysis_result, fact_check_data)
                    enhanced_features['fact_checking'] = True
                except Exception as e:
                    logger.error(f"Fact checking failed for image: {e}")
            
            if news_verifier:
                try:
                    news_data = news_verifier.verify_news_claims(extracted_text)
                    analysis_result = news_verifier.integrate_with_analysis(analysis_result, news_data)
                    enhanced_features['news_verification'] = True
                except Exception as e:
                    logger.error(f"News verification failed for image: {e}")
            
            # Generate recommendations
            recommendations = generate_recommendations(
                analysis_result['credibility_score'],
                has_fact_check=enhanced_features['fact_checking'],
                has_news_verification=enhanced_features['news_verification']
            )
            analysis_result['recommendations'] = recommendations
            
            return jsonify({
                'success': True,
                'extracted_text': extracted_text,
                'analysis': analysis_result,
                'input_type': 'image',
                'enhanced_features': enhanced_features,
                'image_info': {
                    'original_filename': file.filename,
                    'text_length': len(extracted_text),
                    'word_count': len(extracted_text.split()),
                    'model_used': image_processor.get_model_info() if hasattr(image_processor, 'get_model_info') else 'TrOCR'
                }
            })
            
        finally:
            # Always clean up uploaded file
            try:
                if os.path.exists(temp_image_path):
                    os.unlink(temp_image_path)
                    logger.info("🧹 Cleaned up image file")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Could not clean up file: {str(cleanup_error)}")
        
    except Exception as e:
        return handle_error(e, "Enhanced Image Analysis")

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'Check the API documentation for available endpoints',
        'available_endpoints': ['/health', '/analyze/text', '/analyze/url', '/analyze/video', '/analyze/image']
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

# Development and Testing Endpoints
@app.route('/test', methods=['POST'])
def test_endpoint():
    """Test endpoint for development"""
    try:
        data = request.get_json()
        logger.info(f"Test endpoint received: {data}")
        
        return jsonify({
            'message': 'Test successful',
            'received_data': data,
            'processors_available': processors_status,
            'timestamp': logger.name,
            'status': 'ok'
        })
    except Exception as e:
        return jsonify({'error': f'Test failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Development server startup
    logger.info("🚀 Starting Enhanced Misinformation Detection API v2.0.0...")
    logger.info(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"📊 Max file size: {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB")
    logger.info(f"🔧 Processors status: {processors_status}")
    
    # Display API key status
    if os.getenv('GOOGLE_FACT_CHECK_API_KEY'):
        logger.info("🔑 Google Fact Check API key configured")
    else:
        logger.warning("⚠️ Google Fact Check API key not found")
    
    if os.getenv('NEWSAPI_API_KEY'):
        logger.info("🔑 NewsAPI key configured")
    else:
        logger.warning("⚠️ NewsAPI key not found")
    
    # Run Flask development server
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
