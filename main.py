import warnings
warnings.filterwarnings('ignore')
import os
import pickle
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="Course Recommender", page_icon="🎓", layout="wide")

# --- LOAD AUTH CONFIG ---
def load_config():
    if not os.path.exists('config.yaml'):
        default_config = {
            'credentials': {'usernames': {}},
            'cookie': {'expiry_days': 30, 'key': 'a_very_long_and_secure_signature_key_for_jwt_32_bytes', 'name': 'course_recommender_cookie'}
        }
        with open('config.yaml', 'w') as file:
            yaml.dump(default_config, file)
        return default_config
    try:
        with open('config.yaml') as file:
            data = yaml.load(file, Loader=SafeLoader)
            if not data or 'credentials' not in data:
                 return {'credentials': {'usernames': {}}, 'cookie': {'expiry_days': 30, 'key': 'a_very_long_and_secure_signature_key_for_jwt_32_bytes', 'name': 'course_recommender_cookie'}}
            return data
    except:
        return {'credentials': {'usernames': {}}, 'cookie': {'expiry_days': 30, 'key': 'a_very_long_and_secure_signature_key_for_jwt_32_bytes', 'name': 'course_recommender_cookie'}}

def save_config(config):
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

# Initial load
config = load_config()

# --- AUTHENTICATOR SETUP ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- SESSION STATE INITIALIZATION ---
if 'view' not in st.session_state:
    st.session_state['view'] = 'register'
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'logged_in_view' not in st.session_state:
    st.session_state['logged_in_view'] = 'dashboard'

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: white;
    }
    .course-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .course-card:hover {
        transform: translateY(-5px);
        border-color: #00d2ff;
    }
    h1, h2, h3, h4, p, span, label, .stMarkdown {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(45deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 0;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION FLOW ---
# If user is not authenticated, show Register or Login
if not st.session_state.get("authentication_status"):
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.image("https://img.icons8.com/clouds/200/000000/education.png")
        st.title("Knowledge Recommender")
        st.write("Register to start your personalized learning journey.")

    with col_r:
        if st.session_state['view'] == 'register':
            with st.container(border=True):
                st.subheader("Create Account")
                new_username = st.text_input("Username", key="reg_user")
                new_password = st.text_input("Password", type="password", key="reg_pass")
                confirm_password = st.text_input("Re-enter Password", type="password", key="reg_conf")

                if st.button("Create Account"):
                    if not new_username or not new_password:
                        st.error("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif new_username in config['credentials']['usernames']:
                        st.error("Username already exists")
                    else:
                        # Hash password
                        hashed_password = stauth.Hasher.hash(new_password)
                        
                        # Add to config
                        config['credentials']['usernames'][new_username] = {
                            'email': new_username + "@example.com",
                            'name': new_username,
                            'password': hashed_password
                        }
                        save_config(config)
                        
                        st.success("✨ Account created successfully!")
                        st.info("Please login with your new credentials.")
                        
                        # FORCE redirect to login view
                        st.session_state['view'] = 'login'
                        st.rerun()
                
                if st.button("Already have an account? Login"):
                    st.session_state['view'] = 'login'
                    st.rerun()

        else: # view == 'login'
            st.subheader("Login")
            # Clear authentication status to ensure they must log in
            authenticator.login('main')
            
            if st.session_state["authentication_status"] == False:
                st.error('❌ Invalid credentials')
            elif st.session_state["authentication_status"] == None:
                st.info('👋 Please log in to continue.')
            
            if st.button("New user? Create an account"):
                st.session_state['view'] = 'register'
                st.rerun()

# --- LOGGED IN CONTENT ---
if st.session_state.get("authentication_status"):
    # Header Area
    col_title, col_nav, col_out = st.columns([4, 1.2, 0.8])
    
    with col_title:
        st.markdown("<h2>🎓 Welcome, " + st.session_state['name'] + "</h2>", unsafe_allow_html=True)
    
    with col_nav:
        if st.session_state['logged_in_view'] == 'dashboard':
            if st.button("📜 View Search History"):
                st.session_state['logged_in_view'] = 'history'
                st.rerun()
        else:
            if st.button("🏠 Back to Dashboard"):
                st.session_state['logged_in_view'] = 'dashboard'
                st.rerun()
            
    with col_out:
        authenticator.logout('Logout', 'main')

    st.write("---")

    # --- VIEW: HISTORY ---
    if st.session_state['logged_in_view'] == 'history':
        st.title("🕒 Your Search History")
        if not st.session_state['history']:
            st.info("No history yet.")
        else:
            for item in reversed(st.session_state['history']):
                st.markdown("""
                    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #00d2ff;">
                        <b>""" + item + """</b>
                    </div>
                """, unsafe_allow_html=True)
            
            if st.button("🗑️ Clear History"):
                st.session_state['history'] = []
                st.rerun()

    # --- VIEW: DASHBOARD ---
    else:
        @st.cache_resource
        def load_data():
            try:
                courses = pickle.load(open('models/courses.pkl', 'rb'))
                sim = pickle.load(open('models/similarity.pkl', 'rb'))
                return courses, sim
            except:
                return None, None

        courses_list, similarity = load_data()
        if courses_list is None:
            st.error("Data files missing.")
            st.stop()

        def recommend(course):
            idx = courses_list[courses_list['course_name'] == course].index[0]
            distances = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])
            return [courses_list.iloc[i[0]].course_name for i in distances[1:7]]

        st.markdown("### 🔍 Course Search")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            course_names = courses_list['course_name'].values
            selected_course = st.selectbox("Search for a course:", course_names)

        with search_col2:
            st.write("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button('✨ Recommend'):
                if selected_course not in st.session_state['history']:
                    st.session_state['history'].append(selected_course)
                st.session_state['recommended'] = recommend(selected_course)

        if 'recommended' in st.session_state:
            st.write("### 🎯 Recommendations")
            recs = st.session_state['recommended']
            cols = st.columns(3)
            for idx, course in enumerate(recs):
                with cols[idx % 3]:
                    st.markdown("""
                        <div class="course-card">
                            <div>
                                <h4 style="font-size: 1rem;">""" + course + """</h4>
                            </div>
                            <div style="font-weight: bold; color: #00d2ff; font-size: 0.8rem; margin-top: 10px;">
                                Match Rank: #""" + str(idx+1) + """
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <div style="text-align: center; margin-top: 5rem; padding: 2rem; border-top: 1px solid rgba(255,255,255,0.1);">
            <p style="opacity: 0.5; font-size: 0.8rem;">Course Recommendation System 2026</p>
        </div>
    """, unsafe_allow_html=True)
