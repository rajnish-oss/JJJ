import re
def generate_slug(display_name:str):
    
    short_name = display_name.split(',')[0]
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', short_name).lower().strip()
    return re.sub(r'\s+', '_', slug)