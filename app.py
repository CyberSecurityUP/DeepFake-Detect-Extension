import os
import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
import mimetypes

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = './uploaded_images'
API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImVlYTRlMGU3LTI5MjUtNDdjMC05N2E4LTczODQ3NTdiZTJjNyIsInVzZXJfaWQiOiJlZWE0ZTBlNy0yOTI1LTQ3YzAtOTdhOC03Mzg0NzU3YmUyYzciLCJhdWQiOiJhY2Nlc3MiLCJleHAiOjAuMH0.FP9ypt4AWBEQaAa-N0Hra-lqe31St_Ha-ZTF22jWHzY'  # Insira sua chave de API AIorNot aqui
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Função para verificar se a imagem é um deepfake usando a API AIorNot
def check_deepfake(image_path, api_key):
    url = "https://api.aiornot.com/v1/reports/image"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    # Detecta automaticamente o tipo MIME do arquivo com base na extensão
    file_name = os.path.basename(image_path)
    file_type, _ = mimetypes.guess_type(image_path)

    # Verifica se o tipo MIME é suportado
    if file_type not in ["image/png", "image/jpeg"]:
        return {"error": "Unsupported file format. Please use PNG or JPEG images."}

    # Envia o arquivo para a API
    try:
        with open(image_path, "rb") as file:
            files = {"object": (file_name, file, file_type)}
            response = requests.post(url, headers=headers, files=files)

        # Verifica e interpreta a resposta da API
        if response.status_code == 200:
            response_data = response.json()
            # Exibe a resposta completa para depuração
            print("Resposta completa da API:", response_data)

            # Processa o veredicto da resposta
            verdict = response_data.get("report", {}).get("verdict", "unknown")
            is_ai = response_data.get("report", {}).get("ai", {}).get("is_detected", False)
            is_human = response_data.get("report", {}).get("human", {}).get("is_detected", False)

            # Retorna o resultado estruturado
            return {
                "success": True,
                "verdict": verdict,
                "is_ai": is_ai,
                "is_human": is_human,
                "raw_response": response_data  # Inclui toda a resposta para análise adicional
            }
        elif response.status_code == 429:
            return {"error": "Rate limit exceeded. Please try again later."}
        else:
            return {
                "error": f"Failed to check deepfake - Status code: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


# Rota para upload de imagem e verificação de deepfake
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Salva o arquivo com um nome seguro
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Verifica se o arquivo foi realmente salvo
    if not os.path.exists(file_path):
        return jsonify({"error": "File could not be saved."}), 500

    # Passa o caminho completo do arquivo salvo para a verificação de deepfake
    result = check_deepfake(file_path, API_KEY)

    # Remove o arquivo após análise
    os.remove(file_path)

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
