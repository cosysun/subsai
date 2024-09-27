#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Subs AI Web User Interface (webui)
"""

import importlib
import json
import mimetypes
import os.path
import sys
import tempfile
from base64 import b64encode
from pathlib import Path

import pandas as pd
import streamlit as st
from pysubs2.time import ms_to_str, make_time
from streamlit import runtime
from streamlit_player import st_player
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder, DataReturnMode

from subsai import SubsAI, Tools
from subsai.configs import ADVANCED_TOOLS_CONFIGS
from subsai.models.YoutubeDownloader import download_youtube_video
from subsai.utils import available_subs_formats
from streamlit.web import cli as stcli

__author__ = "abdeladim-s"
__contact__ = "https://github.com/abdeladim-s"
__copyright__ = "Copyright 2023,"
__deprecated__ = False
__license__ = "GPLv3"
__version__ = importlib.metadata.version('subsai')

subs_ai = SubsAI()
tools = Tools()


def _get_key(model_name: str, config_name: str) -> str:
    """
    a simple helper method to generate unique key for configs UI

    :param model_name: name of the model
    :param config_name: configuration key
    :return: str key
    """
    return model_name + '-' + config_name


def _config_ui(config_name: str, key: str, config: dict):
    """
    helper func that returns the config UI based on the type of the config

    :param config_name: the name of the model
    :param key: the key to set for the config ui
    :param config: configuration object

    :return: config UI streamlit objects
    """
    if config['type'] == str:
        return st.text_input(config_name, help=config['description'], key=key, value=config['default'])
    elif config['type'] == list:
        return st.selectbox(config_name, config['options'], index=config['options'].index(config['default']),
                            help=config['description'], key=key)
    elif config['type'] == float or config['type'] == int:
        if config['default'] is None:
            return st.text_input(config_name, help=config['description'], key=key, value=config['default'])
        return st.number_input(label=config_name, help=config['description'], key=key, value=config['default'])
    elif config['type'] == bool:
        return st.checkbox(label=config_name, value=config['default'], help=config['description'], key=key)
    else:
        print(f'Warning: {config_name} does not have a supported UI')
        pass


def _generate_config_ui(model_name, config_schema):
    """
    Loops through configuration dict object and generates the configuration UIs
    :param model_name:
    :param config_schema:
    :return: Config UIs
    """
    for config_name in config_schema:
        config = config_schema[config_name]
        key = _get_key(model_name, config_name)
        _config_ui(config_name, key, config)


def _get_config_from_session_state(model_name: str, config_schema: dict, notification_placeholder) -> dict:
    """
    Helper function to get configuration dict from the generated config UIs

    :param model_name: name of the model
    :param config_schema: configuration schema
    :param notification_placeholder: notification placeholder streamlit object in case of errors

    :return: dict of configs
    """
    model_config = {}
    for config_name in config_schema:
        key = _get_key(model_name, config_name)
        try:
            value = st.session_state[key]
            if config_schema[config_name]['type'] == str:
                if value == 'None' or value == '':
                    value = None
            elif config_schema[config_name]['type'] == float:
                if value == 'None' or value == '':
                    value = None
                else:
                    value = float(value)
            elif config_schema[config_name]['type'] == int:
                if value == 'None' or value == '':
                    value = None
                else:
                    value = int(value)

            model_config[config_name] = value
        except KeyError as e:
            pass
        except Exception as e:
            notification_placeholder.error(f'Problem parsing configs!! \n {e}')
            return
    return model_config


def _vtt_base64(subs_str: str, mime='application/octet-stream'):
    """
    Helper func to return vtt subs as base64 to load them into the video

    :param subs_str: str of the subtitles
    :param mime: mime type

    :return: base64 data
    """
    data = b64encode(subs_str.encode()).decode()
    return f"data:{mime};base64,{data}"


def _media_file_base64(file_path, mime='video/mp4', start_time=0):
    """
    Helper func that returns base64 of the media file

    :param file_path: path of the file
    :param mime: mime type
    :param start_time: start time

    :return: base64 of the media file
    """
    if file_path == '':
        data = ''
        return [{"type": mime, "src": f"data:{mime};base64,{data}#t={start_time}"}]
    with open(file_path, "rb") as media_file:
        data = b64encode(media_file.read()).decode()
        try:
            mime = mimetypes.guess_type(file_path)[0]
        except Exception as e:
            print(f'Unrecognized video type!')

    return [{"type": mime, "src": f"data:{mime};base64,{data}#t={start_time}"}]


@st.cache_resource
def _create_translation_model(model_name: str):
    """
    Returns a translation model and caches it

    :param model_name: name of the model
    :param model_config: configs

    :return: translation model
    """
    translation_model = tools.create_translation_model(model_name)
    return translation_model


@st.cache_data
def _transcribe(file_path, model_name, model_config):
    """
    Returns and caches the generated subtitles

    :param file_path: path of the media file
    :param model_name: name of the model
    :param model_config: configs dict

    :return: `SSAFile` subs
    """
    model = subs_ai.create_model(model_name, model_config=model_config)
    subs = subs_ai.transcribe(media_file=file_path, model=model)
    return subs


def _subs_df(subs):
    """
    helper function that returns a :class:`pandas.DataFrame` from subs object

    :param subs: subtitles

    :return::class:`pandas.DataFrame`
    """
    sub_table = []
    if subs is not None:
        for sub in subs:
            row = [ms_to_str(sub.start, fractions=True), ms_to_str(
                sub.end, fractions=True), sub.text]
            sub_table.append(row)

    df = pd.DataFrame(sub_table, columns=['Start time', 'End time', 'Text'])
    return df


footer = """
<style>
    #page-container {
      position: relative;
    }

    footer{
        visibility:hidden;
    }

    .footer {
    position: relative;
    left: 0;
    top:230px;
    bottom: 0;
    width: 100%;
    background-color: transparent;
    color: #808080; /* theme's text color hex code at 50 percent brightness*/
    text-align: left; /* you can replace 'left' with 'center' or 'right' if you want*/
    }
