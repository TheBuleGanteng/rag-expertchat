import translators as ts
import logging
#from fast_langdetect import detect, detect_multilingual
from langdetect import detect

logger = logging.getLogger('django')

# Leverages google mediapipe for translation. For more information, see: https://ai.google.dev/edge/mediapipe/solutions/text/language_detector#models
def detect_language(input_text):
    logger.debug(f'running detect_language() ... function started and input_text is: { input_text }')

    truncated_text = (input_text[:100] + '...') if len(input_text) > 100 else input_text
    #truncated_text = truncated_text.replace('\n','')
    logger.debug(f'running detect_language() ... '
                f'truncated_text is: {truncated_text}')

    detected_language_code = detect(input_text)
    
    # For some reason, detect() sometimes returns 'ca' when it should return 'en', so correcting for that here
    if detected_language_code == 'ca':
        detected_language_code = 'en'
        logger.warning(f'running detect_language() ... '
                       f'detected_language_code tried returning "ca" '
                       f'manually changed to: { detected_language_code }')
    
    logger.debug(f'running detect_language() ... '
                f'detected_language_code is: { detected_language_code }')
                #f'detected_language_code_prob is: { detected_language_code_prob }')
    return detected_language_code


def translate(input_text, from_language, to_language):
    logger.debug(f'running aichat_chat/helpers/translate.py ... '
                f'input_text is: { input_text }, '
                f'from_language is: { from_language }, '
                f'to_language is { to_language }')

    # Translate and return the translated text
    output_text = ts.translate_text(
        query_text=input_text, 
        from_language=from_language, 
        to_language=to_language, 
        translator='google'
    )
    return output_text



# Predefined list of Google Translate supported languages
supported_languages_full = {
    'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic',
    'hy': 'Armenian', 'az': 'Azerbaijani', 'eu': 'Basque', 'be': 'Belarusian',
    'bn': 'Bengali', 'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan',
    'ceb': 'Cebuano', 'ny': 'Chichewa', 'zh-CN': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)', 'co': 'Corsican', 'hr': 'Croatian',
    'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English', 'eo': 'Esperanto',
    'et': 'Estonian', 'tl': 'Filipino', 'fi': 'Finnish', 'fr': 'French',
    'fy': 'Frisian', 'gl': 'Galician', 'ka': 'Georgian', 'de': 'German',
    'el': 'Greek', 'gu': 'Gujarati', 'ht': 'Haitian Creole', 'ha': 'Hausa',
    'haw': 'Hawaiian', 'iw': 'Hebrew', 'hi': 'Hindi', 'hmn': 'Hmong', 'hu': 'Hungarian',
    'is': 'Icelandic', 'ig': 'Igbo', 'id': 'Indonesian', 'ga': 'Irish', 'it': 'Italian',
    'ja': 'Japanese', 'jw': 'Javanese', 'kn': 'Kannada', 'kk': 'Kazakh', 'km': 'Khmer',
    'rw': 'Kinyarwanda', 'ko': 'Korean', 'ku': 'Kurdish (Kurmanji)', 'ky': 'Kyrgyz',
    'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian', 'lt': 'Lithuanian', 'lb': 'Luxembourgish',
    'mk': 'Macedonian', 'mg': 'Malagasy', 'ms': 'Malay', 'ml': 'Malayalam',
    'mt': 'Maltese', 'mi': 'Maori', 'mr': 'Marathi', 'mn': 'Mongolian', 'my': 'Myanmar (Burmese)',
    'ne': 'Nepali', 'no': 'Norwegian', 'or': 'Odia', 'ps': 'Pashto', 'fa': 'Persian',
    'pl': 'Polish', 'pt': 'Portuguese', 'pa': 'Punjabi', 'ro': 'Romanian', 'ru': 'Russian',
    'sm': 'Samoan', 'gd': 'Scots Gaelic', 'sr': 'Serbian', 'st': 'Sesotho', 'sn': 'Shona',
    'sd': 'Sindhi', 'si': 'Sinhala', 'sk': 'Slovak', 'sl': 'Slovenian', 'so': 'Somali',
    'es': 'Spanish', 'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish', 'tg': 'Tajik',
    'ta': 'Tamil', 'tt': 'Tatar', 'te': 'Telugu', 'th': 'Thai', 'tr': 'Turkish',
    'tk': 'Turkmen', 'uk': 'Ukrainian', 'ur': 'Urdu', 'ug': 'Uyghur', 'uz': 'Uzbek',
    'vi': 'Vietnamese', 'cy': 'Welsh', 'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba',
    'zu': 'Zulu'
}


supported_languages_selected = {
    'en': {
        'name': 'English',
        'translated_name': 'English'
    },
    'zh': {
        'name': '简体中文 (Chinese Simplified)',
        'translated_name': '简体中文'
    },
    'ja': {
        'name': '日本語 (Japanese)',
        'translated_name': '日本語'
    },
    'ko': {
        'name': '한국어 (Korean)',
        'translated_name': '한국어'
    },
    'es': {
        'name': 'Español (Spanish)',
        'translated_name': 'español'
    },
    'id': {
        'name': 'B. Indonesia (Indonesian)',
        'translated_name': 'Bahasa Indonesia'
    },
}
