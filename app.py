# Streamlit page config must come before any Streamlit commands
import streamlit as st
st.set_page_config(page_title="Smarter Campaign Link Generator Chatbot")

# Other imports
import openai
import pandas as pd
from datetime import datetime
import os
import json
import urllib.parse
from openai import OpenAI

# Load OpenAI API key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Load network index and appindex
with open("networkindex.json") as f:
    raw_networkindex = json.load(f)
    network_index = raw_networkindex if isinstance(raw_networkindex, dict) else {}

with open("appindex.json") as f:
    raw_appindex = json.load(f)
    app_index = raw_appindex if isinstance(raw_appindex, dict) else {}

campaign_type = ["display", "paidsocial","affiliate"]
def infer_campaign_type(text):
    lower_text = text.lower()
    if "affiliate" in lower_text:
        return "affiliate"
    elif "social" in lower_text:
        return "paidsocial"
    else:
        return "display"


# Safe index helper
def safe_index(options, value, default=0):
    try:
        return options.index(value)
    except ValueError:
        return default

# Brand, Region, Platform maps
brand_map = {
    "Pokerstars": "PS", "Full Tilt": "FT", "Pokerstars Play": "PPLAY", "Pokerstars Casino": "PC",
    "FoxBet": "FXB", "SkyBet": "SB", "Sport": "SPORT", "Pokerstars Sports": "PSS",
    "Masterbrand": "MB", "Pokerstars Dojo": "PSDJ", "Pokerstars News": "PSN"
}
region_map = {
    "Canada": "CA", "France": "FR", "Germany": "DE", "Spain": "ES", "United Kingdom": "UK",
    "European Union": "EU", "Brazil": "BR", "Denmark": "DK", "Romania": "RO",
    "Ontario": "CAON", "Pennsylvania": "USPA", "New Jersey": "USNJ", "Michigan": "USMI"
}
platform_map = {
    "iOS": "iOS", "Android": "AND", "Desktop": "DESK", "Mobile Web": "MOB", "All Devices": "DIS"
}

# Function schema for GPT
function_schema = [
    {
        "name": "extract_campaign_fields",
        "description": "Extracts structured campaign fields from free text.",
        "parameters": {
            "type": "object",
            "properties": {
                "brand": {"type": "string"},
                "region": {"type": "string"},
                "platform": {"type": "string"},
                "campaign": {"type": "string"},
                "budget_code": {"type": "string"},
                "agency": {"type": "string"},
                "buying_platform": {"type": "string"},
                "publisher": {"type": "string"},
                "publisher_subsite": {"type": "string"},
                "targeting": {"type": "string"},
                "vertical": {"type": "string"},
                "offer": {"type": "string"},
                "formats": {"type": "array", "items": {"type": "string"}},
                "subtargeting": {"type": "string"},
                "x_field": {"type": "string"},
                "lp_url": {"type": "string"}
            },
            "required": [
                "brand", "region", "platform", "campaign", "budget_code", "agency",
                "buying_platform", "publisher", "publisher_subsite", "targeting", "vertical",
                "offer", "formats", "subtargeting", "x_field", "lp_url"
            ]
        }
    }
]

# Load app index
with open("appindex.json") as f:
    raw_appindex = json.load(f)
    app_index = raw_appindex if isinstance(raw_appindex, dict) else {}

# Brand code mapping for learning and abbreviation
brand_map = {
    "Pokerstars": "PS",
    "Full Tilt": "FT",
    "Pokerstars Play": "PPLAY",
    "Pokerstars Casino": "PC",
    "FoxBet": "FXB",
    "SkyBet": "SB",
    "Sport": "SPORT",
    "Pokerstars Sports": "PSS",
    "Masterbrand": "MB",
    "Pokerstars Dojo": "PSDJ",
    "Pokerstars News": "PSN"
}

