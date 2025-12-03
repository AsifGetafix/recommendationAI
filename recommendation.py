import streamlit as st
import requests
import json
import pandas as pd

# -----------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------

hpe_logo_url = "https://in-media.apjonlinecdn.com/logo/stores/1/HP_New_logo_1.svg"
techpay_logo_url = "https://techpay.ai/wp-content/uploads/2024/10/Artboard-6-1.webp"


custom_css = f"""
<style>

    /* Top header bar */
    .hpe-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 12px 20px;
        justify-content: space-between;
        border-bottom: 1px solid #00a88f40;
        margin-bottom: 15px;
        margin-top: 50px;
    }}

    .hpe-header img {{
        height: 40px;
    }}

    .hpe-header-title {{
        font-size: 24px;
        font-weight: 600;
        color: #0b5d52;
    }}

    .block-container {{
        padding-top: 0 !important;
    }}

</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="hpe-header">
        <img src="{techpay_logo_url}">
        <div class="hpe-header-title">Techpay Recommendation AI</div>
        <img src="{hpe_logo_url}">
    </div>
    """,
    unsafe_allow_html=True
)

st.set_page_config(page_title="TechPay.ai Recommendation Engine", layout="wide")

GROQ_API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

# -----------------------------------------------------------
# NEW: CARD RENDERER
# -----------------------------------------------------------
def render_laptop_card(name, reason, price, specs=None):
    st.markdown(
        f"""
        <div style="
            border: 1px solid #00a88f40;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            background: #ffffff;
            box-shadow: 0px 2px 6px rgba(0,0,0,0.08);
        ">
            <h3 style="color:#0b5d52; margin-bottom:8px;">{name}</h3>
            <p><b>Why this choice:</b> {reason}</p>
            <p><b>Price range:</b> {price}</p>
            { "<p><b>Specs:</b></p>" if specs else "" }
            { ''.join([f"<li><b>{k}:</b> {v}</li>" for k,v in (specs or {}).items()]) }
        </div>
        """,
        unsafe_allow_html=True
    )


def render_comparison_table(recos):
    import pandas as pd

    rows = []
    for r in recos:
        base = {
            "Laptop": r.get("name", ""),
            "Why this choice": r.get("reason", ""),
            "Price": r.get("price", "")
        }
        if "specs" in r:
            base.update(r["specs"])
        rows.append(base)

    st.markdown("### 📊 Side-by-Side Comparison")
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)


# -----------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "requirements" not in st.session_state:
    st.session_state.requirements = {}

if "predefined_mode_done" not in st.session_state:
    st.session_state.predefined_mode_done = False


# -----------------------------------------------------------
# FREE TEXT CHAT LLM FUNCTION
# -----------------------------------------------------------
def ask_llm_predefined(requirements):
    prompt = f"""
You are an expert HP laptop recommendation system.

You MUST respond **only in valid JSON** in the following format:

{{
  "recommendations": [
    {{
      "name": "Laptop 1",
      "reason": "Why this laptop fits",
      "price": "MYR xxxx - xxxx",
      "specs": {{
        "CPU": "Intel ...",
        "RAM": "16GB",
        "Storage": "512GB SSD",
        "Display": "14-inch FHD"
      }}
    }},
    {{
      "name": "Laptop 2",
      "reason": "...",
      "price": "...",
      "specs": {{ ... }}
    }},
    {{
      "name": "Laptop 3",
      "reason": "...",
      "price": "...",
      "specs": {{ ... }}
    }}
  ]
}}

**No explanation. No markdown. Only pure JSON.**

Requirements:
{json.dumps(requirements, indent=2)}
"""

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }
    ).json()

    return response["choices"][0]["message"]["content"]

# -----------------------------------------------------------
# PREDEFINED QUESTION LLM FUNCTION
# -----------------------------------------------------------
def ask_llm_freetext(user_message):
    prompt = f"""
You are an expert advisor specializing exclusively in **HP (Hewlett Packard) laptops**.

Your tasks:
- Answer questions about HP laptops, specifications, features, comparisons.
- If the user asks for a recommendation, suggest ONLY HP laptops and 
- If the user asks about any other brand, explain politely that you only specialize in HP.
- Respond in a conversational, friendly tone.
- **ONLY IF THE USER ASKS recommendations, You MUST respond in valid JSON** in the following format:

{{
  "recommendations": [
    {{
      "name": "Laptop 1",
      "reason": "Why this laptop fits",
      "price": "MYR xxxx - xxxx",
      "specs": {{
        "CPU": "Intel ...",
        "RAM": "16GB",
        "Storage": "512GB SSD",
        "Display": "14-inch FHD"
      }}
    }},
    {{
      "name": "Laptop 2",
      "reason": "...",
      "price": "...",
      "specs": {{ ... }}
    }},
    {{
      "name": "Laptop 3",
      "reason": "...",
      "price": "...",
      "specs": {{ ... }}
    }}
  ]
}}

**No explanation. No markdown. Only pure JSON.**

User query: {user_message}
"""

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    return response.json()["choices"][0]["message"]["content"]


