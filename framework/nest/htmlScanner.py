import re
import os

class HtmlScanner:
    def __init__(self, root_directory):
        self.root_directory = root_directory

    def scan_and_replace(self, html_content):
        # Define a regex pattern to match your custom syntax, e.g., {{ images('filename.jpg') }}
        pattern = r'\{\{ *(\w+)\(\'([^\']+)\'.*?\) *\}\}'

        def replace_images(match):
            function_name = match.group(1)
            filename = match.group(2)
            if function_name == 'images':
                return self._replace_images(filename)
            # Add more functions as needed

        # Use regex to find and replace all occurrences of custom syntax
        replaced_html = re.sub(pattern, replace_images, html_content)
        return replaced_html

    def _replace_images(self, filename):
        # Construct the URL to the images directory
        images_path = os.path.join(self.root_directory, 'resources', 'images', filename)
        return images_path.replace('\\', '/')  # Replace backslashes with forward slashes for URL compatibility