</style>

<div id="page-container">
    <div class="footer">
    </div>
</div>
"""


def webui() -> None:
    """
    main web UI
    :return: None
    """
    st.set_page_config(page_title='Subs AI',
                       page_icon="🎞️",
                       menu_items={
                           'Get Help': 'https://github.com/abdeladim-s/subsai',
                           'Report a bug': "https://github.com/abdeladim-s/subsai/issues",
                           'About': f"### [Subs AI](https://github.com/abdeladim-s/subsai) \nv{__version__} "
                           f"\n \nLicense: GPLv3"
                       },
                       layout="wide",
                       initial_sidebar_state='auto')

    st.markdown(f"# Subs AI 🎞️")
    st.sidebar.title("Settings")

    if 'transcribed_subs' in st.session_state:
        subs = st.session_state['transcribed_subs']
    else:
        subs = None

    notification_placeholder = st.empty()

    with st.sidebar:
        with st.expander('Media file', expanded=True):
            file_mode = st.selectbox("Select file mode", ['Local path', 'Upload', 'Youtube'], index=0,
                                     help='Use `Local Path` if you are on a local machine, or use `Upload` to '
                                          'upload your files if you are using a remote server')
            if file_mode == 'Local path':
                file_path = st.text_input(
                    'Media file path', help='Absolute path of the media file')
            elif file_mode == 'Upload':
                uploaded_file = st.file_uploader("Choose a media file")
                if uploaded_file is not None:
                    temp_dir = tempfile.TemporaryDirectory()
                    tmp_dir_path = temp_dir.name
                    file_path = os.path.join(tmp_dir_path, uploaded_file.name)
                    file = open(file_path, "wb")
                    file.write(uploaded_file.getbuffer())
                else:
                    file_path = ""
            else:
                file_path = ""
                yt_url = st.text_input(
                    'video url', help="Please input youtube video url!")
                if len(yt_url) != 0 and yt_url not in st.session_state:
                    file_path = download_youtube_video(yt_url)
                    st.session_state[yt_url] = file_path
                elif yt_url in st.session_state:
                    file_path = st.session_state[yt_url]
            st.session_state['file_path'] = file_path

        transcribe_button = st.button('Transcribe', type='primary')
        transcribe_loading_placeholder = st.empty()

    stt_model_name = "openai/whisper"
    if transcribe_button:
        config_schema = SubsAI.config_schema(stt_model_name)
        model_config = _get_config_from_session_state(
            stt_model_name, config_schema, notification_placeholder)
        subs = _transcribe(file_path, stt_model_name, model_config)
        st.session_state['transcribed_subs'] = subs
        transcribe_loading_placeholder.success('Done!', icon="✅")

    with st.expander('Post Processing Tools', expanded=False):
        advanced_tool = st.selectbox('Advanced tools', options=['', *list(ADVANCED_TOOLS_CONFIGS.keys())],
                                     help='some post processing tools')

        if advanced_tool == 'google-translate':
            target_language = st.selectbox('Target language',
                                           options=("ja", "zh-CN", "en"))
            try:
                b1, b2 = st.columns([1, 1])
                with b1:
                    submitted = st.button("Translate")
                    if submitted:
                        if 'transcribed_subs' not in st.session_state:
                            st.error('No subtitles to translate')
                        else:
                            with st.spinner("Processing (This may take a while) ..."):
                                translated_subs = tools.google_translate(subs=subs,
                                                                         source_language='auto',
                                                                         target_language=target_language)
                                st.session_state['original_subs'] = st.session_state['transcribed_subs']
                                st.session_state['transcribed_subs'] = translated_subs
                            notification_placeholder.success(
                                'Success!', icon="✅")
                with b2:
                    reload_transcribed_subs = st.button(
                        'Reload Original subtitles')
                    if reload_transcribed_subs:
                        if 'original_subs' in st.session_state:
                            st.session_state['transcribed_subs'] = st.session_state['original_subs']
                        else:
                            st.error('Original subs are already loaded')
            except Exception as e:
                st.error("dont find subtitles, google translator failed!")
                print(f"翻译失败: {e}")

    subs_column, video_column = st.columns([4, 3])

    with subs_column:
        if 'transcribed_subs' in st.session_state:
            df = _subs_df(st.session_state['transcribed_subs'])
        else:
            df = pd.DataFrame()
        gb = GridOptionsBuilder()
        # customize gridOptions
        gb.configure_default_column(
            groupable=False, value=True, enableRowGroup=True, editable=True)

        gb.configure_column("Start time", type=["customDateTimeFormat"],
                            custom_format_string='HH:mm:ss', pivot=False, editable=False)
        gb.configure_column("End time", type=["customDateTimeFormat"],
                            custom_format_string='HH:mm:ss', pivot=False, editable=False)
        gb.configure_column("Text", type=["textColumn"], editable=True)

        gb.configure_grid_options(
            domLayout='normal', allowContextMenuWithControlKey=False, undoRedoCellEditing=True, )
        gb.configure_selection(use_checkbox=False)

        gridOptions = gb.build()

        returned_grid = AgGrid(df,
                               height=500,
                               width='100%',
                               fit_columns_on_grid_load=True,
                               theme="alpine",
                               update_on=['rowValueChanged'],
                               update_mode=GridUpdateMode.VALUE_CHANGED,
                               data_return_mode=DataReturnMode.AS_INPUT,
                               try_to_convert_back_to_original_types=False,
                               gridOptions=gridOptions)

        # change subs
        if len(returned_grid['selected_rows']) != 0:
            st.session_state['selected_row_idx'] = returned_grid.selected_rows[0]['_selectedRowNodeInfo'][
                'nodeRowIndex']
            try:
                selected_row = returned_grid['selected_rows'][0]
                changed_sub_index = selected_row['_selectedRowNodeInfo']['nodeRowIndex']
                changed_sub_text = selected_row['Text']
                subs = st.session_state['transcribed_subs']
                subs[changed_sub_index].text = changed_sub_text
                st.session_state['transcribed_subs'] = subs
            except Exception as e:
                print(e)
                notification_placeholder.error('Error parsing subs!', icon="🚨")

    with video_column:
        if subs is not None:
            subs = st.session_state['transcribed_subs']
            vtt_subs = _vtt_base64(subs.to_string(format_='vtt'))
        else:
            vtt_subs = ""

        options = {
            "playback_rate": 1,
            'config': {
                'file': {
                    'attributes': {
                        'crossOrigin': 'true'
                    },
                    'tracks': [
                        {'kind': 'subtitles',
                         'src': vtt_subs,
                         'srcLang': 'default', 'default': 'true'},
                    ]
                }}
        }

        if 'file_path' in st.session_state and st.session_state['file_path'] != '':
            if os.path.getsize(file_path) > st.web.server.server.get_max_message_size_bytes():
                print(f"Media file cannot be previewed: size exceeds the message size limit of {
                      st.web.server.server.get_max_message_size_bytes() / int(1e6):.2f} MB.")
                st.info(f'Media file cannot be previewed: size exceeds the size limit of {st.web.server.server.get_max_message_size_bytes() / int(1e6):.2f} MB.'
                        f' But you can try to run the transcription as usual.', icon="🚨")
                st.info(
                    f' You can increase the limit by running: subsai-webui --server.maxMessageSize Your_desired_size_limit_in_MB')
                st.info(
                    f"If it didn't work, please use the command line interface instead.")
            else:
                event = st_player(_media_file_base64(
                    st.session_state['file_path']), **options, height=500, key="player")

    with st.expander('Export subtitles file'):
        media_file = Path(file_path)
        export_format = st.radio(
            "Format",
            available_subs_formats())
        export_filename = st.text_input('Filename', value=media_file.stem)
        if export_format == '.sub':
            fps = st.number_input(
                'Framerate', help='Framerate must be specified when writing MicroDVD')
        else:
            fps = None
        submitted = st.button("Export")
        if submitted:
            try:
                subs = st.session_state['transcribed_subs']
                exported_file = media_file.parent / \
                    (export_filename + export_format)
                subs.save(exported_file, fps=fps)
                st.success(f'Exported file to {exported_file}', icon="✅")
                with open(exported_file, 'r', encoding='utf-8') as f:
                    st.download_button(
                        'Download', f, file_name=export_filename + export_format)
            except Exception as e:
                st.error(
                    "Maybe you forgot to run the transcription! Please transcribe a media file first to export its transcription!")
                st.error("See the terminal for more info!")
                print(e)

    with st.expander('Merge subtitles with video'):
        media_file = Path(file_path)
        exported_video_filename = st.text_input(
            'Filename', value=f"{media_file.stem}-subs-merged", key='merged_video_out_file')
        submitted = st.button("Merge", key='merged_video_export_btn')
        if submitted:
            try:
                subs = st.session_state['transcribed_subs']
                # subs = tools.merge_subs(
                #     st.session_state['transcribed_subs'], st.session_state['original_subs'])
                exported_file_path = tools.merge_subs_with_video2(
                    subs, str(media_file.resolve()), exported_video_filename)
                st.success(f'Exported file to {exported_file_path}', icon="✅")
                with open(exported_file_path, 'rb') as f:
                    st.download_button('Download', f, file_name=f"{
                                       exported_video_filename}{media_file.suffix}")
            except Exception as e:
                st.error("Something went wrong!")
                st.error("See the terminal for more info!")
                print(e)

    st.markdown(footer, unsafe_allow_html=True)


def run():
    if runtime.exists():
        webui()
    else:
        sys.argv = ["streamlit", "run", __file__,
                    "--theme.base", "dark"] + sys.argv
        sys.exit(stcli.main())


if __name__ == '__main__':
    run()
