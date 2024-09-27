#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configurations file
"""

from ffsubsync.constants import DEFAULT_MAX_SUBTITLE_SECONDS, DEFAULT_START_SECONDS, DEFAULT_MAX_OFFSET_SECONDS, \
    DEFAULT_APPLY_OFFSET_SECONDS, DEFAULT_FRAME_RATE, DEFAULT_VAD

from subsai.models.faster_whisper_model import FasterWhisperModel
from subsai.models.hugging_face_model import HuggingFaceModel
from subsai.models.whisperX_model import WhisperXModel
from subsai.models.whisper_model import WhisperModel
from subsai.models.whisper_timestamped_model import WhisperTimeStamped
from subsai.models.whispercpp_model import WhisperCppModel
from subsai.utils import get_available_devices, available_translation_models
from subsai.models.stable_ts_model import StableTsModel
from subsai.models.whisper_api_model import WhisperAPIModel

AVAILABLE_MODELS = {
    'openai/whisper': {
        'class': WhisperModel,
        'description': 'Whisper is a general-purpose speech recognition model. It is trained on a large dataset of '
                       'diverse audio and is also a multi-task model that can perform multilingual speech recognition '
                       'as well as speech translation and language identification.',
        'url': 'https://github.com/openai/whisper',
        'config_schema': WhisperModel.config_schema,
    },
    'linto-ai/whisper-timestamped': {
        'class': WhisperTimeStamped,
        'description': 'Multilingual Automatic Speech Recognition with word-level timestamps and confidence.',
        'url': 'https://github.com/linto-ai/whisper-timestamped',
        'config_schema': WhisperTimeStamped.config_schema,
    },
    'ggerganov/whisper.cpp': {
        'class': WhisperCppModel,
        'description': 'High-performance inference of OpenAI\'s Whisper automatic speech recognition (ASR) model\n'
                       '* Plain C/C++ implementation without dependencies\n'
                       '* Runs on the CPU\n',
        'url': 'https://github.com/ggerganov/whisper.cpp\nhttps://github.com/abdeladim-s/pywhispercpp',
        'config_schema': WhisperCppModel.config_schema,
    },
    'guillaumekln/faster-whisper': {
        'class': FasterWhisperModel,
        'description': '**faster-whisper** is a reimplementation of OpenAI\'s Whisper model using '
                       '[CTranslate2](https://github.com/OpenNMT/CTranslate2/), which is a fast inference engine for '
                       'Transformer models.\n'
                       'This implementation is up to 4 times faster than [openai/whisper]( '
                       'https://github.com/openai/whisper) for the same accuracy while using less memory. The '
                       'efficiency can be further improved with 8-bit quantization on both CPU and GPU.',
        'url': 'https://github.com/guillaumekln/faster-whisper',
        'config_schema': FasterWhisperModel.config_schema,
    },
    'm-bain/whisperX': {
        'class': WhisperXModel,
        'description': """**whisperX** is a fast automatic speech recognition (70x realtime with large-v2) with word-level timestamps and speaker diarization.""",
        'url': 'https://github.com/m-bain/whisperX',
        'config_schema': WhisperXModel.config_schema,
    },
    'jianfch/stable-ts': {
        'class': StableTsModel,
        'description': '**Stabilizing Timestamps for Whisper** This library modifies [Whisper](https://github.com/openai/whisper) to produce more reliable timestamps and extends its functionality.',
        'url': 'https://github.com/jianfch/stable-ts',
        'config_schema': StableTsModel.config_schema,
    },
    'API/openai/whisper': {
        'class': WhisperAPIModel,
        'description': 'API for the OpenAI large-v2 Whisper model, requires an API key.',
        'url': 'https://platform.openai.com/docs/guides/speech-to-text',
        'config_schema': WhisperAPIModel.config_schema,
    },
    'HuggingFace': {
        'class': HuggingFaceModel,
        'description': 'Hugging Face implementation of Whisper. '
                       'Any speech recognition pretrained model from the Hugging Face hub can be used as well',
        'url': 'https://huggingface.co/tasks/automatic-speech-recognition',
        'config_schema': HuggingFaceModel.config_schema,
    },
}

BASIC_TOOLS_CONFIGS = {
    'set time': {
        'description': 'Set time to a subtitle',
        'config_schema': {
            'h': {
                'type': float,
                'description': "hours: Integer or float values, may be positive or negative",
                'options': None,
                'default': 0,
            },
            'm': {
                'type': float,
                'description': "minutes: Integer or float values, may be positive or negative",
                'options': None,
                'default': 0,
            },
            's': {
                'type': float,
                'description': "seconds: Integer or float values, may be positive or negative",
                'options': None,
                'default': 0,
            },
            'ms': {
                'type': float,
                'description': "milliseconds: Integer or float values, may be positive or negative",
                'options': None,
                'default': 0,
            }
        }
    },
    'shift': {
        'description': 'Shift all subtitles by constant time amount',
        'config_schema': {
            'h': {
                'type': float,
                'description': "hours: Integer or float values, may be positive or negative",
                'options': None,
                'default': 0,
            },
            'm': {
                'type': float,
                'description': "minutes: Integer or float values, may be positive or negative",
                'options': None,
                'default': 0,
            },
            's': {
                'type': float,
                'description': "seconds: Integer or float values, may be positive or negative",
                'options': None,
                'default': 0,
            },
            'ms': {
                'type': float,
                'description': "milliseconds: Integer or float values, may be positive or negative",
                'options': None,
                'default': 0,
            },
            'frames': {
                'type': int,
                'description': "When specified, must be an integer number of frames",
                'options': None,
                'default': None,
            },
            'fps': {
                'type': float,
                'description': "When specified, must be a positive number.",
                'options': None,
                'default': None,
            }

        }
    },
}

ADVANCED_TOOLS_CONFIGS = {
    'google-translate': {
        'languages': ()
    },
}