# Region code mapping
region_map = {
    "Canada": "CA",
    "France": "FR",
    "Germany": "DE",
    "Spain": "ES",
    "United Kingdom": "UK",
    "European Union": "EU",
    "Brazil": "BR",
    "Denmark": "DK",
    "Romania": "RO",
    "Ontario": "CAON",
    "Pennsylvania": "USPA",
    "New Jersey": "USNJ",
    "Michigan": "USMI"
}

# Platform code mapping
platform_map = {
    "iOS": "iOS",
    "Android": "AND",
    "Desktop": "DESK",
    "Mobile Web": "MOB",
    "All Devices": "DIS"
}

# Utility function to safely resolve index

def safe_index(options, value, default=0):
    try:
        return options.index(value)
    except ValueError:
        return default

# Suggest Fields Block
st.markdown("### 🧠 Smart Campaign Field Suggestion, get hints or paste Generate link for PS UK DIS STARSSEASON via TRADEDESK on TRADEDESK and RON, LP https://www.pokerstars.uk/poker/pages/stars-season/, offer GENERIC, vertical POKER, Targeting ALL, Format 320x50, 480x320, Sub-targeting R and X Field as X, Budget Code G, Agency TSG.")
campaign_hint = st.text_input("Describe your campaign idea or simply copy paste this", key="campaign_hint", placeholder="e.g., Display campaign in CA for PS on Reddit")

suggest_fields_schema = [
    {
        "name": "suggest_campaign_fields",
        "description": "Suggest likely campaign fields from a freeform marketing description",
        "parameters": {
            "type": "object",
            "properties": {
                "brand": {"type": "string"},
                "region": {"type": "string"},
                "platform": {"type": "string"},
                "campaign": {"type": "string"},
                "buying_platform": {"type": "string"},
                "publisher": {"type": "string"},
                "vertical": {"type": "string"}
            },
            "required": ["brand", "region", "platform"]
        }
    }
]

if st.button("Suggest Fields") and campaign_hint:
    try:
        suggestion_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract likely structured campaign fields from a marketing prompt."},
                {"role": "user", "content": campaign_hint}
            ],
            functions=suggest_fields_schema,
            function_call="auto"
        )
        suggested = json.loads(suggestion_response.choices[0].message.function_call.arguments)

        # Normalize suggested fields using maps
        if "brand" in suggested:
            suggested["brand"] = brand_map.get(suggested["brand"], suggested["brand"]).upper()
        if "region" in suggested:
            suggested["region"] = region_map.get(suggested["region"], suggested["region"]).upper()
        if "platform" in suggested:
            suggested["platform"] = platform_map.get(suggested["platform"], suggested["platform"])
        if "publisher" in suggested:
            suggested["publisher"] = suggested["publisher"].upper()
        if "buying_platform" in suggested:
            suggested["buying_platform"] = suggested["buying_platform"].upper()
        if "vertical" in suggested:
            suggested["vertical"] = suggested["vertical"].upper()

        st.session_state["suggested_fields"] = suggested
        st.success("✅ Fields suggested. Scroll down to see them in the form.")
        st.json(suggested)
    except Exception as e:
        st.error(f"❌ Suggestion failed: {e}")


# 📌 Generate AF links

