from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import os
import uuid
from werkzeug.utils import secure_filename
import logging
import sys
from datetime import datetime
from pydub import AudioSegment
from dotenv import load_dotenv
from itertools import cycle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

PROJECT_NAME = os.getenv("PROJECT_NAME", "KichikOlimUZ")

def env_list(name):
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]

def load_media_urls():
    media_path = os.path.join(BASE_DIR, "media_urls.json")
    try:
        with open(media_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.warning("media_urls.json topilmadi")
    except json.JSONDecodeError as exc:
        logger.error(f"media_urls.json o'qishda xatolik: {exc}")
    return {"images": {}, "videos": {}, "audio": {}}

def media_url(media_type, key):
    return MEDIA_URLS.get(media_type, {}).get(key, "")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
MEDIA_URLS = load_media_urls()

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
app.config['AUDIO_FOLDER'] = os.getenv("AUDIO_FOLDER", os.path.join(BASE_DIR, "static", "audio"))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)

STT_TOKENS = env_list("STT_TOKENS")
TTS_TOKENS = env_list("TTS_TOKENS")

if not STT_TOKENS or not TTS_TOKENS:
    raise RuntimeError("STT_TOKENS va TTS_TOKENS .env yoki Railway environment variables ichida berilishi kerak")

stt_token_cycle = cycle(STT_TOKENS)
tts_token_cycle = cycle(TTS_TOKENS)

current_stt_token = next(stt_token_cycle)
current_tts_token = next(tts_token_cycle)

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# 4-sinf 2-qism mavzulari
GRADE4_PART2_TOPICS = [
    {
        'id': 'modda',
        'name': 'Modda',
        'character': 'Modda qahramoni',
        'image': media_url("images", "modda"),
        'video': media_url("videos", "modda"),
        'greeting': '🧪 Salom! Men Modda qahramoni. Moddalar haqida savollaringizga javob beraman!',
        'icon': '🧪',
        'color': '#9C27B0'
    },
    {
        'id': 'havo',
        'name': 'Havo',
        'character': 'Havo shakli',
        'image': media_url("images", "havo"),
        'video': media_url("videos", "havo"),
        'greeting': '💨 Salom! Men Havo qahramoni. Havo va uning xossalari haqida so\'rang!',
        'icon': '💨',
        'color': '#00BCD4'
    },
    {
        'id': 'suv',
        'name': 'Suv',
        'character': 'Suv qahramoni',
        'image': media_url("images", "suv"),
        'video': media_url("videos", "suv"),
        'greeting': '💧 Salom! Men Suv qahramoni. Suv va uning manbalari haqida savol bering!',
        'icon': '💧',
        'color': '#2196F3'
    },
    {
        'id': 'litosfera',
        'name': 'Litosfera',
        'character': 'Litosfera qahramoni',
        'image': media_url("images", "litosfera"),
        'video': media_url("videos", "litosfera"),
        'greeting': '🗻 Salom! Men Litosfera qahramoni. Yer qobig\'i haqida so\'rang!',
        'icon': '🗻',
        'color': '#795548'
    },
    {
        'id': 'tuproq',
        'name': 'Tuproq',
        'character': 'Tuproq qahramoni',
        'image': media_url("images", "tuproq"),
        'video': media_url("videos", "tuproq"),
        'greeting': '🌱 Salom! Men Tuproq qahramoni. Tuproq va unda yashovchi jonzotlar haqida so\'rang!',
        'icon': '🌱',
        'color': '#8BC34A'
    },
    {
        'id': 'yonuvchi',
        'name': 'Yonuvchi foydali qazilmalar',
        'character': 'Neft qahramoni',
        'image': media_url("images", "yonuvchi"),
        'video': media_url("videos", "yonuvchi"),
        'greeting': '🛢️ Salom! Men Neft qahramoni. Yonuvchi qazilmalar haqida savol bering!',
        'icon': '🛢️',
        'color': '#FF9800'
    },
    {
        'id': 'metallar',
        'name': 'Metallar',
        'character': 'Metall qahramoni',
        'image': media_url("images", "metallar"),
        'video': media_url("videos", "metallar"),
        'greeting': '⚙️ Salom! Men Metall qahramoni. Metallar va ulardan foydalanish haqida so\'rang!',
        'icon': '⚙️',
        'color': '#607D8B'
    },
    {
        'id': 'harakat',
        'name': 'Harakat va kuch',
        'character': 'Kuch qahramoni',
        'image': media_url("images", "harakat"),
        'video': media_url("videos", "harakat"),
        'greeting': '🏃 Salom! Men Kuch qahramoni. Harakat va kuch haqida savollaringizga javob beraman!',
        'icon': '🏃',
        'color': '#F44336'
    },
    {
        'id': 'yer',
        'name': 'Yer',
        'character': 'Yer qahramoni',
        'image': media_url("images", "yer"),
        'video': media_url("videos", "yer"),
        'greeting': '🌍 Salom! Men Yer qahramoni. Sayyoramizning tuzilishi haqida so\'rang!',
        'icon': '🌍',
        'color': '#4CAF50'
    },
    {
        'id': 'tabiat',
        'name': 'Tabiat hodisalari',
        'character': 'Tabiat qahramoni',
        'image': media_url("images", "tabiat"),
        'video': media_url("videos", "tabiat"),
        'greeting': '⛈️ Salom! Men Tabiat qahramoni. Tabiat hodisalari haqida savol bering!',
        'icon': '⛈️',
        'color': '#FF5722'
    },
    {
        'id': 'kashfiyot',
        'name': 'Kashfiyotlar tarixi',
        'character': 'Kashfiyotchi',
        'image': media_url("images", "kashfiyot"),
        'video': media_url("videos", "kashfiyot"),
        'greeting': '💡 Salom! Men Kashfiyotchi. Buyuk kashfiyotlar tarixi haqida so\'rang!',
        'icon': '💡',
        'color': '#FFC107'
    },
    {
        'id': 'kosmos',
        'name': 'Kosmos',
        'character': 'Kosmonavt',
        'image': media_url("images", "kosmos"),
        'video': media_url("videos", "kosmos"),
        'greeting': '🚀 Salom! Men Kosmonavt. Kosmos va yulduzlar haqida savol bering!',
        'icon': '🚀',
        'color': '#3F51B5'
    }
]

