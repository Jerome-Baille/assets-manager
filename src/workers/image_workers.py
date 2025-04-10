"""Workers for image processing operations."""

from PyQt5.QtCore import QObject, pyqtSignal
from PIL import Image
import os
import concurrent.futures
import json

class ImageResizerWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)

    def __init__(self, input_path, output_dir, sizes):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.sizes = sizes

    def run(self):
        try:
            # First verify the image can be opened
            try:
                img = Image.open(self.input_path)
                img.size  # Verify image is valid
            except Exception as e:
                self.error.emit(f"Failed to open image: {str(e)}")
                return
                
            with Image.open(self.input_path) as img:
                total_tasks = len(self.sizes)
                completed_tasks = 0
                self.status_update.emit("Loading image...")
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    
                    def resize_image(size):
                        try:
                            resized_img = img.copy()
                            if resized_img is None:
                                return "Failed to copy image - received None object"
                                
                            resized_img = resized_img.resize((size, size), Image.LANCZOS)
                            
                            if size == 16:
                                output_path = os.path.join(self.output_dir, 'favicon.ico')
                                if resized_img.mode != 'RGBA':
                                    resized_img = resized_img.convert('RGBA')
                                try:
                                    resized_img.save(output_path, format='ICO', sizes=[(16, 16)])
                                except Exception as save_error:
                                    return f"Failed to save favicon.ico: {str(save_error)}"
                            else:
                                output_path = os.path.join(self.output_dir, f'icon-{size}x{size}.png')
                                try:
                                    resized_img.save(output_path, format='PNG')
                                except Exception as save_error:
                                    return f"Failed to save icon-{size}x{size}.png: {str(save_error)}"
                                
                            return True
                        except Exception as e:
                            return f"Failed to resize image to {size}x{size}: {str(e)}"
                    
                    for size in self.sizes:
                        futures.append(executor.submit(resize_image, size))
                    
                    for i, future in enumerate(concurrent.futures.as_completed(futures)):
                        result = future.result()
                        if result is not True:
                            self.error.emit(f"Failed to resize image: {result}")
                            return
                        
                        completed_tasks += 1
                        progress_value = int((completed_tasks / total_tasks) * 100)
                        self.progress.emit(progress_value)
                        self.status_update.emit(f"Generating icons: {completed_tasks}/{total_tasks}")
                
                # Create manifest.json
                manifest_icons = [
                    {
                        "src": f"icon-{size}x{size}.png",
                        "sizes": f"{size}x{size}",
                        "type": "image/png"
                    }
                    for size in self.sizes if size != 16
                ]
                
                manifest_content = {
                    "name": "PWA App",
                    "short_name": "PWA",
                    "icons": manifest_icons,
                    "start_url": ".",
                    "display": "standalone",
                    "theme_color": "#ffffff",
                    "background_color": "#ffffff"
                }
                
                try:
                    with open(os.path.join(self.output_dir, 'manifest.json'), 'w') as f:
                        json.dump(manifest_content, f, indent=2)
                except Exception as e:
                    self.error.emit(f"Failed to create manifest.json: {str(e)}")
                    return
                
            self.status_update.emit("All icons generated successfully!")
            self.progress.emit(100)
            self.finished.emit()
            
        except FileNotFoundError:
            self.error.emit("File not found.")
        except PermissionError:
            self.error.emit("Permission denied.")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


class ImageConverterWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)

    def __init__(self, input_files, output_dir, output_format, resize_settings=None):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.output_format = output_format
        self.resize_settings = resize_settings

    def run(self):
        try:
            total_files = len(self.input_files)
            processed_files = 0
            self.status_update.emit("Preparing to convert...")

            format_settings = {
                'WebP': ('.webp', 'WebP'),
                'JPEG': ('.jpg', 'JPEG'),
                'PNG': ('.png', 'PNG'),
                'AVIF': ('.avif', 'AVIF')
            }

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []

                def convert_file(file_path, output_format):
                    try:
                        with Image.open(file_path) as img:
                            original_width, original_height = img.size

                            if self.resize_settings:
                                target_width = self.resize_settings['width']
                                target_height = self.resize_settings['height']

                                if self.resize_settings['keep_aspect_ratio']:
                                    aspect_ratio = original_width / original_height
                                    if original_width > original_height:
                                        new_width = target_width
                                        new_height = int(target_width / aspect_ratio)
                                    else:
                                        new_height = target_height
                                        new_width = int(target_height * aspect_ratio)
                                else:
                                    new_width = target_width
                                    new_height = target_height

                                img = img.resize((new_width, new_height), Image.LANCZOS)
                                original_width, original_height = new_width, new_height

                            base_name = os.path.splitext(os.path.basename(file_path))[0]
                            extension, save_format = format_settings[output_format]
                            output_path = os.path.join(self.output_dir, f"{base_name}{extension}")

                            if output_format == 'PNG':
                                compression_level = 9 - int(100 / 11.1)  # Hardcoded quality to 100
                                img.save(output_path, format='PNG', optimize=True, 
                                       compress_level=min(9, max(0, compression_level)))
                            elif output_format == 'AVIF':
                                width, height = img.size
                                if width % 8 != 0 or height % 8 != 0:
                                    new_width = (width // 8) * 8
                                    new_height = round(new_width * height / width)
                                    new_height = (new_height // 8) * 8
                                    img = img.resize((new_width, new_height), Image.LANCZOS)
                                img.save(output_path, format='AVIF', quality=100)  # Hardcoded quality to 100
                            else:
                                if output_format == 'JPEG' and img.mode == 'RGBA':
                                    img = img.convert('RGB')
                                img.save(output_path, format=save_format, quality=100)  # Hardcoded quality to 100

                            return True
                    except Exception as e:
                        return f"Error converting {os.path.basename(file_path)}: {str(e)}"

                for file_path in self.input_files:
                    if self.output_format == 'Both':
                        futures.append(executor.submit(convert_file, file_path, 'WebP'))
                        futures.append(executor.submit(convert_file, file_path, 'AVIF'))
                    elif self.output_format in format_settings:
                        futures.append(executor.submit(convert_file, file_path, self.output_format))
                    else:
                        self.error.emit(f"Unsupported format: {self.output_format}")
                        return

                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    result = future.result()
                    if result is not True:
                        self.error.emit(result)
                        return

                    processed_files += 1
                    progress_value = int((processed_files / total_files) * 100)
                    self.progress.emit(progress_value)
                    self.status_update.emit(f"Converting files: {processed_files}/{total_files}")

            self.status_update.emit(f"Successfully converted {processed_files} files!")
            self.progress.emit(100)
            self.finished.emit()

        except FileNotFoundError:
            self.error.emit("File not found.")
        except PermissionError:
            self.error.emit("Permission denied.")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")