def generate_af_links(network_id, platform, parsed):
    warnings = []
    network_search_key = f"{parsed['agency']}{parsed['publisher']}"
    network_entry = network_index.get(network_search_key.upper())
    if not network_entry:
        warnings.append(f"⚠️ No entry found for network_id '{network_search_key}' in networkindex.json")
    platform_key = f"{parsed['brand']}-{parsed['region']}-{parsed['platform']}"
    app_entry = app_index.get(platform_key)
    if not app_entry:
        warnings.append(f"⚠️ No entry found for platform key '{platform_key}' in appindex.json")
        app_entry = {}

    click_base = app_entry.get("click", "https://amaya.onelink.me/197923601")
    imp_base = app_entry.get("imp", "https://impression.amaya.com")
    platform_key_click = platform.lower() + "click"
    platform_key_imp = platform.lower() + "imp"

    if platform_key_click == "disclick":
        platform_key_click = "andclick"
        no_imp = True

    click_template = network_entry.get(platform_key_click, "") if network_entry else ""
    imp_template = network_entry.get(platform_key_imp, "") if network_entry else ""

    for key, val in parsed.items():
        if isinstance(val, str):
            click_template = click_template.replace(f"{{{{{key}}}}}", val)
            imp_template = imp_template.replace(f"{{{{{key}}}}}", val)

    encoded_lp = urllib.parse.quote(f"{parsed['lp_url']}?source={ams_id}&utm_medium=display&utm_source={parsed['publisher'].lower()}&utm_campaign={parsed['campaign'].lower()}&review=true") if parsed.get("lp_url") else ""
    print(encoded_lp)
    extra_params = f"&c={placement}&af_sub4={ams_id}"
    if encoded_lp:
        extra_params += f"&af_android_url={encoded_lp}&af_ios_url={encoded_lp}&af_web_dp={encoded_lp}"

    final_click = f"{click_base}{click_template}{extra_params}" if click_template else f"{click_base}{extra_params}"
    final_imp = f"{imp_base}{imp_template}{extra_params}" if imp_template else f"{imp_base}{extra_params}"

    if no_imp == True: 
        final_imp = ""
    else: 
        final_imp

    for w in warnings:
        st.warning(w)

    return {"click": final_click, "imp": final_imp}

# 🧠 Text area input
st.title("🎯 Smarter Campaign Link Generator Chatbot")
descriptions = st.text_area("Paste campaign description:", height=150)

if st.button("Generate Links") and descriptions:
    rows = []
    campaign_type = infer_campaign_type(descriptions)

    amsid_path = "ams_ids_partitioned.json"
    if os.path.exists(amsid_path):
        with open(amsid_path) as f:
            all_ams_data = json.load(f)
            ams_data = all_ams_data.get(campaign_type, [])
    else:
        ams_data = []
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract structured campaign parameters for link generation."},
                {"role": "user", "content": descriptions.strip()}
            ],
            functions=function_schema,
            function_call="auto"
        )
        args = response.choices[0].message.function_call.arguments
        parsed = json.loads(args)
       
        # Fetch unused AMS IDs from json list
        available_ams = [entry for entry in ams_data if entry.get("used") is False]
        print(available_ams)
        print(parsed["formats"])
        if len(available_ams) < len(parsed["formats"]):
            st.error("Not enough unused AMS IDs available.")
        else:
            for fmt in parsed["formats"]:
                ams_entry = available_ams.pop(0)
                ams_id = ams_entry["id"]
                ams_entry["used"] = True

                placement = "-".join([
                    parsed["brand"], parsed["region"], parsed["platform"], parsed["campaign"],
                    parsed["budget_code"], parsed["agency"], parsed["buying_platform"], parsed["publisher"],
                    parsed["publisher_subsite"], parsed["targeting"], parsed["vertical"], parsed["offer"],
                    ams_id, fmt, parsed["subtargeting"], parsed["x_field"]
                ])

                click_tag = f"{parsed['lp_url']}?source={ams_id}&utm_medium=display&utm_source={parsed['publisher'].lower()}&utm_campaign={parsed['campaign'].lower()}&review=true"

                af_links = generate_af_links(parsed["buying_platform"], parsed["platform"], {
                    **parsed, "ams_id": ams_id, "video_format": fmt
                })

                rows.append({
                    "Placement Code": placement,
                    "Click Tag": click_tag,
                    "Appsflyer Click": af_links["click"],
                    "Appsflyer IMP": af_links["imp"]
                })

            # Save updated AMS ID list
            with open(amsid_path, "w") as f:
                json.dump(ams_data, f, indent=2)

    except Exception as e:
        rows.append({"Placement Code": "ERROR", "Click Tag": str(e), "Appsflyer Click": "", "Appsflyer IMP": ""})

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", df.to_csv(index=False), "campaign_links.csv")