# Mavzular konfiguratsiyasi
TOPICS_CONFIG = {
    '1': {
        'I': {
            'name': 'Tabiy fanlar I qism',
            'image': media_url("images", "sun"),
            'video': media_url("videos", "sun"),
            'greeting': '🌞 Salom! Menga astronomiya haqida istalgan savolingizni bering!'
        },
        'II': {
            'name': 'Tabiy fanlar II qism',
            'image': media_url("images", "earth"),
            'video': media_url("videos", "earth"),
            'greeting': '🌍 Salom! Yer haqida savollaringizga javob beraman!'
        }
    },
    '2': {
        'I': {
            'name': 'Tabiy fanlar I qism',
            'image': media_url("images", "sun"),
            'video': media_url("videos", "sun"),
            'greeting': '🌞 2-sinf! Quyosh haqida nimalarni bilasiz?'
        },
        'II': {
            'name': 'Tabiy fanlar II qism',
            'image': media_url("images", "earth"),
            'video': media_url("videos", "earth"),
            'greeting': '🌍 2-sinf! Keling, Yer sayyoramizni o\'rganamiz!'
        }
    },
    '3': {
        'I': {
            'name': 'Tabiy fanlar I qism',
            'image': media_url("images", "sun"),
            'video': media_url("videos", "sun"),
            'greeting': '🌞 3-sinf! Quyosh tizimi haqida savollar bering!'
        },
        'II': {
            'name': 'Tabiy fanlar II qism',
            'image': media_url("images", "earth"),
            'video': media_url("videos", "earth"),
            'greeting': '🌍 3-sinf! Yerning tuzilishi va harakati haqida so\'rang!'
        }
    },
    '4': {
        'I': {
            'name': 'Tabiy fanlar I qism',
            'image': media_url("images", "sun"),
            'video': media_url("videos", "sun"),
            'greeting': '🌞 4-sinf! Quyosh va yulduzlar haqida savollaringizni kutaman!'
        },
        'II': {
            'name': 'Tabiy fanlar II qism',
            'image': media_url("images", "earth"),
            'video': media_url("videos", "earth"),
            'greeting': '🌍 4-sinf! Yer va koinot haqida chuqurroq bilim oling!'
        }
    }
}

