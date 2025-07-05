import streamlit as st
import requests
import os
from dotenv import load_dotenv

st.set_page_config(layout="wide", page_title="Kokoro TTS Webapp")

st.title("🗣️ TTS demo and mixing with Kokoro V1")

st.markdown(
    """
    _This is a demo application. This is only intended for testing, so that kids can try out the new Kokoro model and we can get feedback._
    """
)
st.markdown("")

text_input = st.text_area("Enter text here:", "Hey there! This is a demonstration of mixing voices for text-to-speech functionality. Try blending two or more voices!", height=150)

# The full list of available voices provided by kokoro. Reference : https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
available_voices = [
    'af_heart', 'af_alloy', 'af_aoede', 'af_bella', 'af_jessica', 'af_kore', 'af_nicole', 'af_nova', 'af_river', 'af_sarah', 'af_sky',
    'am_adam', 'am_echo', 'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx', 'am_puck', 'am_santa',
    'bf_alice', 'bf_emma', 'bf_isabella', 'bf_lily',
    'bm_daniel', 'bm_fable', 'bm_george', 'bm_lewis',
    'jf_alpha', 'jf_gongitsune', 'jf_nezumi', 'jf_tebukuro',
    'jm_kumo',
    'zf_xiaobei', 'zf_xiaoni', 'zf_xiaoxiao', 'zf_xiaoyi',
    'zm_yunjian', 'zm_yunxi', 'zm_yunxia', 'zm_yunyang',
    'ef_dora', 'em_alex', 'em_santa',
    'ff_siwis',
    'hf_alpha', 'hf_beta', 'hm_omega', 'hm_psi',
    'if_sara', 'im_nicola',
    'pf_dora', 'pm_alex', 'pm_santa'
]

st.subheader("Voice Selection & Mixing")

if 'voice_selections' not in st.session_state:
    default_voice_during_init = 'af_bella'
    st.session_state.voice_selections = [{'voice': default_voice_during_init, 'weight': 1.0}]

def add_voice_selection():
    st.session_state.voice_selections.append({'voice': available_voices[0], 'weight': 1.0})

def remove_voice_selection(index):
    #Ensure minimum one voice selection to prevent an empty state
    if len(st.session_state.voice_selections) > 1:
        st.session_state.voice_selections.pop(index)
    else:
        st.warning("You must have at least one voice selected.")

with st.container(border=True):
    for i, selection in enumerate(st.session_state.voice_selections):
        cols = st.columns([0.6, 0.3, 0.1]) # columns width percentages for voice,weight and trash
        
        with cols[0]: # I'm using indexes as indentifiers
            current_voice_index = available_voices.index(selection['voice']) if selection['voice'] in available_voices else 0
            selected_voice = st.selectbox(f"Voice {i+1}", available_voices, index=current_voice_index, key=f"voice_select_{i}")
            st.session_state.voice_selections[i]['voice'] = selected_voice

        with cols[1]:
            weight = st.number_input(
                f"Weight {i+1}",
                min_value=0.01,  
                max_value=1.0,  
                value=selection['weight'],
                step=0.01,      
                key=f"voice_weight_{i}"
            )
            st.session_state.voice_selections[i]['weight'] = weight
        
        with cols[2]:
            st.write("") 
            st.write("")
            if st.button(f"🗑️", key=f"remove_voice_{i}", help="Remove this voice selection", use_container_width=True):
                remove_voice_selection(i)
                st.rerun() #Update UI after removal

    st.button("➕  Add Another Voice", on_click=add_voice_selection, use_container_width=True)

total_weight = sum(s['weight'] for s in st.session_state.voice_selections)
if not (0.999 <= total_weight <= 1.001): #thanks to python's floating point calculations :skull
    st.warning(f"**Warning:** The sum of all voice weights must be 1.0 (currently: {total_weight:.2f}). Please adjust the weights.")
else:
    st.success(f"✅   Voice weights sum to {total_weight:.2f}. Ready to generate!")


