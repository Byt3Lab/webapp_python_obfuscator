from quart import render_template, request, jsonify, send_file
import os
import config
from werkzeug.utils import secure_filename
from utils.obfuscator import Obfuscator

async def index():
    return await render_template('index.html')

async def obfuscate_zip():
    files = await request.files
    file = files.get('file')

    if not file:
        return jsonify({'error': 'No file provided'}), 400

    filename = secure_filename(file.filename)
    if not filename or not filename.lower().endswith('.zip'):
        return jsonify({'error': 'File must be a zip file'}), 400

    form = await request.form
    try:
        options_list = form.getlist('options')
    except Exception:
        opt = form.get('options')
        options_list = [opt] if opt else []

    method = form.get('method', 'pyarmor')
    options = {
        'method': method,
        'flags': options_list,
        'file_name': filename
    }

    file_path = os.path.join(config.UPLOAD_FOLDER, filename)

    await file.save(file_path)

    obfuscator = Obfuscator(file_path, options)
    try:
        result_zip = await obfuscator.obfuscate()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'file_path': result_zip})

async def download_obfuscated_zip():
    file_path = request.args.get('file_path')
    file_name = file_path.split('/')[-1] if file_path else 'protected_code.zip'
    return await send_file(file_path, mimetype='application/zip', as_attachment=True, attachment_filename=file_name)