def attach_media_urls():
    for topic in GRADE4_PART2_TOPICS:
        topic["image"] = media_url("images", topic["id"])
        topic["video"] = media_url("videos", topic["id"])

    for grade_parts in TOPICS_CONFIG.values():
        for part_config in grade_parts.values():
            image_key = "sun" if "I qism" in part_config["name"] else "earth"
            video_key = image_key
            part_config["image"] = media_url("images", image_key)
            part_config["video"] = media_url("videos", video_key)

attach_media_urls()

def get_next_stt_token():
    global current_stt_token
    current_stt_token = next(stt_token_cycle)
    logger.warning(f"STT token almashtirildi: {current_stt_token[:10]}...")
    return current_stt_token

def get_next_tts_token():
    global current_tts_token
    current_tts_token = next(tts_token_cycle)
    logger.warning(f"TTS token almashtirildi: {current_tts_token[:10]}...")
    return current_tts_token

def convert_to_wav(input_path, output_path):
    try:
        logger.info(f"Konvertatsiya: {input_path} -> {output_path}")
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format='wav')
        logger.info(f"Konvertatsiya muvaffaqiyatli: {os.path.getsize(output_path)} bytes")
        return True
    except Exception as e:
        logger.error(f"Konvertatsiya xatosi: {str(e)}")
        return False

def pitch_shift_with_pydub(audio_path, output_path, semitones=7):
    try:
        audio = AudioSegment.from_file(audio_path)
        
        # Pydub orqali pitch shift qilinganda tezlik ham oshadi. 
        # Shirinroq bolakay ovozi chiqishi uchun speed_factor ni 1.3 atrofida ushlaymiz.
        # Bu ovozni aniq, yosh va mayin bolaga o'xshatadi.
        speed_factor = 1.0 + (semitones / 22.0)
        
        new_frame_rate = int(audio.frame_rate * speed_factor)
        
        # Ovozni yuqori pitchni va sal tezlikni o'rnatamiz
        pitched_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_frame_rate})
        
        # Faylni saqlashda standart kadr tezligiga qaytaramiz (lekin ovoz bola ovozidek qoladi)
        pitched_audio = pitched_audio.set_frame_rate(audio.frame_rate)
        
        pitched_audio.export(output_path, format='wav')
        logger.info(f"Pitch shift muvaffaqiyatli: {semitones} semitones, sekinlashtirildi")
        return True
        return False
    except Exception as e:
        logger.error(f"Pitch shift xatosi: {str(e)}")
        audio = AudioSegment.from_file(audio_path)
        audio.export(output_path, format='wav')
        return False

