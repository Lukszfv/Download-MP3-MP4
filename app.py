from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import subprocess

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FFMPEG_PATH = os.getenv("FFMPEG_PATH", "")
COOKIES_PATH = os.path.join(BASE_DIR, "cookies.txt")


def get_ffmpeg():
    if os.name == "nt" and FFMPEG_PATH:
        return os.path.join(FFMPEG_PATH, "ffmpeg.exe")
    return "ffmpeg"


def forcar_h264(caminho):
    novo = caminho.replace(".mp4", "_h264.mp4")
    ffmpeg_exe = get_ffmpeg()

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", caminho,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "192k",
        novo
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(novo):
        os.remove(caminho)
        os.rename(novo, caminho)


def baixar(url, formato):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    is_youtube = "youtube.com" in url or "youtu.be" in url
    is_instagram = "instagram.com" in url

    base_opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": False,
        "no_warnings": True,
        "overwrites": True,
        "force_ipv4": True,
    }

    if is_youtube:
        base_opts["extractor_args"] = {
            "youtube": {
                "player_client": ["android"]
            }
        }

    if is_instagram and os.path.exists(COOKIES_PATH):
        base_opts["cookiefile"] = COOKIES_PATH

    try:
        if formato == "mp3":
            opts = {
                **base_opts,
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
        else:
            if is_youtube:
                opts = {
                    **base_opts,
                    "format": "18/best",
                    "merge_output_format": "mp4",
                }
            else:
                opts = {
                    **base_opts,
                    "format": "best",
                    "merge_output_format": "mp4",
                }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)

        video_id = info["id"]
        ext = "mp3" if formato == "mp3" else "mp4"
        arquivo = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

        # fallback se extensão diferente
        if not os.path.exists(arquivo):
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(video_id):
                    arquivo = os.path.join(DOWNLOAD_DIR, f)
                    break

        if os.path.exists(arquivo):
            if formato == "mp4":
                forcar_h264(arquivo)
            return arquivo

    except Exception as e:
        import traceback
        print("ERRO DOWNLOAD:", e)
        traceback.print_exc()

    return None


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/youtube")
def youtube():
    return render_template("pagina_youtube.html")


@app.route("/twitter")
def twitter():
    return render_template("pagina_twitter.html")
 
@app.route("/tiktok")
def tiktok():
    return render_template("pagina_tiktok.html")
 
@app.route("/instagram")
def instagram():
    return render_template("pagina_instagram.html")


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    formato = request.form.get("format")

    if not url or not formato:
        return "Dados invalidos", 400

    arquivo = baixar(url, formato)

    if arquivo:
        response = send_file(arquivo, as_attachment=True)

        @response.call_on_close
        def apagar():
            try:
                if os.path.exists(arquivo):
                    os.remove(arquivo)
            except:
                pass

        return response

    return "Erro ao gerar o arquivo", 500


if __name__ == "__main__":
    app.run(debug=True)