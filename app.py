import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. SECURITY SYSTEM FUNCTION
# ==========================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.set_page_config(page_title="MCFC | Login", page_icon="💙")
        st.title("Manchester City MDT | Secure Access")
        password = st.text_input("Enter Access Code", type="password")
        if st.button("Unlock Dashboard"):
            if password == "1234":  
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect code.")
        return False
    return True

# ==========================================
# 2. MAIN APP CONTENT
# =========================================
if check_password():
    # --- MAN CITY THEME CONFIG ---
    CITY_SKY_BLUE, CITY_NAVY, CITY_WHITE = "#6CABDD", "#1C2C5B", "#FFFFFF"

    st.set_page_config(page_title="MCFC | MDT Intelligence Hub", layout="wide")

    st.markdown(f"""
    <style>
        /* 1. FORCE DARK NAVY BACKGROUND */
        .stApp {{ background-color: {CITY_NAVY} !important; }}

        /* 2. UNIVERSAL TEXT BRIGHTNESS */
        .main p, .main li, .main label, .main div[data-testid="stMarkdownContainer"] p, .main .stMarkdown p {{
            color: {CITY_WHITE} !important;
            opacity: 1 !important;
        }}

        /* 3. HEADERS */
        .main h1, .main h2, .main h3 {{ color: {CITY_SKY_BLUE} !important; }}
        .main h4, .main h5, .main h6 {{ color: {CITY_WHITE} !important; }}

        /* 4. METRICS */
        div[data-testid="stMetricLabel"] p {{ color: {CITY_SKY_BLUE} !important; font-weight: 600 !important; }}
        div[data-testid="stMetricValue"] > div {{ color: {CITY_WHITE} !important; }}

        /* 5. TABS */
        button[data-baseweb="tab"] p {{ color: rgba(255, 255, 255, 0.7) !important; }}
        button[data-baseweb="tab"][aria-selected="true"] p {{ color: {CITY_SKY_BLUE} !important; font-weight: bold !important; }}

        /* 6. SIDEBAR */
        [data-testid="stSidebar"] {{ background-color: #121E3E !important; border-right: 1px solid {CITY_SKY_BLUE}; }}
        [data-testid="stSidebar"] .stMarkdown p {{ color: {CITY_WHITE} !important; }}

        /* 7. WIDGET LABELS */
        div[data-testid="stWidgetLabel"] p {{ color: {CITY_WHITE} !important; font-weight: 500 !important; }}

        /* 8. TABLES */
        thead tr th {{ background-color: {CITY_SKY_BLUE} !important; color: {CITY_NAVY} !important; }}
        tbody td {{ background-color: #263868 !important; color: {CITY_WHITE}; }}

        /* 9. CAPTIONS & SECONDARY TEXT (Calculation/Context) */
        .stCaption, .stMarkdown small, .main .stMarkdown div p {{
            color: {CITY_WHITE} !important;
            opacity: 0.9 !important;
        }}

        /* 10. EXPANDERS */
        .streamlit-expanderHeader {{ color: {CITY_WHITE} !important; background-color: #263868 !important; }}
    </style>
    """, unsafe_allow_html=True)

    def robust_clean(df):
        df.columns = df.columns.str.strip().str.upper()
        # Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated()]

        name_col = next((c for c in df.columns if 'NAME' in c), None)
        date_col = next((c for c in df.columns if 'DATE' in c), None)
        if name_col:
            df = df.rename(columns={name_col: 'ATHLETENAME'})
            df['ATHLETENAME'] = df['ATHLETENAME'].astype(str).str.strip().str.title()
        if date_col:
            df = df.rename(columns={date_col: 'DATE'})
            df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce').dt.normalize()
        return df

    def get_unit(pos):
        pos = str(pos).upper().strip()
        if pos in ['ST', 'LW', 'RW']: return 'Attack'
        if pos in ['CAM', 'CM', 'CDM']: return 'Midfield'
        if pos in ['LB', 'CB', 'RB']: return 'Defence'
        return 'Goalkeeper' if pos == 'GK' else 'Other'

    def calc_metrics(df):
        df = df.sort_values(['ATHLETENAME', 'DATE'])
        df['7D_AVG'] = df.groupby('ATHLETENAME')['TOTAL DISTANCE (M)'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
        df['28D_AVG'] = df.groupby('ATHLETENAME')['TOTAL DISTANCE (M)'].transform(lambda x: x.rolling(window=28, min_periods=1).mean())
        df['ACWR'] = (df['7D_AVG'] / df['28D_AVG']).replace([np.inf, -np.inf], 0).fillna(0)
        return df

    if 'master_data' not in st.session_state: st.session_state.master_data = None
    if 'injury_data' not in st.session_state: st.session_state.injury_data = None

    c_logo, c_title = st.columns([1, 8])
    with c_logo: st.image("https://www.mancity.com/dist/images/logos/crest.svg", width=80)
    with c_title: st.title("Manchester City MDT | Decision Support Hub")

    uploaded_files = st.sidebar.file_uploader("Upload MDT Files", accept_multiple_files=True)

    if uploaded_files:
        data_map = {f.name: robust_clean(pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)) for f in uploaded_files}
        gps = next((df for n, df in data_map.items() if 'GPS' in n.upper() or 'INTEGRATED' in n.upper()), None)
        well = next((df for n, df in data_map.items() if 'WELLNESS' in n.upper()), None)
        mins = next((df for n, df in data_map.items() if 'MINUTE' in n.upper() or 'PLAYED' in n.upper()), None)
        inj = next((df for n, df in data_map.items() if 'INJURY' in n.upper() or 'ILLNESS' in n.upper()), None)
        gym = next((df for n, df in data_map.items() if 'GYM' in n.upper()), None)

        if gps is not None:
            gps['UNIT'] = gps['POSITION'].apply(get_unit)
            master = calc_metrics(gps)
            if well is not None:
                master = pd.merge(master, well[['ATHLETENAME', 'DATE', 'SORENESS', 'FATIGUE', 'SLEEPHOURS']], on=['ATHLETENAME', 'DATE'], how='left')
            if mins is not None:
                master = pd.merge(master, mins[['ATHLETENAME', 'DATE', 'MINUTESPLAYED']], on=['ATHLETENAME', 'DATE'], how='left')
                master['MINUTESPLAYED'] = master['MINUTESPLAYED'].fillna(0)

            if gym is not None:
                lift_map = {
                    'Bench Press': {'CHEST_V': 1.0, 'SH_V': 0.5, 'ARM_V': 0.5, 'BACK_V': 0.25, 'LEG_V': 0, 'CORE_V': 0.25},
                    'Deadlift':    {'CHEST_V': 0, 'SH_V': 0.25, 'ARM_V': 0.25, 'BACK_V': 1.0, 'LEG_V': 1.0, 'CORE_V': 0.75},
                    'Power Clean': {'CHEST_V': 0, 'SH_V': 0.5, 'ARM_V': 0.25, 'BACK_V': 0.75, 'LEG_V': 1.0, 'CORE_V': 0.75},
                    'Pull Up':     {'CHEST_V': 0, 'SH_V': 0.25, 'ARM_V': 0.75, 'BACK_V': 1.0, 'LEG_V': 0, 'CORE_V': 0.5},
                    'Squat':       {'CHEST_V': 0, 'SH_V': 0.25, 'ARM_V': 0, 'BACK_V': 0.25, 'LEG_V': 1.0, 'CORE_V': 0.75}
                }
                for muscle in ['CHEST_V', 'SH_V', 'ARM_V', 'BACK_V', 'LEG_V', 'CORE_V']:
                    gym[muscle] = gym.apply(lambda row: row['VOLUME'] * lift_map.get(row['EXERCISE'], {}).get(muscle, 0), axis=1)

                gym_daily = gym.groupby(['ATHLETENAME', 'DATE']).agg({
                    'VOLUME': 'sum', 'LOAD': 'sum', 'RPE': 'mean', 'SETS': 'sum', 'REPS': 'sum',
                    'CHEST_V': 'sum', 'SH_V': 'sum', 'ARM_V': 'sum', 'BACK_V': 'sum', 'LEG_V': 'sum', 'CORE_V': 'sum'
                }).reset_index()

                master = pd.merge(master, gym_daily, on=['ATHLETENAME', 'DATE'], how='left')
                gym_cols = ['VOLUME', 'LOAD', 'CHEST_V', 'SH_V', 'ARM_V', 'BACK_V', 'LEG_V', 'CORE_V']
                master[gym_cols] = master[gym_cols].fillna(0)

            st.session_state.master_data = master

        if inj is not None:
            # THE FIX: robust_clean renames STARTDATE to DATE. We rename it back for the Medical tab.
            if 'DATE' in inj.columns and 'STARTDATE' not in inj.columns:
                inj = inj.rename(columns={'DATE': 'STARTDATE'})

            # Convert both dates correctly
            for col in ['STARTDATE', 'ENDDATE']:
                if col in inj.columns:
                    inj[col] = pd.to_datetime(inj[col], dayfirst=True, errors='coerce').dt.normalize()
            st.session_state.injury_data = inj

    if st.session_state.master_data is not None:
        master = st.session_state.master_data
        player_list = sorted(master['ATHLETENAME'].unique())
        st.sidebar.divider()
        sel_player = st.sidebar.selectbox("Select Athlete for Spotlight", player_list)
        p_df = master[master['ATHLETENAME'] == sel_player].sort_values('DATE')
        t_coach, t_analyst, t_perf, t_med = st.tabs([
            "📋 Coach",
            "📊 Analyst",
            "⚡ Performance (SES & S&C)",
            "🏥 Medical"
        ])
        with t_coach:
            # Change 1: Tabs for view selection with icons
            tab_matrix, tab_spotlight = st.tabs(["📋 Squad Matrix", "🔦 Player Spotlight"])

            with tab_matrix:
                # Change 1: Match Alert above title
                st.markdown("#### ⚽ Fulham (A) in 3 Days")
                # Change 2: Updated Header
                st.markdown("### Current First Team Squad Availability")
                summary_list = []

                for p in player_list:
                    p_rows = master[master['ATHLETENAME'] == p].sort_values('DATE')

                    def get_recent(series, default_val):
                        valid = series.dropna()
                        return valid.iloc[-1] if not valid.empty else default_val

                    latest_gps = p_rows[p_rows['TOTAL DISTANCE (M)'] > 0].iloc[-1] if not p_rows[p_rows['TOTAL DISTANCE (M)'] > 0].empty else p_rows.iloc[-1]

                    sore = get_recent(p_rows['SORENESS'], 5)
                    fat = get_recent(p_rows['FATIGUE'], 5)
                    slp = get_recent(p_rows['SLEEPHOURS'], 8)

                    avail = "❌ Unavailable" if p == "Casey Lewis" else "✅ Fit"

                    raw_well = ((10-float(sore)) + (10-float(fat)) + min(10, (float(slp)/8)*10)) / 3
                    readiness_pct = int(raw_well * 10)
                    if avail == "✅ Fit": readiness_pct = min(100, int(readiness_pct * 1.10))

                    pitch_acwr = latest_gps.get('ACWR', 0)
                    gym_7d = p_rows['VOLUME'].tail(7).mean()
                    gym_28d = p_rows['VOLUME'].tail(28).mean()
                    gym_acwr = gym_7d / gym_28d if (pd.notnull(gym_28d) and gym_28d > 0) else 1.0

                    pitch_stable = 0.8 <= pitch_acwr <= 1.3
                    gym_stable = 0.8 <= gym_acwr <= 1.3

                    if avail == "❌ Unavailable" or pitch_acwr > 1.5 or pitch_acwr < 0.6 or gym_acwr > 1.5 or gym_acwr < 0.6 or readiness_pct < 50:
                        smart_rec = "Immediate Changes"
                    elif pitch_stable and gym_stable and readiness_pct >= 70:
                        smart_rec = "Training Plan Effective"
                    else:
                        smart_rec = "Slightly Alter Training Plan"

                    summary_list.append({
                        "Athlete": p,
                        "Availability": avail,
                        "Pitch ACWR": round(pitch_acwr, 2),
                        "Gym ACWR": round(gym_acwr, 2),
                        "Readiness (%)": readiness_pct,
                        "Total Minutes": int(p_rows['MINUTESPLAYED'].sum()),
                        "Smart Recommendation": smart_rec
                    })

                sdf = pd.DataFrame(summary_list)
                def style_matrix(row):
                    styles = [''] * len(row)
                    styles[1] = 'color: red' if 'Unavailable' in row['Availability'] else 'color: green'
                    if 0.8 <= row['Pitch ACWR'] <= 1.3: styles[2] = 'color: green; font-weight: bold'
                    elif 1.3 < row['Pitch ACWR'] <= 1.5: styles[2] = 'color: #CC9900; font-weight: bold'
                    else: styles[2] = 'color: red; font-weight: bold'
                    if 0.8 <= row['Gym ACWR'] <= 1.3: styles[3] = 'color: green; font-weight: bold'
                    else: styles[3] = 'color: #CC9900; font-weight: bold'
                    if row['Readiness (%)'] >= 75: styles[4] = 'color: green; font-weight: bold'
                    elif 60 <= row['Readiness (%)'] < 75: styles[4] = 'color: #CC9900; font-weight: bold'
                    else: styles[4] = 'color: red; font-weight: bold'
                    if row['Smart Recommendation'] == "Training Plan Effective": styles[6] = 'color: green; font-weight: bold'
                    elif row['Smart Recommendation'] == "Slightly Alter Training Plan": styles[6] = 'color: #CC9900; font-weight: bold'
                    else: styles[6] = 'color: red; font-weight: bold'
                    return styles
                st.dataframe(sdf.style.apply(style_matrix, axis=1).format({'Pitch ACWR': '{:.2f}', 'Gym ACWR': '{:.2f}', 'Readiness (%)': '{0}%'}), use_container_width=True, hide_index=True)

            with tab_spotlight:
                valid_rows = p_df[p_df['TOTAL DISTANCE (M)'] > 0]
                if not valid_rows.empty:
                    curr = valid_rows.iloc[-1]

                    def get_latest_valid(col):
                        v = p_df[col].dropna()
                        return v.iloc[-1] if not v.empty else 5.0

                    sore = get_latest_valid('SORENESS')
                    fat = get_latest_valid('FATIGUE')
                    slp = get_latest_valid('SLEEPHOURS')

                    raw_well = ((10-float(sore)) + (10-float(fat)) + min(10, (float(slp)/8)*10)) / 3
                    readiness = int(raw_well * 10)
                    if sel_player != "Casey Lewis": readiness = min(100, int(readiness * 1.10))

                    # ACWR Logic for Spotlight
                    pitch_acwr = curr.get('ACWR', 0)
                    g_7 = p_df['VOLUME'].tail(7).mean(); g_28 = p_df['VOLUME'].tail(28).mean()
                    gym_acwr = g_7 / g_28 if g_28 > 0 else 1.0

                    p_icon = "✅" if 0.8 <= pitch_acwr <= 1.3 else "⚠️" if 0.6 <= pitch_acwr <= 1.5 else "❌"
                    g_icon = "✅" if 0.8 <= gym_acwr <= 1.3 else "⚠️" if 0.6 <= gym_acwr <= 1.5 else "❌"

                    if readiness >= 75: read_icon, read_stat = "✅", "Great"
                    elif 60 <= readiness < 75: read_icon, read_stat = "⚠️", "Cautious"
                    else: read_icon, read_stat = "❌", "Very Poor"

                    cost_val = (float(fat) + float(sore)) / 2
                    if cost_val <= 5.5: cost_icon, cost_col = "✅", "green"
                    elif 5.5 < cost_val <= 6.5: cost_icon, cost_col = "⚠️", "#CC9900"
                    else: cost_icon, cost_col = "❌", "red"

                    if sel_player == "Casey Lewis" or pitch_acwr > 1.5 or readiness < 50:
                        s_icon, s_txt, s_color, s_role = "❌", "NOT IN SQUAD", "red", "Withdraw from squad."
                    elif 0.8 <= pitch_acwr <= 1.3 and cost_val <= 5.5:
                        s_icon, s_txt, s_color, s_role = "✅", "STARTER", "green", "Physically cleared for high-intensity start."
                    else:
                        s_icon, s_txt, s_color, s_role = "⚠️", "BENCH / SUB", "#CC9900", "Limited impact role."

                    st.header(f"{sel_player} | {curr['POSITION']}")
                    st.markdown(f"<h2 style='color:{s_color};'>{s_icon} Status: {s_txt}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size: 22px; margin-bottom: 5px;'><strong>Tactical Role:</strong> {s_role}</p>", unsafe_allow_html=True)

                    # Change 1: Match Alert below Tactical Role
                    st.markdown("#### ⚽ Fulham (A) in 3 Days")
                    st.divider()

                    # Change 2: Replaced Current ACWR with Pitch and Gym ACWR
                    m1, m2, m3, m4 = st.columns(4)
                    with m1: st.markdown(f"**Pitch ACWR**<br><h2>{pitch_acwr:.2f} {p_icon}</h2>", unsafe_allow_html=True)
                    with m2: st.markdown(f"**Gym ACWR**<br><h2>{gym_acwr:.2f} {g_icon}</h2>", unsafe_allow_html=True)
                    with m3: st.markdown(f"**Readiness Score**<br><h2>{readiness}% {read_icon}</h2>", unsafe_allow_html=True)
                    with m4:
                        u_map = {'Attack': 'SPRINT DISTANCE (M)', 'Midfield': 'TOTAL DISTANCE (M)', 'Defence': 'HSR DISTANCE (M)', 'Goalkeeper': 'NO. OF EXP. ACC. (TIMES)'}
                        target = u_map.get(curr['UNIT'], 'TOTAL DISTANCE (M)')
                        pos_list = master[master['UNIT'] == curr['UNIT']]['ATHLETENAME'].unique()
                        pos_avg_val = np.mean([master[(master['ATHLETENAME'] == n) & (master[target] > 0)][target].tail(7).mean() for n in pos_list])
                        st.metric(f"Pos Specific ({target.title()})", f"{int(curr[target]) if pd.notnull(curr[target]) else 0}", delta=f"{int(curr[target] - pos_avg_val) if pd.notnull(curr[target] - pos_avg_val) else 0}")

                    st.subheader("🧬 Load vs. Response Analysis")
                    ath_7s_dist = p_df[p_df['TOTAL DISTANCE (M)'] > 0]['TOTAL DISTANCE (M)'].tail(7).mean()
                    ath_7s_gym = p_df[p_df['VOLUME'] > 0]['VOLUME'].tail(7).mean()
                    pos_avg_dist_7s = np.nanmean([master[(master['ATHLETENAME'] == n) & (master['TOTAL DISTANCE (M)'] > 0)]['TOTAL DISTANCE (M)'].tail(7).mean() for n in pos_list])
                    personal_baseline_30s = p_df[p_df['VOLUME'] > 0]['VOLUME'].tail(30).mean()

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write("**Average Load This Week**")
                        d_arr, g_arr = ("↑" if ath_7s_dist > pos_avg_dist_7s else "↓"), ("↑" if ath_7s_gym > personal_baseline_30s else "↓")
                        st.write(f"🏃 Distance: {int(ath_7s_dist) if pd.notnull(ath_7s_dist) else 0}m {d_arr}")
                        st.write(f"🏋️ Gym Load: {int(ath_7s_gym) if pd.notnull(ath_7s_gym) else 0}kg {g_arr}")
                        st.caption(f"Pos Avg: {int(pos_avg_dist_7s)}m | Baseline: {int(personal_baseline_30s)}kg")
                    with col_b:
                        st.write("**Physical Cost**")
                        st.markdown(f"<h3 style='color:{cost_col}; margin-top:0;'>{cost_val:.1f} {cost_icon}</h3>", unsafe_allow_html=True)
                        st.write("(Fatigue & Soreness)")

                    d_dir, g_dir = ("higher" if ath_7s_dist > pos_avg_dist_7s else "lower"), ("higher" if ath_7s_gym > personal_baseline_30s else "lower")
                    if cost_icon == "✅": bg, tx, summ = "#D4EDDA", "#155724", "dealing with load well."
                    elif cost_icon == "⚠️": bg, tx, summ = "#FFF3CD", "#856404", "showing signs of fatigue."
                    else: bg, tx, summ = "#F8D7DA", "#721C24", "showing high physical strain."
                    st.markdown(f"""<div style="background-color:{bg}; color:{tx}; padding:15px; border-radius:5px; margin-bottom: 20px;">
                    <strong>MDT Insight:</strong> Distance is {d_dir} than Position Avg and Gym load is {g_dir} than Baseline. The athlete is {summ}</div>""", unsafe_allow_html=True)

                    st.subheader("🏥 Medical Context")
                    if st.session_state.injury_data is not None:
                        i_df = st.session_state.injury_data[st.session_state.injury_data['ATHLETENAME'] == sel_player]
                        if not i_df.empty:
                            latest_inj = i_df.iloc[-1]
                            st.write(f"**Most Recent Injury:** {latest_inj['TYPE']} ({latest_inj['STARTDATE'].strftime('%d/%m/%Y')})")
                            st.write(f"**Severity:** {latest_inj['SEVERITY']} | **Days Lost:** {latest_inj['DAYSLOST']}")
                            if pitch_acwr >= 0.8 and pitch_acwr <= 1.3 and cost_icon == "✅": a_t, a_i, a_c = "Adapting Well", "✅", "green"
                            elif pitch_acwr > 1.5 or cost_icon == "❌": a_t, a_i, a_c = "Adapting Badly", "❌", "red"
                            else: a_t, a_i, a_c = "Adapting Moderately", "⚠️", "#CC9900"
                            st.markdown(f"**Adaptation After Injury:** <span style='color:{a_c}; font-weight:bold;'>{a_t} {a_i}</span>", unsafe_allow_html=True)

                    st.subheader("🎯 The Verdict")
                    note_text = f" **Note: Readiness is {read_stat}, player may need rest/recovery.**" if read_stat != "Great" else ""
                    if s_txt == "STARTER": st.write(f"**Recommendation:** Physically elite. ACWR and Physical Cost are optimized. Start {sel_player} without restrictions.{note_text}")
                    elif s_txt == "BENCH / SUB": st.write(f"**Recommendation:** Recommended for bench role. {note_text if note_text else 'Load response suggests a protected plan.'}")
                    else: st.write(f"**Recommendation:** High risk detected. Rotation required.{note_text}")
                else: st.warning("No performance data found.")
            pass

        with t_analyst:
            # 1. FIXED Status Logic (Exact Hardcoded Mapping)
            game_data = p_df[p_df['MINUTESPLAYED'] > 0].tail(1)
            curr_game = game_data.iloc[0] if not game_data.empty else p_df.iloc[-1]

            status_manual_map = {
                "Alex Smith": ("STARTER", "green"),
                "Cameron Wright": ("STARTER", "green"),
                "Charlie Walker": ("STARTER", "green"),
                "Chris Clark": ("STARTER", "green"),
                "Drew Allan": ("STARTER", "green"),
                "Hayden Scott": ("BENCH / SUB", "#CC9900"),
                "Jamie Brown": ("STARTER", "green"),
                "Jesse Hall": ("STARTER", "green"),
                "Jordan Johnson": ("BENCH / SUB", "#CC9900"),
                "Morgan Wilson": ("NOT IN SQUAD", "red"),
                "Quinn King": ("NOT IN SQUAD", "red"),
                "Riley Young": ("NOT IN SQUAD", "red"),
                "Sam Taylor": ("NOT IN SQUAD", "red"),
                "Taylor Lee": ("STARTER", "green")
            }

            ana_status, ana_col = status_manual_map.get(sel_player, ("NOT IN SQUAD", "red"))

            role_map = {
                'ST': "Looks to press high and win the ball back quickly or force mistakes from defenders, they look to move around as much as possible to drag defenders and create space or run in behind the oppositions defensive line.",
                'LW': "Looks to press high to win the ball back or force mistakes from defenders, but also looks to use their pace to get in behind the opposition defense.",
                'RW': "Looks to press high to win the ball back or force mistakes from defenders, but also looks to use their pace to get in behind the opposition defense.",
                'CM': "Looks to cover as much ground as possible to ensure they dominate the midfield battle, they look to create space for themselves to drive with the ball or make a line breaking pass in behind to the attackers.",
                'CAM': "Looks to cover as much ground as possible to ensure they dominate the midfield battle, they look to create space for themselves to drive with the ball or make a line breaking pass in behind to the attackers.",
                'CDM': "Looks to track players in the midfield and break passing lanes and tackle the opposition, they are the first line of defense and look to win the ball back before they reach the defenders.",
                'LB': "Likes to get up high and help support the wingers, but they also need to make sure they are not leaving spaces at the back for opposition wingers to overload.",
                'RB': "Likes to get up high and help support the wingers, but they also need to make sure they are not leaving spaces at the back for opposition wingers to overload.",
                'CB': "Needs to try push high and have a high line, they command the wingers and aim to win the ball as high as possible, and if attackers get in behind they are quick enough to recover.",
                'GK': "Acts as a sweeper keeper picking up any loose balls in behind but also there as an extra option for defenders in the build up."
            }
            t_role = role_map.get(curr_game['POSITION'], "Tactical role defined by unit requirements.")

            st.markdown(f"### 🛡️ Tactical Performance Context: {sel_player}")
            st.markdown(f"**Current Status:** <span style='color:{ana_col}; font-weight:bold;'>{ana_status}</span> | **Position:** {curr_game['POSITION']} | **Formation:** 4-2-3-1 | **System:** High Aggressive Press & Quick Transitional Play from Defense to Attack", unsafe_allow_html=True)
            st.write(f"**Role Objective:** {t_role}")

            tab_unit, tab_role_exec = st.tabs(["📊 Tactical Comparison", "🎯 Role Execution"])

            with tab_unit:
                st.markdown(f"#### 📈 Positional Comparison: {curr_game['UNIT']} Baseline Comparison")

                pos_metrics_map = {
                    'Attack': ['SPRINT DISTANCE (M)', 'NO. OF EXP. ACC. (TIMES)', 'MAX SPEED (KM/H)'],
                    'Midfield': ['TOTAL DISTANCE (M)', 'HSR DISTANCE (M)', 'SPRINT DISTANCE (M)'],
                    'Defence': ['HSR DISTANCE (M)', 'NO. OF EXP. DEC. (TIMES)', 'SPRINT DISTANCE (M)'],
                    'Goalkeeper': ['NO. OF EXP. ACC. (TIMES)', 'NO. OF EXP. DEC. (TIMES)', 'MAX SPEED (KM/H)']
                }
                selected_metrics = pos_metrics_map.get(curr_game['UNIT'], ['TOTAL DISTANCE (M)', 'HSR DISTANCE (M)', 'SPRINT DISTANCE (M)'])
                col_an1, col_an2 = st.columns([2, 1])

                with col_an1:
                    player_vals, pos_avgs = [], []
                    for m in selected_metrics:
                        p_stat = curr_game.get(m, 0)
                        player_vals.append(p_stat if pd.notnull(p_stat) else 0)
                        active_pos_df = master[(master['UNIT'] == curr_game['UNIT']) & (master['MINUTESPLAYED'] > 0)]
                        avg_stat = active_pos_df[m].mean() if (m in active_pos_df.columns and not active_pos_df.empty) else 0
                        pos_avgs.append(avg_stat if pd.notnull(avg_stat) else 0)

                    fig_tact = go.Figure()
                    fig_tact.add_trace(go.Bar(name='Latest Game', x=selected_metrics, y=player_vals, marker_color='green'))
                    fig_tact.add_trace(go.Bar(name='Unit Average (Active)', x=selected_metrics, y=pos_avgs, marker_color='red'))
                    fig_tact.update_layout(barmode='group', height=350, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.1),
                                        plot_bgcolor='#87CEEB', paper_bgcolor='#87CEEB', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                    st.plotly_chart(fig_tact, use_container_width=True)

                with col_an2:
                    st.markdown("<h3 style='font-weight:bold; font-size:24px;'>Tactical Insight</h3>", unsafe_allow_html=True)
                    primary_ratio = (player_vals[0] / pos_avgs[0]) if (pos_avgs[0] > 0 and pd.notnull(player_vals[0])) else 1
                    p_pos = curr_game['POSITION']

                    if p_pos == 'GK':
                        if primary_ratio > 1.10:
                            perf_txt = "**Physically Dominant Sweeper:** Explosive movement is above unit baseline."
                            benefit = "Currently sweeping up long balls behind the high line with elite efficiency. This high engagement ensures the defense can push higher without fear of simple balls over the top."
                            risk = "Fulham often look for long balls over the top to bypass the press. As a GK, fatigue is low, but maintaining 90-minute hyper-awareness is vital to cut out these direct threats."
                        elif primary_ratio < 0.90:
                            perf_txt = "**Physically Conservative Keeper:** Engagement frequency is lower than unit average."
                            benefit = "Energy levels are perfectly preserved, but the keeper is staying deep. This leaves the space behind our high-line defenders vulnerable to direct attacks."
                            risk = "Fulham exploit deep-sitting keepers with direct transitional play. Must stay alert and proactive to ensure they aren't caught in 'no-man's land' during a long ball over the top."
                        else:
                            perf_txt = "**Physically Aligned:** Sweeping and explosive actions match unit expectations."
                            benefit = "Providing a stable, predictable option for defenders. The distribution and sweeping engagement are within the required tactical parameters for the 4-2-3-1."
                            risk = "Fulham's direct style requires constant focus. Stay aware of long-ball opportunities throughout the whole match to assist the CBs."
                    else:
                        if primary_ratio > 1.10:
                            perf_txt = f"**Physically Dominant:** Operating at {int((primary_ratio-1)*100)}% above unit baseline."
                            benefit = "Relentless individual pressing. However, this high output increases risk of late-game CNS fatigue. Monitor for a drop in defensive compactness after 65 mins."
                            risk = "Fulham thrive in transitions when the opposition press breaks. If the player fatigues and creates a gap, Fulham's quick wingers will exploit the space left behind."
                        elif primary_ratio < 0.90:
                            perf_txt = f"**Physically Conservative:** Output is {int((1-primary_ratio)*100)}% below unit average."
                            benefit = "Player is managing energy for the full 90, but the lower intensity suggests they are failing to hit the high-press triggers required by the system."
                            risk = "By not closing down lanes, Fulham are granted time to find line-breaking passes. This passivity allows them to build momentum and pin our fullbacks deep."
                        else:
                            perf_txt = "**Physically Aligned:** Output is perfectly in sync with positional standards."
                            benefit = "Sustainability is high. Maintaining the required vertical and lateral distance to keep our 4-2-3-1 shape compact against the ball."
                            risk = "Fulham will look for individual errors in the press. By matching the unit average, this player ensures the system remains a collective 'block' that is harder to bypass."

                    st.info(f"{perf_txt}\n\n**System Impact:** {benefit}\n\n**Fulham (A) Forecast:** {risk}")

            with tab_role_exec:
                p_pos = curr_game['POSITION']

                # 1. Middle-aligned heading for Goalkeepers
                if p_pos == 'GK':
                    st.markdown("<h4 style='text-align: center;'>🎯 System-Specific Tactical Metrics</h4>", unsafe_allow_html=True)
                    _, col_mid, _ = st.columns([1, 2, 1])
                    with col_mid:
                        engagement_score = curr_game.get('NO. OF EXP. ACC. (TIMES)', 0) + curr_game.get('NO. OF EXP. DEC. (TIMES)', 0)
                        unit_season = master[(master['UNIT'] == curr_game['UNIT']) & (master['MINUTESPLAYED'] > 0)]
                        avg_engage = (unit_season['NO. OF EXP. ACC. (TIMES)'].mean() + unit_season['NO. OF EXP. DEC. (TIMES)'].mean())
                        diff = engagement_score - avg_engage

                        st.metric("Latest Engagement (Acc + Dec)", f"{int(engagement_score)}", delta=f"{int(diff)} vs Unit Season Avg")
                        if diff > 10: st.error("**Excessive Engagement:** High volume of explosive actions. Check if the high line is forcing too many recovery sweeps.")
                        elif diff >= 0: st.success("**Active Sweeper:** Proactive movement frequency is optimal for our high-line build-up.")
                        else: st.warning("**Static Keeper:** Lower than average movement. Ensure the keeper is staying connected to the back four.")

                else:
                    st.markdown("#### 🎯 System-Specific Tactical Metrics")
                    c_role1, c_role2 = st.columns(2)
                    with c_role1:
                        engagement_score = curr_game.get('NO. OF EXP. ACC. (TIMES)', 0) + curr_game.get('NO. OF EXP. DEC. (TIMES)', 0)
                        unit_season = master[(master['UNIT'] == curr_game['UNIT']) & (master['MINUTESPLAYED'] > 0)]
                        avg_engage = (unit_season['NO. OF EXP. ACC. (TIMES)'].mean() + unit_season['NO. OF EXP. DEC. (TIMES)'].mean())
                        diff = engagement_score - avg_engage
                        st.metric("Latest Engagement (Acc + Dec)", f"{int(engagement_score)}", delta=f"{int(diff)} vs Season Unit Avg")

                        if diff > 10: st.error("**Excessive Engagement:** Significantly high activity. Over-working detected; potential substitution watch after 60 mins.")
                        elif 0 <= diff <= 10: st.success("**High Engagement:** Proactive 'ball hunting' detected, vital for the high-press system.")
                        elif -5 <= diff < 0: st.warning("**Moderate Engagement:** Slightly below average. Ensure positional intensity is maintained to meet system requirements.")
                        else: st.error("**Passive Engagement:** Significant activity drop. Likely 'containing' space rather than 'closing' it.")

                    with c_role2:
                        if p_pos in ['ST', 'RW', 'LW']:
                            top_speed = curr_game.get('MAX SPEED (KM/H)', 0)
                            st.metric("Top Speed (Last Game)", f"{top_speed} km/h")
                            if top_speed >= 33: st.success("**Elite Speed Readiness:** Fast enough to exploit space in behind effectively.")
                            else: st.error("**Pace Deficiency:** Speed below 33 km/h. Player needs to maximize effort in transitions.")

                        elif p_pos in ['CM', 'CAM', 'CDM']:
                            dist = curr_game.get('TOTAL DISTANCE (M)', 0); dur = curr_game.get('DURATION (MIN)', 1)
                            m_per_min = dist / dur
                            st.metric("Work Rate (m/min)", f"{m_per_min:.1f} m/min")
                            if m_per_min > 130: st.error("**Over-working:** Intensity is unsustainably high. Risk of tactical burnout.")
                            elif m_per_min >= 115: st.success("**High Intensity:** Covering ground effectively to dominate the midfield battle.")
                            elif m_per_min >= 105: st.warning("**Sub-optimal Intensity:** Intensity is slightly below target.")
                            else: st.error("**Low Intensity:** Failing to cover ground required to dominate the midfield.")

                        elif p_pos in ['CB', 'LB', 'RB']:
                            current_max = curr_game.get('MAX SPEED (KM/H)', 0)
                            personal_best = master[master['ATHLETENAME'] == sel_player]['MAX SPEED (KM/H)'].max()
                            speed_pct = (current_max / personal_best) if personal_best > 0 else 0
                            st.metric("Recovery Speed Readiness", f"{speed_pct:.1%}")
                            if speed_pct > 0.90: st.success("**High Line Secure:** Safe to push high; player has the recovery speed required.")
                            else: st.error("**High Line At Risk:** Low top-end speed. High risk of exposure behind the line.")
            st.divider()
            pass

        with t_perf:
            # --- 1. SQUAD TRIAGE MATRIX (TOTAL WORKLOAD TAB) ---
            master['DATE'] = pd.to_datetime(master['DATE'], dayfirst=True, errors='coerce')
            all_athletes = sorted(master['ATHLETENAME'].unique())
            squad_stats = []
            for athlete in all_athletes:
                p_rows = master[master['ATHLETENAME'] == athlete].sort_values('DATE')
                if p_rows.empty: continue

                # Pitch ACWR
                latest_session = p_rows[p_rows['TOTAL DISTANCE (M)'] > 0].iloc[-1] if not p_rows[p_rows['TOTAL DISTANCE (M)'] > 0].empty else p_rows.iloc[-1]
                pitch_acwr = latest_session.get('ACWR', 1.0)

                # Gym ACWR Calculation
                gym_rows = p_rows[p_rows['VOLUME'] > 0]
                if not gym_rows.empty:
                    g_7d = gym_rows['VOLUME'].tail(7).mean()
                    g_28d = gym_rows['VOLUME'].tail(28).mean()
                    gym_acwr = g_7d / g_28d if g_28d > 0 else 1.0
                    g_val = gym_rows['VOLUME'].iloc[-1]
                else:
                    gym_acwr = 1.0
                    g_val = 0

                latest_well_row = p_rows[(p_rows['SORENESS'] > 0) | (p_rows['FATIGUE'] > 0)].tail(1)
                avg_dist = p_rows['TOTAL DISTANCE (M)'].replace(0, np.nan).tail(28).mean()
                avg_vol = p_rows.get('VOLUME', 0).replace(0, np.nan).tail(28).mean()

                d_val = latest_session.get('TOTAL DISTANCE (M)', 0)
                sore_val = latest_well_row['SORENESS'].values[0] if not latest_well_row.empty else 5.0
                fat_val = latest_well_row['FATIGUE'].values[0] if not latest_well_row.empty else 5.0
                cost = float((sore_val + fat_val) / 2)

                dist_spike = (d_val / avg_dist * 100) if (avg_dist and avg_dist > 0) else 100
                gym_spike = (g_val / avg_vol * 100) if (avg_vol and avg_vol > 0) else 100

                risk_score = 0
                if dist_spike > 130 or gym_spike > 130: risk_score += 5
                if cost >= 6.5: risk_score += 10
                if pitch_acwr > 1.5 or pitch_acwr < 0.7: risk_score += 20

                squad_stats.append({
                    "Athlete": athlete, "Position": p_rows['POSITION'].iloc[-1],
                    "Latest Dist (m)": int(d_val), "Latest Gym (kg)": int(g_val),
                    "Physical Cost": cost, "Pitch ACWR": float(pitch_acwr), "Gym ACWR": float(gym_acwr),
                    "_dist_spike": dist_spike, "_gym_spike": gym_spike, "_total_risk": risk_score
                })
            df_squad = pd.DataFrame(squad_stats).sort_values('_total_risk', ascending=False)

            sub_total, sub_ses, sub_sc = st.tabs(["📊 Squad Workload (MDT)", "🏃 SES (Pitch Deep-Dive)", "🏋️ S&C (Gym Deep-Dive)"])

            with sub_total:
                st.markdown("### 📋 Squad Workload & Recovery Matrix")
                def style_triage_final(row):
                    styles = [''] * len(row)
                    if row['_dist_spike'] > 130: styles[2] = 'color: #ff4b4b; font-weight: bold'
                    elif row['_dist_spike'] > 115: styles[2] = 'color: #ffa500; font-weight: bold'
                    else: styles[2] = 'color: #2ecc71; font-weight: bold'
                    if row['_gym_spike'] > 130: styles[3] = 'color: #ff4b4b; font-weight: bold'
                    elif row['_gym_spike'] > 115: styles[3] = 'color: #ffa500; font-weight: bold'
                    else: styles[3] = 'color: #2ecc71; font-weight: bold'
                    c = row['Physical Cost']
                    if c >= 6.5: styles[4] = 'color: #ff4b4b; font-weight: bold'
                    elif c >= 5.5: styles[4] = 'color: #ffa500; font-weight: bold'
                    else: styles[4] = 'color: #2ecc71; font-weight: bold'
                    if not (0.8 <= row['Pitch ACWR'] <= 1.3): styles[5] = 'color: #ff4b4b; font-weight: bold'
                    else: styles[5] = 'color: #2ecc71; font-weight: bold'
                    if not (0.8 <= row['Gym ACWR'] <= 1.3): styles[6] = 'color: #ff4b4b; font-weight: bold'
                    else: styles[6] = 'color: #2ecc71; font-weight: bold'
                    return styles

                visible_cols = ["Athlete", "Position", "Latest Dist (m)", "Latest Gym (kg)", "Physical Cost", "Pitch ACWR", "Gym ACWR"]
                st.dataframe(df_squad.style.apply(style_triage_final, axis=1).format({"Physical Cost": "{:.1f}/10", "Pitch ACWR": "{:.2f}", "Gym ACWR": "{:.2f}"}),
                            use_container_width=True, hide_index=True, column_order=visible_cols)
                st.info("💡 **Note:** Focus performance reviews on players with **Red** or **Yellow** values to proactively manage injury risk.")

            with sub_ses:
                p_history = master[master['ATHLETENAME'] == sel_player].sort_values('DATE')
                p_move_history = p_history[p_history['TOTAL DISTANCE (M)'] > 0]
                latest = p_move_history.iloc[-1] if not p_move_history.empty else p_history.iloc[-1]
                p_pos = latest.get('POSITION', 'Unknown'); p_unit = latest.get('UNIT', 'General')

                avail = "❌ Unavailable" if sel_player == "Casey Lewis" else "✅ Fit"
                sore_c = latest.get('SORENESS', 5); fat_c = latest.get('FATIGUE', 5); slp_c = latest.get('SLEEPHOURS', 8)
                raw_well = ((10-float(sore_c)) + (10-float(fat_c)) + min(10, (float(slp_c)/8)*10)) / 3
                readiness_pct = int(raw_well * 10) if not pd.isna(raw_well) else 50
                if avail == "✅ Fit": readiness_pct = min(100, int(readiness_pct * 1.10))
                acwr_c = round(latest.get('ACWR', 0), 2)

                if 0.8 <= acwr_c <= 1.3: acwr_icon = "✅"
                elif (1.3 < acwr_c <= 1.5) or (0.6 <= acwr_c < 0.8): acwr_icon = "⚠️"
                else: acwr_icon = "❌"

                if avail == "❌ Unavailable" or acwr_c > 1.5 or acwr_c < 0.6 or readiness_pct < 60:
                    smart_rec = "Immediate Changes"; rec_icon = "❌"; rec_col = "red"
                elif 0.8 <= acwr_c <= 1.3 and readiness_pct > 70:
                    smart_rec = "Training Plan Effective"; rec_icon = "✅"; rec_col = "green"
                else:
                    smart_rec = "Slightly Alter Training Plan"; rec_icon = "⚠️"; rec_col = "#CC9900"

                st.markdown(f"## {sel_player} | <span style='font-size: 0.8em; color: gray;'>{p_pos}</span>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin-bottom: 0px;'><strong>Smart Recommendation:</strong></p><h2 style='color:{rec_col}; margin-top: 0px; margin-bottom: 0px;'>{rec_icon} {smart_rec}</h2>", unsafe_allow_html=True)
                st.markdown(f"<span style='font-size: 1.3em; font-weight: bold;'>Current Pitch ACWR: {acwr_c} {acwr_icon}</span>", unsafe_allow_html=True)

                # Positional Role (Pitch Specific)
                role_desc_pitch = {
                    'Attack': "Attackers require elite high-speed running (HSR) and sprinting capacity. Monitoring ensures explosive availability remains high for breaching defensive lines.",
                    'Midfield': "Midfielders demand the highest total distance and repeated metabolic work-rate. Requirements focus on aerobic durability to sustain box-to-box coverage.",
                    'Defence': "Defenders prioritize high acceleration and deceleration counts. Pitch metrics emphasize short-area reactivity and recovery speed for defensive duels.",
                    'Goalkeeper': "Goalkeepers focus on explosive short-range positioning and reactive load. Requirements focus on power-based mobility and cognitive readiness."
                }
                st.info(f"**Positional Role ({p_unit}):** {role_desc_pitch.get(p_unit, 'Requirements focus on tactical positioning and unit-specific physical outputs.')}")

                st.subheader("Wellness Scores (28-Day Avg)")
                w_df = p_history.tail(28)
                a_slp = w_df['SLEEPHOURS'].mean(); a_fat = w_df['FATIGUE'].mean(); a_sore = w_df['SORENESS'].mean()
                w_cols = st.columns(3)
                def get_w_status_custom(val):
                    if val < 5.5: return "✅", "green"
                    elif 5.5 <= val <= 6.5: return "⚠️", "#CC9900"
                    else: return "❌", "red"
                f_i, f_c = get_w_status_custom(a_fat); sr_i, sr_c = get_w_status_custom(a_sore)
                sl_i, sl_c = ("✅", "green") if a_slp >= 7.5 else (("⚠️", "#CC9900") if a_slp >= 6.5 else ("❌", "red"))
                with w_cols[0]: st.markdown(f"**Sleep**<br><h3 style='color:{sl_c};'>{sl_i} {a_slp:.1f} hrs</h3>", unsafe_allow_html=True)
                with w_cols[1]: st.markdown(f"**Fatigue**<br><h3 style='color:{f_c};'>{f_i} {a_fat:.1f}/10</h3>", unsafe_allow_html=True)
                with w_cols[2]: st.markdown(f"**Soreness**<br><h3 style='color:{sr_c};'>{sr_i} {a_sore:.1f}/10</h3>", unsafe_allow_html=True)

                st.subheader(f"Position Comparison (28-Session Avg) | {p_unit}")
                pos_list = master[master['UNIT'] == p_unit]['ATHLETENAME'].unique()
                metrics = [('TOTAL DISTANCE (M)', 'Total Dist', 'm'), ('HSR DISTANCE (M)', 'HSR Dist', 'm'), ('SPRINT DISTANCE (M)', 'Sprint Dist', 'm'), ('NO. OF EXP. ACC. (TIMES)', 'Accels', 'ct'), ('NO. OF EXP. DEC. (TIMES)', 'Decels', 'ct')]
                m_cols = st.columns(5)
                gps_low_metrics = []
                for i, (m_key, m_label, m_unit) in enumerate(metrics):
                    p_avg = p_history[p_history[m_key] > 0][m_key].tail(28).mean()
                    pos_avg_val = np.mean([master[(master['ATHLETENAME'] == n) & (master[m_key] > 0)][m_key].tail(28).mean() for n in pos_list if not master[(master['ATHLETENAME'] == n) & (master[m_key] > 0)].empty])
                    p_diff = ((p_avg / pos_avg_val) - 1) * 100 if pos_avg_val > 0 else 0
                    if p_diff <= -6: icon, col = "❌", "red"; gps_low_metrics.append(m_label)
                    else: icon, col = "✅", "green"
                    with m_cols[i]:
                        st.markdown(f"**{m_label} ({m_unit})**")
                        st.markdown(f"### {int(p_avg) if pd.notnull(p_avg) else 0}")
                        st.markdown(f"<span style='color:{col}; font-weight:bold;'>{icon} {p_diff:+.1f}%</span>", unsafe_allow_html=True)

                # --- POSITIONAL IMPACT ASSESSMENT SENTENCE ---
                role_impacts = {
                    'Attack': "explosive availability for breaching defensive lines",
                    'Midfield': "aerobic durability for box-to-box coverage",
                    'Defence': "short-area reactivity and recovery speed for defensive duels",
                    'Goalkeeper': "power-based mobility and reactive readiness"
                }
                impact_area = role_impacts.get(p_unit, "tactical positioning and unit-specific physical outputs")
                if gps_low_metrics:
                    st.write(f"**Impact Assessment:** Lower outputs in {', '.join(gps_low_metrics)} suggest a potential drop in positional effectiveness, making it harder to sustain the required {impact_area}.")
                else:
                    st.write(f"**Impact Assessment:** Current outputs are aligned with or exceeding unit averages, ensuring {sel_player} meets the physical demands of the {p_unit} role.")

                st.divider()
                cl1, cl2 = st.columns(2)
                with cl1:
                    cur_sp = latest.get('MAX SPEED (KM/H)', 0); pb_sp = p_history['MAX SPEED (KM/H)'].max()
                    sp_pct = min(100, (cur_sp / pb_sp * 100)) if pb_sp > 0 else 0
                    fig_g = go.Figure(go.Indicator(
                        mode = "gauge+number", value = sp_pct, number = {'suffix': "%", 'font': {'color': 'black'}},
                        title = {'text': f"<span style='color:black; font-weight:bold;'>Speed PB Capture</span>"},
                        gauge = {'axis': {'range': [0, 100], 'tickfont': {'color': 'black'}, 'tickmode': 'linear', 'tick0': 0, 'dtick': 20},
                                'bar': {'color': "#2ecc71" if sp_pct >= 90 else "#ffa500"},
                                'threshold': {'line': {'color': "green", 'width': 4}, 'thickness': 0.75, 'value': 90},
                                'bgcolor': "rgba(0,0,0,0)"}
                    ))
                    fig_g.update_layout(height=230, margin=dict(l=40, r=60, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_g, use_container_width=True)
                    st.markdown(f"<p style='font-size: 0.85em; color: #444;'><strong>Context:</strong> This gauge reflects their <strong>Latest Session Max Speed</strong> ({cur_sp} km/h) relative to their <strong>All-Time PB</strong> ({pb_sp} km/h). Maintaining >90% indicates high neurological freshness.</p>", unsafe_allow_html=True)
                with cl2:
                    st.markdown("<h5 style='color:black;'>Mechanical Efficiency</h5>", unsafe_allow_html=True)
                    mmin = latest.get('TOTAL DISTANCE/MIN (M/MIN)', 0)
                    if mmin == 0: mmin = (latest['TOTAL DISTANCE (M)'] / 90)
                    eff_well = (float(latest.get('SORENESS', 5)) + float(latest.get('FATIGUE', 5))) / 2
                    eff = mmin / eff_well if (eff_well > 0 and mmin > 0) else 0
                    st.metric("Efficiency Index", f"{eff:.2f}")
                    if eff >= 15: st.success("✅ **Scores in Desired Range**")
                    else: st.error("❌ **Scores Below Desired Range**")
                    st.markdown(f"<p style='font-size: 0.85em; color: #444;'><strong>Context:</strong> Movement output (m/min) relative to internal cost. <strong>{p_unit}s</strong> typically aim for >15.0.</p>", unsafe_allow_html=True)

                # --- PERFORMANCE VERDICT (Updated with Recommendations) ---
                st.subheader("🎯 The Performance Verdict")
                v_reasons = []
                if a_fat > 5.5: v_reasons.append("muscle fatigue");
                if a_sore > 5.5: v_reasons.append("muscle soreness")
                if acwr_c > 1.3: v_reasons.append("workload spike")
                if sp_pct < 90: v_reasons.append("neurological deficit")

                if smart_rec == "Training Plan Effective":
                    st.write(f"**Verdict:** {sel_player} is physically optimized. Pitch loading is perfectly aligned with the tactical role. **Recommendation:** Training program is fine; maintain current pitch loading.")
                else:
                    under_msg = f" {sel_player} is significantly underperforming in metrics compared to other players in **{p_unit}**." if gps_low_metrics else ""

                    if smart_rec == "Slightly Alter Training Plan":
                        pitch_reco = "Suggest a 10% reduction in high-intensity pitch volume (HSR/Sprints) in the next session to allow wellness markers to return to baseline."
                    else: # Immediate Changes
                        pitch_reco = "Immediate reduction in drill intensity and total pitch volume is required to mitigate injury risk and address recovery deficits."

                    st.write(f"**Diagnostic Summary:** The current recommendation to **{smart_rec}** is driven by {', '.join(v_reasons) if v_reasons else 'minor loading variances'}.{under_msg} **Recommendation:** {pitch_reco}")


            with sub_sc:
                sc_all = master[(master['ATHLETENAME'] == sel_player) & (master['VOLUME'] > 0)].sort_values('DATE')
                if sc_all.empty:
                    st.warning(f"No S&C data found for {sel_player}.")
                else:
                    latest_gym = sc_all.iloc[-1]
                    p_pos = latest_gym.get('POSITION', 'Unknown')
                    p_unit = latest_gym.get('UNIT', 'Other')
                    p_rows = master[master['ATHLETENAME'] == sel_player].sort_values('DATE')

                    # --- 1. DYNAMIC SMART RECO (MATCHING COACH TAB LOGIC) ---
                    def get_recent(series, default_val):
                        valid = series.dropna()
                        return valid.iloc[-1] if not valid.empty else default_val

                    latest_gps = p_rows[p_rows['TOTAL DISTANCE (M)'] > 0].iloc[-1] if not p_rows[p_rows['TOTAL DISTANCE (M)'] > 0].empty else p_rows.iloc[-1]

                    # Wellness/Readiness components
                    sore = get_recent(p_rows['SORENESS'], 5)
                    fat = get_recent(p_rows['FATIGUE'], 5)
                    slp = get_recent(p_rows['SLEEPHOURS'], 8)
                    avail = "❌ Unavailable" if sel_player == "Casey Lewis" else "✅ Fit"

                    raw_well = ((10-float(sore)) + (10-float(fat)) + min(10, (float(slp)/8)*10)) / 3
                    readiness_pct = int(raw_well * 10)
                    if avail == "✅ Fit": readiness_pct = min(100, int(readiness_pct * 1.10))

                    # Load Metrics
                    pitch_acwr = latest_gps.get('ACWR', 0)
                    gym_7d_vol = sc_all['VOLUME'].tail(7).mean()
                    gym_28d_vol = sc_all['VOLUME'].tail(28).mean()
                    gym_acwr = round(gym_7d_vol / gym_28d_vol, 2) if gym_28d_vol > 0 else 1.0

                    # Logic used in Coach Tab
                    pitch_stable = 0.8 <= pitch_acwr <= 1.3
                    gym_stable = 0.8 <= gym_acwr <= 1.3

                    if avail == "❌ Unavailable" or pitch_acwr > 1.5 or pitch_acwr < 0.6 or gym_acwr > 1.5 or gym_acwr < 0.6 or readiness_pct < 50:
                        sc_rec, sc_icon, sc_col = "Immediate Changes", "❌", "red"
                    elif pitch_stable and gym_stable and readiness_pct >= 70:
                        sc_rec, sc_icon, sc_col = "Training Plan Effective", "✅", "green"
                    else:
                        sc_rec, sc_icon, sc_col = "Slightly Alter Training Plan", "⚠️", "#CC9900"

                    g_acwr_icon = "✅" if 0.8 <= gym_acwr <= 1.3 else "⚠️" if (1.3 < gym_acwr <= 1.5) or (0.6 <= gym_acwr < 0.8) else "❌"

                    st.markdown(f"## {sel_player} | <span style='font-size: 0.8em; color: gray;'>{p_pos}</span>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin-bottom: 0px;'><strong>Smart Recommendation:</strong></p><h2 style='color:{sc_col}; margin-top: 0px; margin-bottom: 0px;'>{sc_icon} {sc_rec}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<span style='font-size: 1.3em; font-weight: bold;'>Current Gym ACWR: {gym_acwr} {g_acwr_icon}</span>", unsafe_allow_html=True)

                    # --- 2. POSITIONAL ROLE CONTEXT ---
                    role_descriptions = {
                        'Attack': "Attackers require high explosive power and trunk stability to manage high-speed changes of direction and duels. Training focuses on 'Speed-Strength' to ensure gym load doesn't blunt match-day acceleration.",
                        'Midfield': "Midfielders demand elite work capacity and repeated effort ability. Gym data should reflect high 'Volume-Density' to support the metabolic demands of covering large distances on the pitch.",
                        'Defence': "Defenders prioritize maximal strength and robust physical mass to win aerial and ground duels. High 'Intensity Density' is critical here to maintain a strength reserve for contact situations.",
                        'Goalkeeper': "Goalkeepers focus on reactive power, vertical jumping, and shoulder girdle stability. Training plans are low-volume but extremely high-intent to maintain neurological freshness."
                    }
                    pos_desc = role_descriptions.get(p_unit, "Positional training focuses on individual robustness and sport-specific movement patterns.")
                    st.info(f"**Positional Role ({p_unit}):** {pos_desc}")

                    # --- 3. WELLNESS SCORES (28-Day Avg logic) ---
                    st.subheader("Wellness Scores (28-Day Avg)")
                    p_history_sc = master[master['ATHLETENAME'] == sel_player].sort_values('DATE')
                    w_df_sc = p_history_sc.tail(28)
                    a_slp_sc = w_df_sc['SLEEPHOURS'].mean(); a_fat_sc = w_df_sc['FATIGUE'].mean(); a_sore_sc = w_df_sc['SORENESS'].mean()
                    w_cols_sc = st.columns(3)
                    def get_w_status_custom_sc(val):
                        if val < 5.5: return "✅", "green"
                        elif 5.5 <= val <= 6.5: return "⚠️", "#CC9900"
                        else: return "❌", "red"
                    f_i_sc, f_c_sc = get_w_status_custom_sc(a_fat_sc); sr_i_sc, sr_c_sc = get_w_status_custom_sc(a_sore_sc)
                    sl_i_sc, sl_c_sc = ("✅", "green") if a_slp_sc >= 7.5 else (("⚠️", "#CC9900") if a_slp_sc >= 6.5 else ("❌", "red"))
                    with w_cols_sc[0]: st.markdown(f"**Sleep**<br><h3 style='color:{sl_c_sc};'>{sl_i_sc} {a_slp_sc:.1f} hrs</h3>", unsafe_allow_html=True)
                    with w_cols_sc[1]: st.markdown(f"**Fatigue**<br><h3 style='color:{f_c_sc};'>{f_i_sc} {a_fat_sc:.1f}/10</h3>", unsafe_allow_html=True)
                    with w_cols_sc[2]: st.markdown(f"**Soreness**<br><h3 style='color:{sr_c_sc};'>{sr_i_sc} {a_sore_sc:.1f}/10</h3>", unsafe_allow_html=True)

                    # --- 4. GYM PROGRESSION (28-SESSION BASELINE) ---
                    st.divider()
                    st.subheader("📈 Gym Progression (Latest vs. 28-Session Average)")
                    sc_28 = sc_all.tail(28)
                    metrics_list = [('VOLUME', 'Total Volume', 'kg'), ('LOAD', 'Total Load', 'kg'), ('RPE', 'Session RPE', '/10'), ('SETS', 'Total Sets', 'ct'), ('REPS', 'Total Reps', 'ct')]
                    m_cols = st.columns(5)
                    gym_trends = []
                    for i, (m_key, m_label, m_unit_str) in enumerate(metrics_list):
                        cur_val = latest_gym[m_key]
                        baseline_val = sc_28[m_key].mean()
                        p_diff = ((cur_val / baseline_val) - 1) * 100 if baseline_val > 0 else 0
                        icon, col = ("✅", "green") if p_diff >= 0 else ("❌", "red")
                        if abs(p_diff) > 10: gym_trends.append(f"{'increased' if p_diff > 0 else 'decreased'} {m_label}")
                        with m_cols[i]:
                            st.markdown(f"**{m_label} ({m_unit_str})**")
                            st.markdown(f"### {round(cur_val, 1) if 'RPE' in m_key else int(cur_val)}")
                            st.markdown(f"<span style='color:{col}; font-weight:bold;'>{icon} {p_diff:+.1f}%</span>", unsafe_allow_html=True)

                    # --- 5. PRESCRIBED TRAINING PLAN LOGIC ---
                    i_dens = latest_gym['VOLUME'] / latest_gym['REPS'] if latest_gym['REPS'] > 0 else 0
                    avg_28_dens = (sc_all['VOLUME'].tail(28).sum() / sc_all['REPS'].tail(28).sum()) if sc_all['REPS'].tail(28).sum() > 0 else 0
                    avg_28_reps = sc_all['REPS'].tail(28).mean()

                    if i_dens > avg_28_dens and latest_gym['REPS'] < avg_28_reps:
                        plan_type = "Strength & Power Training"
                        plan_desc = f"Characterized by high load and low repetitions. This builds maximal force production essential for {p_unit} roles, ensuring explosive output without excessive metabolic fatigue."
                    elif i_dens >= (avg_28_dens * 0.85) and latest_gym['REPS'] >= avg_28_reps:
                        plan_type = "Hypertrophy Training"
                        plan_desc = f"Medium loads combined with high repetitions. This focuses on structural robustness and muscle durability, supporting the physical grind required for {p_unit}s."
                    else:
                        plan_type = "Recovery and Rehabilitation Training"
                        plan_desc = f"Low loads and adjusted volume. This protocol is utilized to protect the player, allowing for tissue recovery while maintaining movement quality during periods of high internal strain."

                    st.markdown(f"#### 📝 Current Training Focus: **{plan_type}**")
                    st.write(f"**Logic:** {plan_desc}")

                    # --- 6. RADAR CHART (Most Recent Session + Tooltips + Bold Black Font) ---
                    st.subheader("🎯 Muscle Group Volume Distribution")
                    categories = ['Chest', 'Shoulders', 'Legs', 'Arms', 'Back', 'Core']
                    ath_v = [latest_gym['CHEST_V'], latest_gym['SH_V'], latest_gym['LEG_V'], latest_gym['ARM_V'], latest_gym['BACK_V'], latest_gym['CORE_V']]
                    base_v = [sc_all['CHEST_V'].tail(28).mean(), sc_all['SH_V'].tail(28).mean(), sc_all['LEG_V'].tail(28).mean(), sc_all['ARM_V'].tail(28).mean(), sc_all['BACK_V'].tail(28).mean(), sc_all['CORE_V'].tail(28).mean()]

                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(r=base_v + [base_v[0]], theta=categories + [categories[0]], fill='toself', name='<b>28-Session Baseline</b>', line_color='purple', fillcolor='rgba(128, 0, 128, 0.1)', hovertemplate="Avg Baseline: %{r:.0f}kg<extra></extra>"))
                    fig_radar.add_trace(go.Scatterpolar(r=ath_v + [ath_v[0]], theta=categories + [categories[0]], fill='toself', name='<b>Most Recent Session</b>', line_color='green', fillcolor='rgba(46, 204, 113, 0.4)', hovertemplate="Recent Session: %{r:.0f}kg<extra></extra>"))
                    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, showticklabels=False), angularaxis=dict(tickfont=dict(color='black', size=12, family='Arial Black'))), legend=dict(font=dict(color='black', size=12, family='Arial Black')), showlegend=True, height=450, margin=dict(l=80, r=80, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_radar, use_container_width=True)

                    # --- RADAR CHART INTERPRETATION ---
                    total_recent_v = sum(ath_v)
                    total_base_v = sum(base_v)
                    v_diff_pct = ((total_recent_v / total_base_v) - 1) * 100 if total_base_v > 0 else 0
                    peak_group = categories[np.argmax(ath_v)]

                    st.markdown(f"""
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid {CITY_SKY_BLUE}; margin-bottom: 20px;">
                        <p style='margin: 0; color: black; font-size: 1.0em;'>
                            <strong>Chart Interpretation:</strong> The radar shows a <strong>{v_diff_pct:+.1f}%</strong>
                            overall change in total volume compared to the 28-session baseline, with the largest
                            mechanical load currently focused on the <strong>{peak_group}</strong>.
                            {"This spike in specific muscle group volume correlates with the current elevation in fatigue/soreness markers, suggesting high physiological cost." if (a_fat_sc > 6 or a_sore_sc > 6) else "Despite the distribution shifts, wellness markers remain stable, indicating the athlete is coping well with this specific load profile."}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # --- 7. DIAGNOSTIC GAUGES (Original Text & Formatting Restored) ---
                    st.divider()
                    st.subheader("📊 Gym Output Diagnostics")
                    g_col1, g_col2 = st.columns(2)
                    with g_col1:
                        cur_eff = latest_gym['VOLUME'] / (latest_gym['RPE'] * latest_gym['SETS']) if (latest_gym['RPE'] > 0 and latest_gym['SETS'] > 0) else 0
                        max_eff_val = (sc_all['VOLUME'] / (sc_all['RPE'] * sc_all['SETS'])).tail(90).max()
                        eff_pct = min(100, (cur_eff / max_eff_val * 100)) if max_eff_val > 0 else 0
                        fig_eff = go.Figure(go.Indicator(mode = "gauge+number", value = eff_pct, number = {'suffix': "%", 'font': {'color': 'black'}}, title = {'text': f"<span style='color:black; font-weight:bold;'>Strength Efficiency Index</span>"}, gauge = {'axis': {'range': [0, 100], 'tickfont': {'color': 'black'}, 'dtick': 20}, 'bar': {'color': "#2ecc71" if eff_pct >= 85 else "#ffa500"}, 'threshold': {'line': {'color': "green", 'width': 4}, 'thickness': 0.75, 'value': 85}, 'bgcolor': "rgba(0,0,0,0)"}))
                        fig_eff.update_layout(height=230, margin=dict(l=40, r=60, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_eff, use_container_width=True)
                        st.markdown(f"<p style='font-size: 0.85em; color: #444;'><strong>Calculation:</strong> Total Volume / (Session RPE × Total Sets).<br><strong>Context:</strong> Measures the 'Neurological Price' paid for gym work. A high score (target <strong>>85%</strong>) indicates the athlete is hitting their numbers with high movement quality and low relative strain, preventing 'gym-burnout' from leaking into match-day performance.</p>", unsafe_allow_html=True)
                    with g_col2:
                        st.markdown("<h5 style='color:black; font-weight:bold;'>Intensity Density</h5>", unsafe_allow_html=True)
                        st.metric("Avg Weight per Rep", f"{i_dens:.1f} kg/rep")
                        if i_dens >= avg_28_dens: st.success("✅ **Intensity above 28-day average**")
                        else: st.warning("⚠️ **Intensity below 28-day average**")
                        st.markdown(f"<p style='font-size: 0.85em; color: #444;'><strong>Calculation:</strong> Total Session Volume / Total Session Reps.<br><strong>Context:</strong> Tracks <strong>Strength Quality</strong>. **{p_unit}s** aim for high intensity relative to their historical average. Maintaining density above your 28-day average ensures you are moving effective loads rather than accumulating 'empty volume' reps that cause fatigue without performance gains.</p>", unsafe_allow_html=True)

                    # --- 8. THE PERFORMANCE VERDICT (Integrated Logic) ---
                    st.subheader("🎯 The Performance Verdict")
                    sc_reasons = []
                    if a_fat_sc > 5.5: sc_reasons.append(f"accumulated fatigue ({a_fat_sc:.1f}/10)")
                    if a_sore_sc > 5.5: sc_reasons.append(f"muscle soreness ({a_sore_sc:.1f}/10)")
                    if eff_pct < 85: sc_reasons.append(f"a neural efficiency deficit ({eff_pct:.1f}%)")

                    trend_msg = f" and {', '.join(gym_trends)}" if gym_trends else ""
                    well_msg = f"driven by {', '.join(sc_reasons)}{trend_msg}" if sc_reasons else "supported by stable metrics"

                    st.write(f"**Diagnostic Summary:** The current recommendation to **{sc_rec}** is {well_msg}. This combination impacts the **{p_unit}** role's capacity to maintain peak intensity.")

                    if sc_rec == "Training Plan Effective":
                        st.write("**Recommendation:** Training program is fine. Maintain current loads to capitalize on positive adaptation.")
                    elif sc_rec == "Slightly Alter Training Plan":
                        st.write("**Recommendation:** Reduce total volume by 10-15% in the next session to prioritize recovery while maintaining intensity density.")
                    else:
                        st.write("**Recommendation:** Immediate reduction in load required. Pivot to the 'Recovery and Rehabilitation' focus until wellness markers normalize.")
            pass

        with t_med:
            st.markdown(f"### 🏥 Medical & Availability: {sel_player}")
            inj_df = st.session_state.injury_data

            if inj_df is not None:
                p_inj = inj_df[inj_df['ATHLETENAME'] == sel_player].copy()
                if not p_inj.empty:
                    sort_col = 'STARTDATE'
                    p_inj = p_inj.sort_values(sort_col, ascending=True)
                    tab_titles = [f"{row.get('TYPE', 'Record')} - {row[sort_col].strftime('%B')}" for _, row in p_inj.iterrows()]
                    sub_tabs = st.tabs(tab_titles)

                    for i, (idx, row) in enumerate(p_inj.iterrows()):
                        with sub_tabs[i]:
                            # --- LAYER 1: RISK CONTEXT ---
                            s_dt, e_dt = row.get('STARTDATE'), row.get('ENDDATE')
                            s_str = s_dt.strftime('%d %b %Y') if pd.notnull(s_dt) else "N/A"
                            e_str = e_dt.strftime('%d %b %Y') if pd.notnull(e_dt) else "Ongoing"

                            m1, m2, m3 = st.columns(3)
                            with m1: st.metric("Days Lost", int(row.get('DAYSLOST', 0)) if pd.notnull(row.get('DAYSLOST')) else 0)
                            with m2: st.metric("Severity", str(row.get('SEVERITY', 'N/A')))
                            with m3:
                                count = len(p_inj[(p_inj[sort_col] <= row[sort_col]) & (p_inj['TYPE'] == row['TYPE'])])
                                st.markdown(f"**Occurrence**<br><span style='color:{'red' if count > 1 else 'green'}; font-weight:bold;'>{'⚠️ Repeat' if count > 1 else '✅ First'} Issue (x{count})</span>", unsafe_allow_html=True)

                            st.markdown(f"##### **Timeline:** {s_str} — {e_str} &nbsp;&nbsp; | &nbsp;&nbsp; **Context:** {str(row.get('CONTEXT', 'N/A')).upper()}")

                            # --- ACWR CALCULATIONS ---
                            p_hist_all = master[(master['ATHLETENAME'] == sel_player) & (master['DATE'] <= s_dt)].sort_values('DATE')

                            gym_7d_vol = p_hist_all['VOLUME'].tail(7).mean()
                            gym_28d_vol = p_hist_all['VOLUME'].tail(28).mean()
                            gym_acwr = round(gym_7d_vol / gym_28d_vol, 2) if gym_28d_vol > 0 else 1.0
                            g_acwr_icon = "✅" if 0.8 <= gym_acwr <= 1.3 else "⚠️" if (1.3 < gym_acwr <= 1.5) or (0.6 <= gym_acwr < 0.8) else "❌"

                            p_active_rows = p_hist_all[p_hist_all['TOTAL DISTANCE (M)'] > 0]
                            pitch_acwr = round(p_active_rows.iloc[-1].get('ACWR', 1.0), 2) if not p_active_rows.empty else 1.0
                            p_acwr_icon = "✅" if 0.8 <= pitch_acwr <= 1.3 else "⚠️" if (1.3 < pitch_acwr <= 1.5) or (0.6 <= pitch_acwr < 0.8) else "❌"

                            ac_c1, ac_c2 = st.columns(2)
                            with ac_c1: st.markdown(f"#### **Current Gym ACWR:** {g_acwr_icon} {gym_acwr}")
                            with ac_c2: st.markdown(f"#### **Current Pitch ACWR:** {p_acwr_icon} {pitch_acwr}")
                            st.divider()

                            # --- LOGIC PREP ---
                            win_start = s_dt - timedelta(days=21)
                            window_all = master[(master['DATE'] >= win_start) & (master['DATE'] < s_dt)].copy()
                            p_win = window_all[window_all['ATHLETENAME'] == sel_player]

                            if not p_win.empty:
                                p_unit = p_win['UNIT'].iloc[0]
                                u_win = window_all[window_all['UNIT'] == p_unit]
                                intense_sessions = ['Conditioning Day', 'Tactical Prep', 'Match Day']
                                p_active = p_win[p_win['SESSIONTITLE'].isin(intense_sessions)]
                                u_active = u_win[u_win['SESSIONTITLE'].isin(intense_sessions)]
                                group_label = f"{p_unit} Unit" if not u_active.empty else "Squad"

                                label_combined = (str(row.get('TYPE', '')) + " " + str(row.get('CONTEXT', ''))).upper()
                                m_p, m_g = 'TOTAL DISTANCE (M)', 'VOLUME'
                                if any(x in label_combined for x in ['KNEE', 'ANKLE', 'ACL', 'LIGAMENT']): m_p, m_g = 'NO. OF EXP. DEC. (TIMES)', 'LEG_V'
                                elif any(x in label_combined for x in ['HAMSTRING', 'SPRINT']): m_p, m_g = 'SPRINT DISTANCE (M)', 'LEG_V'
                                elif any(x in label_combined for x in ['BACK', 'SPINE', 'LUMBAR']): m_p, m_g = 'TOTAL DISTANCE (M)', 'BACK_V'
                                elif any(x in label_combined for x in ['SHOULDER', 'ACJ']): m_p, m_g = 'TOTAL DISTANCE (M)', 'SH_V'

                                # --- LAYER 2: LOAD DIAGNOSTIC ---
                                st.subheader(f"🕵️ Load Diagnostic (Last 21 Days vs {group_label})")
                                diag_metrics = ['TOTAL DISTANCE (M)', 'HSR DISTANCE (M)']
                                if not any(x in label_combined for x in ['ILLNESS', 'SICK']):
                                    if m_p not in diag_metrics: diag_metrics.append(m_p)
                                    if m_g and m_g in master.columns: diag_metrics.append(m_g)

                                flagged_metrics = []
                                d_cols = st.columns(len(diag_metrics))
                                for j, met in enumerate(diag_metrics):
                                    p_avg = p_active[met].mean() if not p_active.empty else 0
                                    u_avg = u_active[met].mean() if not u_active.empty else 1
                                    diff = ((p_avg / u_avg) - 1) * 100
                                    limit, danger = (15, 30) if 'TOTAL' in met or '_V' in met else (10, 25)
                                    icon = "✅"
                                    if abs(diff) > danger: icon = "❌"; flagged_metrics.append(f"{met.replace(' (M)', '')} spike of {diff:+.1f}%")
                                    elif abs(diff) > limit: icon = "⚠️"; flagged_metrics.append(f"{met.replace(' (M)', '')} variance of {diff:+.1f}%")
                                    with d_cols[j]:
                                        st.metric(f"{icon} {met.replace(' (M)', '').replace('_V', ' VOL')}", f"{p_avg:.0f}", f"{diff:+.1f}% vs Unit", delta_color="normal" if icon=="✅" else "inverse")

                                # --- LAYER 3: RECOVERY ---
                                st.markdown("#### 🛌 Recovery")
                                r_col1, r_col2 = st.columns(2)
                                rest_days = len(p_win[p_win['SESSIONTITLE'].str.contains('Rest Day', case=False, na=False)])
                                rec_days = len(p_win[p_win['SESSIONTITLE'].str.contains('Recovery Session', case=False, na=False)])
                                with r_col1: st.metric("Rest Days (21d)", rest_days)
                                with r_col2: st.metric("Recovery Sessions (21d)", rec_days)

                                # --- LAYER 4: WELLNESS RED FLAGS ---
                                st.subheader("🚩 Wellness Red Flags (21-Day Window)")
                                w_cols = st.columns(3); total_reds = 0; wellness_issues = []
                                for k, w_met in enumerate(['FATIGUE', 'SORENESS', 'SLEEPHOURS']):
                                    with w_cols[k]:
                                        y = len(p_win[(p_win[w_met] >= 5.5) & (p_win[w_met] <= 6.5)]) if w_met != 'SLEEPHOURS' else len(p_win[(p_win[w_met] >= 6.5) & (p_win[w_met] < 7.5)])
                                        r = len(p_win[p_win[w_met] > 6.5]) if w_met != 'SLEEPHOURS' else len(p_win[p_win[w_met] < 6.5])
                                        total_reds += r
                                        if r > 1: wellness_issues.append(w_met.capitalize())
                                        st.markdown(f"**{w_met.capitalize()}**\n⚠️ {y} | ❌ {r}")

                                # --- LAYER 5: MATCH PREPARATION SHIELDING ---
                                st.divider(); st.subheader("⚖️ Match Preparation Shielding")
                                m_data, t_data = p_win[p_win['SESSIONTITLE'].str.contains('Match', case=False, na=False)], p_win[p_win['SESSIONTITLE'].str.contains('Conditioning|Tactical', case=False, na=False)]
                                shield_gap = 0
                                if not m_data.empty and not t_data.empty:
                                    top_train = t_data.nlargest(3, 'TOTAL DISTANCE/MIN (M/MIN)')['TOTAL DISTANCE/MIN (M/MIN)'].mean()
                                    match_int = m_data['TOTAL DISTANCE/MIN (M/MIN)'].mean()
                                    shield_gap = ((match_int / top_train) - 1) * 100
                                    shield_status = "✅ Fully Shielded" if shield_gap < 10 else "⚠️ Under-Prepared" if shield_gap < 25 else "🚩 Critical Gap"
                                    st.metric(shield_status, f"{shield_gap:+.1f}% Intensity Gap", delta_color="inverse")
                                    st.markdown(f"**Shielding Context:** This compares average intensity (m/min) of top 3 training sessions vs match intensity. A gap >25% indicates the body was not prepared for game demands.")
                                else: st.write("Insufficient data for shielding analysis.")

                                # --- LAYER 6: SMARTER POST-INJURY AUDIT ---
                                st.divider(); st.subheader("🏁 Post-Injury Recovery Audit")
                                audit_msg = "Athlete currently in active treatment."
                                is_struggling_reentry = False
                                if pd.notnull(e_dt) and e_dt < master['DATE'].max():
                                    post_win = master[(master['ATHLETENAME'] == sel_player) & (master['DATE'] > e_dt) & (master['DATE'] <= e_dt + timedelta(days=21))]
                                    next_inj = p_inj[p_inj['STARTDATE'] > e_dt].head(1)
                                    days_healthy = (next_inj['STARTDATE'].iloc[0] - e_dt).days if not next_inj.empty else (master['DATE'].max() - e_dt).days
                                    avg_wellness = post_win[['FATIGUE', 'SORENESS']].mean().mean() if not post_win.empty else 0

                                    if days_healthy > 60:
                                        audit_msg = f"✅ **Highly Successful Return:** Player remained injury-free for {days_healthy} days post-clearance with stable wellness (Avg: {avg_wellness:.1f})."
                                    elif avg_wellness > 5.5:
                                        audit_msg = f"⚠️ **Struggling to Cope:** High internal cost (Wellness: {avg_wellness:.1f}) detected during re-entry phase."
                                        is_struggling_reentry = True
                                    else:
                                        audit_msg = f"ℹ️ **Stable Re-entry:** Coping well with post-injury loads. Recovery maintained for {days_healthy} days."
                                st.write(audit_msg)

                                # --- LAYER 7: CONSOLIDATED CLINICAL SYNTHESIS ---
                                st.divider(); st.subheader("🕵️ Clinical Synthesis")
                                findings = []
                                if p_acwr_icon != "✅": findings.append(f"Pitch ACWR instability ({pitch_acwr})")
                                if g_acwr_icon != "✅": findings.append(f"Gym ACWR imbalance ({gym_acwr})")
                                if flagged_metrics: findings.append(f"mechanical load spikes in {', '.join(flagged_metrics)}")
                                if wellness_issues: findings.append(f"heightened internal strain in {', '.join(wellness_issues)}")
                                if shield_gap > 25: findings.append("a critical lack of match-intensity preparation (shielding)")
                                if rest_days < 2: findings.append("insufficient biological recovery windows (rest days)")
                                if is_struggling_reentry: findings.append("poor physiological adaptation during the post-injury re-entry phase")

                                if not findings:
                                    st.info(f"**Correlation Analysis:** All tracked variables—including ACWRs, load distributions, internal wellness, and match shielding—were within optimal ranges. The {row.get('TYPE')} reported on {s_str} suggests an injury out of MDT control, likely caused by a discrete external event or an isolated mechanical failure.")
                                else:
                                    synthesis = f"**Correlation Analysis:** The injury aligns with a systemic convergence of " + ", ".join(findings[:-1]) + ", and " + findings[-1] + ". Collectively, these factors created a state of physical vulnerability where tissue tolerance was exceeded."
                                    st.warning(synthesis)

                                if i == len(p_inj) - 1:
                                    st.divider(); st.success("#### 🚀 Future Prevention Strategy")
                                    months_clear = (master['DATE'].max() - e_dt).days / 30 if pd.notnull(e_dt) else 0
                                    if months_clear > 2.5:
                                        st.write(f"**Strategic Note:** The current management protocol is highly effective, with {sel_player} remaining injury-free for {months_clear:.1f} months. The priority is to maintain current load-to-rest ratios while continuing the specific {m_g.replace('_V','')} strengthening that stabilized the previous {row.get('TYPE')} risk.")
                                    else:
                                        strategy = "Integrate 'Match-Intensity' shielding blocks (115m/min+) to the weekly cycle." if shield_gap > 20 else "Enforce mandatory 48h recovery windows following high-intensity matches."
                                        st.write(f"**Action Plan:** Immediate focus on {strategy} With {p_inj['DAYSLOST'].sum()} days lost this year, {sel_player} requires stricter load auto-regulation based on wellness feedback to prevent further recurrence.")
                            else:
                                st.warning("Insufficient data available for this period.")
                else:
                    st.success(f"✅ No injury records found for {sel_player}.")
            else:
                st.warning("⚠️ No Injury/Illness data detected.")
    
    # --- THIS ELSE BELOW MUST BE AGAINST THE LEFT MARGIN ---
    # It belongs to the very first "if master_data is not None" check.
    else:
        st.info("👋 Upload data to begin.")