# -----------------------------------------------------------
# SIDEBAR QUESTIONS (UNCHANGED)
# -----------------------------------------------------------
with st.sidebar:
    st.header("HP Laptop Finder")

    cohort = st.selectbox(
        "Cohort?",
        [
            "Entrepreneurs", "Startup", "Remote Freelancers", "Law Firms & Advocates",
            "Creative Professionals", "Studio Users", "Students & Academics",
            "Learn from Home", "Productivity Seekers", "Work from Home"
        ]
    )

    role = st.selectbox(
        "What best describes you/organization?",
        [
            "Individual professional", "Business owner / decision maker",
            "IT manager / procurement team", "Educator or trainer",
            "Student or personal use", "Government or public sector official",
            "Home Office", "Small Office"
        ]
    )

    number_of_users = st.selectbox(
        "How many people will be using HP notebooks?",
        ["Just me (1 user)", "2–10 users", "11–50 users", "51–200 users", "200+ users (large deployment)"]
    )

    work_usage_type = st.selectbox(
        "What kind of work will the notebook(s) be used for?",
        [
            "Everyday office tasks (email, spreadsheets, browsing)",
            "Sales and fieldwork (on-the-go computing)",
            "Remote collaboration and video conferencing",
            "Creative work (graphic design, video editing, animations)",
            "Engineering/technical (CAD, simulations, software dev)",
            "Education/training content delivery",
            "Frontline/retail operations"
        ]
    )

    primary_need = st.selectbox(
        "Which of the following is most important for your work?",
        [
            "Portability and light weight", "Long battery life", "High performance and processing power",
            "Security and manageability", "Rugged/durable build", "Flexible 2-in-1 design with pen input",
            "Cost-effectiveness for bulk deployment"
        ]
    )

    preffered_Screen_size = st.selectbox(
        "Preferred screen size?",
        ["13\" or smaller (portable)", "14\" (balanced)", "15\" or larger"]
    )

    special_features = st.selectbox(
        "Do you need any of these special features?",
        [
            "Touchscreen", "Pen input", "Smartcard reader", "Fingerprint reader",
            "MIL-STD durability", "5G/4G LTE connectivity", "Docking station compatibility",
            "Webcam shutter & noise-canceling mics"
        ]
    )

    familarity = st.selectbox(
        "Preferred HP notebook family?",
        ["No preference", "HP ProBook", "HP EliteBook", "HP Dragonfly", "HP ZBook"]
    )

    if st.button("Get HP Recommendations"):
        st.session_state.requirements = {
            "cohort": cohort,
            "role": role,
            "number_of_users": number_of_users,
            "work_usage_type": work_usage_type,
            "primary_need": primary_need,
            "preffered_Screen_size": preffered_Screen_size,
            "special_features": special_features,
            "familarity": familarity
        }
        st.session_state.predefined_mode_done = True

        reply = ask_llm_predefined(st.session_state.requirements)
        st.session_state.chat.append(("assistant", reply))


# -----------------------------------------------------------
# MAIN CHAT UI
# -----------------------------------------------------------

ASSISTANT_AVATAR = "techpay_icon.png"

for role, msg in st.session_state.chat:

    if role == "user":
        st.chat_message("user").markdown(msg)
        continue

    # ASSISTANT – first try to parse JSON
    try:
        parsed = json.loads(msg)

        # Only render recommendations if valid structure
        if "recommendations" in parsed and isinstance(parsed["recommendations"], list):

            st.chat_message("assistant", avatar=ASSISTANT_AVATAR).markdown("### HP Laptop Recommendations")

            # ---- Render cards ----
            cols = st.columns(3)

            for i, rec in enumerate(parsed["recommendations"]):
                with cols[i]:
                    st.markdown(
                        f"""
                        <div style="
                            border:1px solid #00A88F55;
                            padding:15px;
                            border-radius:12px;
                            background:#F6FFFD;
                            margin-bottom:10px;
                        ">
                            <h4>{rec['name']}</h4>
                            <p><b>Why:</b> {rec['reason']}</p>
                            <p><b>Price:</b> {rec['price']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # ---- Comparison Table ----
            import pandas as pd
            table_data = []
            for rec in parsed["recommendations"]:
                spec = rec["specs"]
                table_data.append({
                    "Laptop": rec["name"],
                    "CPU": spec["CPU"],
                    "RAM": spec["RAM"],
                    "Storage": spec["Storage"],
                    "Display": spec["Display"],
                    "Price": rec["price"]
                })

            df = pd.DataFrame(table_data)
            st.markdown("### 📊 Specification Comparison")
            st.dataframe(df, use_container_width=True)

            continue  # IMPORTANT: Do NOT print raw JSON

    except Exception as e:
        pass  # Not JSON → fall back to normal text

    # Normal assistant text response
    st.chat_message("assistant", avatar=ASSISTANT_AVATAR).markdown(msg)


# Chat Input at bottom
user_input = st.chat_input("Ask anything about HP laptops...")

if user_input:
    st.session_state.chat.append(("user", user_input))

    reply = ask_llm_freetext(user_input)
    st.session_state.chat.append(("assistant", reply))

    st.rerun()