@app.route('/')
def index():
    logger.info("Index sahifasi so'raldi")
    app_config = {
        "projectName": PROJECT_NAME,
        "thinkingMusicUrl": media_url("audio", "oylash"),
        "tutorialVideos": {
            "tuproq": media_url("videos", "tuproqdarslik")
        },
        "gradeCards": [
            {"number": "1", "icon": "🌟", "image": media_url("images", "1"), "color": "#FF6B6B"},
            {"number": "2", "icon": "⭐", "image": media_url("images", "2"), "color": "#4ECDC4"},
            {"number": "3", "icon": "✨", "image": media_url("images", "3"), "color": "#45B7D1"},
            {"number": "4", "icon": "💫", "image": media_url("images", "4"), "color": "#96CEB4"},
        ]
    }
    return render_template(
        'index.html',
        app_config=app_config,
        grade4_part2_topics=GRADE4_PART2_TOPICS
    )

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/delete_audio', methods=['POST'])
def delete_audio():
    data = request.json
    if not data or 'url' not in data:
        return jsonify({'success': False}), 400
    
    filename = data['url'].split('/')[-1]
    file_path = os.path.join(app.config['AUDIO_FOLDER'], filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Ovoz o'chirildi: {filename}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Faylni o'chirishda xatolik: {e}")
        return jsonify({'success': False})

@app.route('/get_topics')
def get_topics():
    """Barcha sinflar va mavzular ro'yxatini qaytaradi"""
    return jsonify(TOPICS_CONFIG)

@app.route('/get_grade4_part2_topics')
def get_grade4_part2_topics():
    """4-sinf 2-qism mavzularini qaytaradi"""
    return jsonify(GRADE4_PART2_TOPICS)

@app.route('/process_audio', methods=['POST'])
def process_audio():
    logger.info("=" * 80)
    logger.info("Yangi so'rov qabul qilindi")
    
    grade = request.form.get('grade', '1')
    part = request.form.get('part', 'I')
    topic_id = request.form.get('topic_id', None)
    
    # Mavzu ma'lumotlarini olish
    if grade == '4' and part == 'II' and topic_id:
        topic_config = next((t for t in GRADE4_PART2_TOPICS if t['id'] == topic_id), GRADE4_PART2_TOPICS[0])
    else:
        topic_config = TOPICS_CONFIG.get(grade, {}).get(part, TOPICS_CONFIG['1']['I'])
    
    if 'audio' not in request.files:
        logger.error("'audio' fayl topilmadi!")
        return jsonify({'success': False, 'error': 'Audio fayl topilmadi'}), 400
    
    audio_file = request.files['audio']
    logger.info(f"Audio fayl: {audio_file.filename}, Grade: {grade}, Part: {part}, Topic: {topic_id}")
    
    if audio_file.filename == '':
        return jsonify({'success': False, 'error': 'Fayl tanlanmagan'}), 400
    
    original_filename = secure_filename(f"original_{uuid.uuid4().hex}.webm")
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    audio_file.save(original_path)
    logger.info(f"Original fayl saqlandi: {original_path}")
    
    wav_filename = f"converted_{uuid.uuid4().hex}.wav"
    wav_path = os.path.join(app.config['UPLOAD_FOLDER'], wav_filename)
    
    if not convert_to_wav(original_path, wav_path):
        os.remove(original_path)
        return jsonify({'success': False, 'error': 'Audio formatni o\'tkazib bo\'lmadi'}), 500
    
    try:
        stt_result = speech_to_text_with_retry(wav_path)
        if 'error' in stt_result:
            return jsonify({'success': False, 'error': stt_result['error']}), 500
        
        if grade == '4' and part == 'II' and topic_id:
            context = f"Siz 4-sinf o'quvchisisiz. Mavzu: {topic_config['name']}. {topic_config['character']} bilan suhbatlashyapsiz. "
            ai_result = get_ai_response_for_topic(context + stt_result['text'], topic_config)
        else:
            context = f"Siz {grade}-sinf {part}-qism o'quvchisisiz. Mavzu: {topic_config['name']}. "
            ai_result = get_ai_response(context + stt_result['text'], grade, part)
        
        if 'error' in ai_result:
            return jsonify({'success': False, 'error': ai_result['error']}), 500
        
        tts_result = text_to_speech_with_retry(ai_result['text'])
        if 'error' in tts_result:
            return jsonify({'success': False, 'error': tts_result['error']}), 500
        
        tts_audio_path = os.path.join(app.config['AUDIO_FOLDER'], tts_result['url'].replace('/static/audio/', ''))
        child_audio_filename = f"child_voice_{uuid.uuid4().hex}.wav"
        child_audio_path = os.path.join(app.config['AUDIO_FOLDER'], child_audio_filename)
        
        success = pitch_shift_with_pydub(tts_audio_path, child_audio_path, semitones=6)
        
        if success:
            child_audio_url = f"/static/audio/{child_audio_filename}"
            # O'zgargan audio muvaffaqiyatli chiqqach, keraksiz asl MP3 ni o'chirib yuboramiz
            if os.path.exists(tts_audio_path):
                os.remove(tts_audio_path)
        else:
            child_audio_url = tts_result['url']
        
        os.remove(original_path)
        os.remove(wav_path)
        
        return jsonify({
            'success': True,
            'user_question': stt_result['text'],
            'ai_response': ai_result['text'],
            'audio_url': child_audio_url,
            'topic': topic_config
        })
        
    except Exception as e:
        logger.error(f"Xatolik: {str(e)}", exc_info=True)
        if os.path.exists(original_path):
            os.remove(original_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        return jsonify({'success': False, 'error': str(e)}), 500

def get_ai_response_for_topic(user_question, topic_config):
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(api_key=HUGGINGFACE_API_KEY, timeout=60)
        
        system_prompt = f"""Siz {topic_config['character']}siz. 4-sinf o'quvchilariga {topic_config['name']} mavzusini o'rgatyapsiz.
        Javoblaringizni {topic_config['icon']} emojisi bilan boshlang.
        Javoblar sodda, tushunarli va qiziqarli bo'lsin, 2-3 jumladan oshmasin.
        O'quvchining savoliga aniq va foydali javob bering."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]
        
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=messages,
            max_tokens=200
        )
        
        ai_text = completion.choices[0].message.content
        logger.info(f"AI javob olindi: {len(ai_text)} chars")
        
        return {'success': True, 'text': ai_text}
        
    except Exception as e:
        logger.error(f"AI xatosi: {str(e)}")
        return {'success': True, 'text': f"{topic_config['icon']} Kechirasiz, hozir javob bera olmayman. Iltimos, keyinroq so'rang."}

def speech_to_text_with_retry(audio_file_path, max_retries=4):
    global current_stt_token
    
    for attempt in range(max_retries):
        try:
            logger.info(f"STT urinish {attempt + 1}/{max_retries}")
            
            if not os.path.exists(audio_file_path):
                return {'error': f"Fayl mavjud emas: {audio_file_path}"}
            
            url = 'https://service.muxlisa.uz/api/v2/stt'
            headers = {'x-api-key': current_stt_token}
            
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            files = {
                'audio': (os.path.basename(audio_file_path), audio_data, 'audio/wav')
            }
            
            response = requests.post(url, headers=headers, files=files, timeout=30)
            logger.info(f"STT status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'text' in result and result['text']:
                    return {'success': True, 'text': result['text']}
                return {'error': "STT dan matn olinmadi"}
            elif response.status_code == 402:
                get_next_stt_token()
                continue
            else:
                return {'error': f"STT xatosi: {response.status_code}"}
        except Exception as e:
            logger.error(f"STT urinish {attempt + 1} xatosi: {str(e)}")
            if attempt == max_retries - 1:
                return {'error': str(e)}
            continue
    
    return {'error': "Barcha tokenlar bilan urinish muvaffaqiyatsiz tugadi"}

def text_to_speech_with_retry(text, max_retries=4):
    global current_tts_token
    
    for attempt in range(max_retries):
        try:
            logger.info(f"TTS urinish {attempt + 1}/{max_retries}")
            
            url = 'https://service.muxlisa.uz/api/v2/tts'
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': current_tts_token
            }
            
            payload = json.dumps({"text": text, "speaker": 0})
            
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            logger.info(f"TTS status: {response.status_code}")
            
            if response.status_code == 200:
                audio_filename = f"response_{uuid.uuid4().hex}.mp3"
                audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
                
                with open(audio_path, 'wb') as f:
                    f.write(response.content)
                
                return {'success': True, 'url': f"/static/audio/{audio_filename}"}
            elif response.status_code == 402:
                get_next_tts_token()
                continue
            else:
                return {'error': f"TTS xatosi: {response.status_code}"}
        except Exception as e:
            logger.error(f"TTS urinish {attempt + 1} xatosi: {str(e)}")
            if attempt == max_retries - 1:
                return {'error': str(e)}
            continue
    
    return {'error': "Barcha tokenlar bilan urinish muvaffaqiyatsiz tugadi"}

def get_ai_response(user_question, grade='1', part='I'):
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(api_key=HUGGINGFACE_API_KEY, timeout=60)
        
        system_prompt = f"""Siz {grade}-sinf o'quvchilariga dars berayotgan astronomiya va tabiy fanlar o'qituvchisisiz.
        O'quvchi {grade}-sinf {part}-qismda o'qiyapti.
        Javoblaringizni sodda, tushunarli va qiziqarli qilib bering.
        {grade}-sinf o'quvchisiga mos tilda gapiring.
        Javoblar 2-3 jumladan oshmasin, bolalar diqqatini saqlash uchun qisqa bo'lsin."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]
        
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=messages,
            max_tokens=200
        )
        
        ai_text = completion.choices[0].message.content
        logger.info(f"AI javob olindi: {len(ai_text)} chars")
        
        return {'success': True, 'text': ai_text}
        
    except Exception as e:
        logger.error(f"AI xatosi: {str(e)}")
        return {'success': True, 'text': "Kechirasiz, hozir javob bera olmayman. Iltimos, keyinroq so'rang."}

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🚀 SERVER ISHGA TUSHDI")
    print("=" * 80)
    print(f"📍 Manzil: http://localhost:5000")
    print("=" * 80)
    print("\n📚 4-SINF 2-QISM MAVZULARI:")
    for topic in GRADE4_PART2_TOPICS:
        print(f"  {topic['icon']} {topic['name']} - {topic['character']}")
    print("\n" + "=" * 80 + "\n")
    
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, host='0.0.0.0', port=port)
