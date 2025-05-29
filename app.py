# Streamlit page config must come before any Streamlit commands
import streamlit as st
st.set_page_config(page_title="Smarter Campaign Link Generator Chatbot")

# Other imports
import openai
import pandas as pd
from datetime import datetime
import os
import json
from openai import OpenAI

# Load OpenAI API key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Load network index and appindex
with open("networkindex.json") as f:
    raw_networkindex = json.load(f)
    network_index = raw_networkindex if isinstance(raw_networkindex, dict) else {}

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
                "ams_id": {"type": "string"},
                "video_format": {"type": "string"},
                "subtargeting": {"type": "string"},
                "x_field": {"type": "string"},
                "lp_url": {"type": "string"}
            },
            "required": [
                "brand", "region", "platform", "campaign", "budget_code", "agency",
                "buying_platform", "publisher", "publisher_subsite", "targeting", "vertical", "offer",
                "ams_id", "video_format", "subtargeting", "x_field", "lp_url"
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
st.markdown("### 🧠 Smart Campaign Field Suggestion")
campaign_hint = st.text_input("Describe your campaign idea", key="campaign_hint", placeholder="e.g., Display campaign in CA for PS on Reddit")

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


# Generate AF links using appindex base + networkindex parameters
def generate_af_links(network_id, platform, parsed):
    warnings = []
    network_search_key = f"{parsed['agency']}{parsed['publisher']}"
    network_entry = network_index.get(network_search_key.upper())
    if not network_entry:
        warnings.append(f"⚠️ No entry found for network_id '{network_id}' in networkindex.json")
    platform_key = f"{parsed['brand']}-{parsed['region']}-{parsed['platform']}"
    app_entry = app_index.get(platform_key)
    if not app_entry:
        warnings.append(f"⚠️ No entry found for platform key '{platform_key}' in appindex.json")
        app_entry = {}

    click_base = app_entry.get("click", "https://amaya.onelink.me/197923601")
    imp_base = app_entry.get("imp", "https://impression.amaya.com")

    if not network_entry:
        return {"click": click_base, "imp": imp_base}

    platform_key_click = f"{platform.lower()}click"
    platform_key_imp = f"{platform.lower()}imp"

    click_template = network_entry.get(platform_key_click, "")
    imp_template = network_entry.get(platform_key_imp, "")

    for key, val in parsed.items():
        if isinstance(val, str):
            click_template = click_template.replace(f"{{{key}}}", val)
            imp_template = imp_template.replace(f"{{{key}}}", val)

    final_click = f"{click_base}{click_template}" if click_template else click_base
    final_imp = f"{imp_base}{imp_template}" if imp_template else imp_base

    for warning in warnings:
        st.warning(warning)

    return {"click": final_click, "imp": final_imp}

suggested = st.session_state.get("suggested_fields", {})
st.markdown("### 🎛️ Auto-filled Campaign Input Form (Optional)")
with st.expander("Click to open manual form"):
    brand = st.selectbox("Brand", ["PS", "PC"], index=["PS", "PC"].index(suggested.get("brand", "PS")))
    region = st.selectbox("Region", ["UK", "CA", "DE", "ES", "EU", "BR", "DK", "RO"], index=["UK", "CA", "DE", "ES", "EU", "BR", "DK", "RO"].index(suggested.get("region", "UK")))
    platform = st.selectbox("Platform", ["iOS", "DIS", "AND", "MOB", "DESK"], index=["iOS", "DIS", "AND", "MOB", "DESK"].index(suggested.get("platform", "DIS")))
    campaign = st.text_input("Campaign Name", suggested.get("campaign", "STARSSEASON"))
    budget_code = st.selectbox("Budget Code", ["G", "TPP", "GVOD", "PAIDSOCIAL", "AFFILIATES"])
    agency = st.selectbox("Agency", ["TSG", "CLEARPIER", "TAPPX", "MOBSUCCESS", "EKSMEDIA", "WEBMEDIAAGENCY", "KYPI"])
    buying_platform = st.selectbox("Buying Platform", ["DIRECT", "DV360", "Mediamath"], index=["DIRECT", "DV360", "Mediamath"].index(suggested.get("buying_platform", "DV360")))
    publisher = st.selectbox("Publisher", ["MOBSUCCESS", "REDDIT", "OGURY", "TEADS", "SPOTIFY", "SNAPCHAT", "FACEBOOK","YOUTUBE"], index=["MOBSUCCESS", "REDDIT", "OGURY", "TEADS", "SPOTIFY", "SNAPCHAT", "FACEBOOK","YOUTUBE"].index(suggested.get("publisher", "YOUTUBE")))
    publisher_subsite = st.selectbox("Publisher's Sub-site", ["RON", "ROS", "ALL"])
    targeting = st.selectbox("Targeting", ["ALL", "RON", "M1845"])
    vertical = st.selectbox("Vertical", ["POKER", "CASINO"], index=["POKER", "CASINO"].index(suggested.get("vertical", "POKER")))
    offer = st.selectbox("Offer", ["GENERIC", "NO", "BONUS"])
    ams_id = st.text_input("AMS ID", "AMSID")
    video_format = st.selectbox("Format", ["VOD6", "VOD15LAN", "VOD20LAN"])
    subtargeting = st.selectbox("Sub-targeting", ["P", "E", "R"])
    x_field = st.text_input("X Field", "X")
    lp_url = st.text_input("Landing Page URL", "https://www.pokerstars.uk/poker/pages/stars-season/")

    if st.button("Generate from Dropdowns"):
        full_input = f"Generate link for {brand} {region} {platform} {campaign} via {buying_platform} on {publisher} and {publisher_subsite} with AMS ID {ams_id}, LP {lp_url}, offer {offer}, vertical {vertical}, Targeting {targeting}, Format {video_format}, Sub-targeting {subtargeting} and X Field as {x_field}, Budget Code {budget_code}, Agency {agency}."
        st.session_state["dropdown_input"] = full_input


# Main app logic
st.title("🎯 Smarter Campaign Link Generator Chatbot")
descriptions = st.text_area("Paste campaign description(s):", value=st.session_state.get("dropdown_input", ""), height=200)
if st.button("Generate Links") and descriptions:
    rows = []
    for line in descriptions.strip().split("\n"):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Extract structured campaign parameters for link generation."},
                    {"role": "user", "content": line}
                ],
                functions=function_schema,
                function_call="auto"
            )
            args = response.choices[0].message.function_call.arguments
            parsed = json.loads(args)

            # Placement code construction
            placement = "-".join([
                parsed["brand"], parsed["region"], parsed["platform"], parsed["campaign"],
                parsed["budget_code"], parsed["agency"], parsed["buying_platform"], parsed["publisher"],
                parsed["publisher_subsite"], parsed["targeting"], parsed["vertical"], parsed["offer"],
                parsed["ams_id"], parsed["video_format"], parsed["subtargeting"], parsed["x_field"]
            ])

            click_tag = f"{parsed['lp_url']}?source={parsed['ams_id']}&utm_medium=display&utm_source={parsed['publisher'].lower()}&utm_campaign={parsed['campaign'].lower()}&review=true"

            af_links = generate_af_links(parsed["buying_platform"], parsed["platform"], parsed)

            rows.append({
                "Input": line,
                "Placement Code": placement,
                "Click Tag": click_tag,
                "Appsflyer Click": af_links["click"],
                "Appsflyer IMP": af_links["imp"]
            })
        except Exception as e:
            rows.append({
                "Input": line,
                "Placement Code": "ERROR",
                "Click Tag": str(e),
                "Appsflyer Click": "",
                "Appsflyer IMP": ""
            })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", df.to_csv(index=False), "campaign_links.csv")