voice_param = ""
if st.session_state.voice_selections:
    active_selections = [s for s in st.session_state.voice_selections if s['weight'] > 0]

    if len(active_selections) == 1: #If only one voice, can't specify mixing, some weird API format
        single_selection = active_selections[0]
        
        if single_selection['weight'] == 1.0:
            voice_param = single_selection['voice']
        else:
            voice_param = f"{single_selection['voice']}({single_selection['weight']})"

    elif len(active_selections) > 1: #This uses mixing format
        voice_parts = []
        for selection in active_selections:
            voice_parts.append(f"{selection['voice']}({selection['weight']})")
        voice_param = "+".join(voice_parts)
    else:
        st.warning("Please ensure at least one voice has a weight greater than 0 to generate speech.")
        voice_param = "" 

else:
    st.warning("Please select at least one voice to generate speech.")


st.markdown("---") 

if st.button("Generate Speech", use_container_width=True):
    if not voice_param:
        st.warning("Please ensure at least one voice has a weight greater than 0 to generate speech.")
        st.stop() #stop if no valid voice_param

    if not (0.999 <= total_weight <= 1.001): #Thanks to python's floating point calculations :skull:
        st.warning("Please correct the voice weights. The sum must be 1.0 before generating speech.")
        st.stop() #stop if weights not valid

    if text_input: 
        st.info("Generating audio, please wait. May take some time for longer texts or complex voice mixes.")
        try:
            load_dotenv()
            KOKORO_API_URL = os.getenv("KOKORO_API_URL")
            
            payload = {
                "model": "kokoro",
                "input": text_input,
                "voice": voice_param, 
                "response_format": "mp3", # Supported formats: 'mp3', 'wav', 'opus', 'flac', 'm4a', 'pcm'
                "speed": 1.0 
            }
            
            headers = {
                "Content-Type": "application/json"
            }

            print(f"DEBUG: Attempting to connect to API in the .env")
            print(f"DEBUG: Request Payload: {payload}")

            response = requests.post(KOKORO_API_URL, json=payload, headers=headers)
            response.raise_for_status() 
            audio_data = response.content 
            
            st.success("Audio generated successfully!")
            st.audio(audio_data, format="audio/mp3") 

            st.download_button(
                label="Download Audio",
                data=audio_data,
                file_name="generated_speech.mp3",
                mime="audio/mp3"
            )

        except requests.exceptions.ConnectionError as e:
            st.error(f"**Error:** Could not connect to Kokoro container instance. Azure sucks.")
            st.error(f"Detailed Connection Error: `{e}`") 
        except requests.exceptions.HTTPError as e:
            st.error(f"**API Error:** Kokoro-FastAPI returned an error status.")
            st.error(f"Status Code: `{response.status_code}`")
            st.error(f"Response content: `{response.text}`") 
            st.error(f"Detailed HTTP Error: `{e}`")
            st.warning("Please verify the entered text and selected voices. Some voice combinations or text inputs might not be valid for the model.")
        except requests.exceptions.RequestException as e:
            st.error(f"**Some General Error Encountered:** An unexpected error occurred during the request.")
            st.error(f"Detailed Error: `{e}`")
            if 'response' in locals() and response is not None:
                st.error(f"API Response content: `{response.text}`")
            st.warning("Please verify your network connection or try again.")
    else:
        st.warning("Please enter some text to generate speech.")

st.markdown("---") 


st.info(
    """
    **How Voice Mixing Works:** \n
    Select multiple voices using the 'Add Another Voice' button. Each voice can have a 'Weight'.
    The sum of all voice weights **must be 1.0**.

    For example:
    * `af_bella` (Weight 0.3) + `af_sky` (Weight 0.7) will blend Bella at 30% and Sky at 70%.
    * If you select three voices, they could be Weight 0.4, 0.3, 0.3.
    
"""
)


st.info(
    """
    **How to read voice names:** \n
    The first letter of the voice is the language so:
    * `a` for American English
    * `b` for British English
    * `j` for Japanese
    * `m` for Mandarin Chinese
    * `s` for Spanish
    * `f` for French
    * `h` for Hindi
    * `i` for Italian
    * `p` for Brazilian Portuguese

    \nThe second letter of the voice is the gender so:

    * `f` for Female
    * `m` for Male

    \nSo a voice like `af_bella` is a American English Female voice.
    """
)

st.markdown(
    """
    ---
    *Powered by [Kokoro-FastAPI](https://github.com/mebinthattil/Kokoro-FastAPI) and Streamlit.* \n
    *Not self hosted on a pi* 😔
    """
)