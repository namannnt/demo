# models/image_processor.py
"""
Complete TrOCR integration for image text extraction
"""
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image, ImageEnhance, ImageFilter
import torch
import os
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self, model_name="microsoft/trocr-base-printed"):
        """
        Initialize image processor with TrOCR
        Available models:
        - microsoft/trocr-base-printed (recommended for printed text)
        - microsoft/trocr-base-handwritten (for handwritten text)
        - microsoft/trocr-large-printed (higher accuracy, slower)
        """
        self.model_name = model_name
        
        try:
            # Load TrOCR processor and model
            self.processor = TrOCRProcessor.from_pretrained(model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.model = self.model.to('cuda')
                self.device = 'GPU'
            else:
                self.device = 'CPU'
            
            logger.info(f"✅ Loaded TrOCR model: {model_name} on {self.device}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load TrOCR model: {str(e)}")
            raise Exception(f"Could not initialize TrOCR: {str(e)}")
    
    def preprocess_image(self, image_path):
        """Load and preprocess image for better OCR results"""
        try:
            logger.info(f"🖼️ Preprocessing image: {image_path}")
            
            # Load image
            image = Image.open(image_path)
            
            # Convert to RGB (TrOCR expects RGB)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get original dimensions
            width, height = image.size
            logger.info(f"📏 Original image size: {width}x{height}")
            
            # Resize if too large (for memory efficiency)
            max_dimension = 2048
            if width > max_dimension or height > max_dimension:
                # Maintain aspect ratio
                if width > height:
                    new_width = max_dimension
                    new_height = int((height * max_dimension) / width)
                else:
                    new_height = max_dimension
                    new_width = int((width * max_dimension) / height)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"📐 Resized to: {new_width}x{new_height}")
            
            return image, None
            
        except Exception as e:
            logger.error(f"❌ Error preprocessing image: {str(e)}")
            return None, f"Image preprocessing failed: {str(e)}"
    
    def enhance_image(self, image):
        """Apply image enhancements to improve OCR accuracy"""
        try:
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(1.2)  # 20% more contrast
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = enhancer.enhance(1.5)  # 50% more sharpness
            
            # Apply slight smoothing to reduce noise
            enhanced = enhanced.filter(ImageFilter.SMOOTH_MORE)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"⚠️ Image enhancement failed: {str(e)}")
            return image  # Return original if enhancement fails
    
    def extract_text_with_trocr(self, image):
        """Extract text using TrOCR model"""
        try:
            logger.info("🔤 Extracting text with TrOCR")
            
            # Process image for model input
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            
            # Move to GPU if model is on GPU
            if next(self.model.parameters()).is_cuda:
                pixel_values = pixel_values.to('cuda')
            
            # Generate text
            with torch.no_grad():
                generated_ids = self.model.generate(pixel_values, max_length=512)
            
            # Decode generated text
            extracted_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Clean up text
            extracted_text = extracted_text.strip()
            
            if not extracted_text:
                return None, "No text detected in image"
            
            logger.info(f"✅ Text extraction completed: {len(extracted_text)} characters")
            return extracted_text, None
            
        except Exception as e:
            logger.error(f"❌ Error during text extraction: {str(e)}")
            return None, f"Text extraction failed: {str(e)}"
    
    def process_image_file(self, image_path):
        """Complete image processing pipeline with fallback strategies"""
        try:
            # Step 1: Preprocess image
            image, error = self.preprocess_image(image_path)
            if error:
                return None, error
            
            # Step 2: Try OCR with original image
            text, error = self.extract_text_with_trocr(image)
            if text and len(text.strip()) > 10:  # Good result
                return text, None
            
            # Step 3: Try with enhanced image if first attempt failed
            logger.info("🔧 Trying with enhanced image...")
            enhanced_image = self.enhance_image(image)
            text, error = self.extract_text_with_trocr(enhanced_image)
            if text and len(text.strip()) > 5:  # Accept shorter text on retry
                return text, None
            
            # Step 4: Try grayscale conversion
            logger.info("🔧 Trying with grayscale conversion...")
            gray_image = image.convert('L').convert('RGB')  # Convert back to RGB
            text, error = self.extract_text_with_trocr(gray_image)
            if text and len(text.strip()) > 3:  # Accept even shorter text
                return text, None
            
            return None, "Could not extract meaningful text after multiple attempts"
            
        except Exception as e:
            logger.error(f"❌ Image processing pipeline failed: {str(e)}")
            return None, f"Image processing failed: {str(e)}"
    
    def validate_image_file(self, file_path):
        """Validate image file before processing"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "Image file does not exist"
            
            # Check file extension
            ext = os.path.splitext(file_path)[1].lower()
            supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif']
            if ext not in supported_formats:
                return False, f"Unsupported format: {ext}. Supported: {', '.join(supported_formats)}"
            
            # Check file size (limit to 10MB)
            file_size = os.path.getsize(file_path)
            max_size = 10 * 1024 * 1024  # 10MB
            if file_size > max_size:
                return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: 10MB)"
            
            # Try to open image to verify it's valid
            try:
                with Image.open(file_path) as img:
                    img.verify()  # Verify image integrity
                    
                # Open again to check dimensions (verify() closes the file)
                with Image.open(file_path) as img:
                    width, height = img.size
                    
                    # Check minimum dimensions
                    if width < 50 or height < 50:
                        return False, f"Image too small: {width}x{height} (minimum: 50x50)"
                        
            except Exception as img_error:
                return False, f"Invalid image file: {str(img_error)}"
            
            return True, "Image file is valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_supported_formats(self):
        """Return list of supported image formats"""
        return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif']
    
    def get_model_info(self):
        """Get information about the loaded model"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'supported_formats': self.get_supported_formats()
        }
