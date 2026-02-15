from flask import Flask, render_template, request, jsonify, Response
import instaloader
import requests
from urllib.parse import quote

# POINT FLASK TO THE CORRECT TEMPLATE FOLDER INSIDE 'API'
app = Flask(__name__, template_folder='templates')
L = instaloader.Instaloader()

# Fix for Vercel read-only file system
# Instaloader tries to save session files, which crashes Vercel.
# We disable this by not logging in and not saving session.

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape_profile():
    data = request.json
    target_username = data.get('username')
    
    if not target_username:
        return jsonify({'error': 'No username provided'}), 400

    try:
        profile = instaloader.Profile.from_username(L.context, target_username)
        
        user_data = {
            'username': profile.username,
            'full_name': profile.full_name,
            'biography': profile.biography,
            'profile_pic_url': f"/proxy_image?url={quote(profile.profile_pic_url)}", 
            'followers': format_number(profile.followers),
            'following': format_number(profile.followees),
            'posts_count': format_number(profile.mediacount),
            'external_url': profile.external_url,
            'posts': []
        }

        count = 0
        for post in profile.get_posts():
            if count >= 9:
                break
            user_data['posts'].append({
                'image_url': f"/proxy_image?url={quote(post.url)}" 
            })
            count += 1
            
        return jsonify(user_data)

    except Exception as e:
        # This will likely happen on Vercel due to IP blocking
        return jsonify({'error': f"Failed (likely IP block): {str(e)}"}), 500

@app.route('/proxy_image')
def proxy_image():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, stream=True)
        return Response(
            response.iter_content(chunk_size=1024), 
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except Exception as e:
        return str(e), 500

def format_number(num):
    if num > 1000000:
        return f"{num/1000000:.1f}m"
    elif num > 1000:
        return f"{num/1000:.1f}k"
    return str(num)

# NOTE: app.run() is REMOVED because Vercel runs the app automatically