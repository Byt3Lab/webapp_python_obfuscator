import config
from quart import Quart
from controllers import main_controller

app = Quart(__name__, template_folder='templates', static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512MB limit for uploads

app.get('/')(main_controller.index)
app.post('/obfuscate')(main_controller.obfuscate_zip)
app.get('/download')(main_controller.download_obfuscated_zip)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)      