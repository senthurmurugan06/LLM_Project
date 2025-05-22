import streamlit as st
import pandas as pd
import ast
from streamlit_lightweight_charts import renderLightweightCharts
import google.generativeai as genai
import os

# Load data
def load_data(csv_path):
    df = pd.read_csv(csv_path)
    # Parse Support and Resistance columns (convert string lists to actual lists)
    def parse_list(val):
        try:
            return ast.literal_eval(val) if pd.notnull(val) and val != '' else []
        except Exception:
            return []
    df['Support'] = df['Support'].apply(parse_list)
    df['Resistance'] = df['Resistance'].apply(parse_list)
    return df

def prepare_chart_data(df):
    # Candlestick data
    candles = [
        {
            "time": row['timestamp'],
            "open": row['open'],
            "high": row['high'],
            "low": row['low'],
            "close": row['close']
        }
        for _, row in df.iterrows()
    ]
    # Markers
    markers = []
    for i, row in df.iterrows():
        if row['direction'] == 'LONG':
            markers.append({
                "time": row['timestamp'],
                "position": "belowBar",
                "color": "green",
                "shape": "arrowUp",
                "text": "LONG"
            })
        elif row['direction'] == 'SHORT':
            markers.append({
                "time": row['timestamp'],
                "position": "aboveBar",
                "color": "red",
                "shape": "arrowDown",
                "text": "SHORT"
            })
        else:
            markers.append({
                "time": row['timestamp'],
                "position": "aboveBar",
                "color": "yellow",
                "shape": "circle",
                "text": "NONE"
            })
    # Support band (green)
    support_band = [
        {
            "time": row['timestamp'],
            "value": min(row['Support']) if row['Support'] else None,
            "color": "rgba(0,255,0,0.2)"
        }
        for _, row in df.iterrows()
    ]
    support_band_upper = [
        {
            "time": row['timestamp'],
            "value": max(row['Support']) if row['Support'] else None,
            "color": "rgba(0,255,0,0.2)"
        }
        for _, row in df.iterrows()
    ]
    # Resistance band (red)
    resistance_band = [
        {
            "time": row['timestamp'],
            "value": min(row['Resistance']) if row['Resistance'] else None,
            "color": "rgba(255,0,0,0.2)"
        }
        for _, row in df.iterrows()
    ]
    resistance_band_upper = [
        {
            "time": row['timestamp'],
            "value": max(row['Resistance']) if row['Resistance'] else None,
            "color": "rgba(255,0,0,0.2)"
        }
        for _, row in df.iterrows()
    ]
    return candles, markers, support_band, support_band_upper, resistance_band, resistance_band_upper

# Gemini Chatbot logic
def gemini_chat(question, df):
    api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key not found. Please set it in Streamlit secrets or as an environment variable."
    genai.configure(api_key=api_key)
    # Give Gemini a summary of the data columns for context
    context = f"""
    You are a financial data assistant. The user is asking about TSLA stock data with the following columns: timestamp, direction, Support, Resistance, open, high, low, close, volume.\n
    Example row:\n{df.iloc[0].to_dict()}\n
    Answer the user's question using the data provided.
    """
    prompt = context + "\nUser question: " + question
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

def main():
    st.set_page_config(page_title="TSLA Dashboard", layout="wide")
    st.title("TSLA Candlestick Dashboard & Gemini Chatbot")

    tab1, tab2 = st.tabs(["📈 Chart Dashboard", "🤖 Gemini Chatbot"])

    with tab1:
        st.header("Candlestick Chart with Markers and Bands")
        df = load_data("TSLA_data - Sheet1.csv")
        candles, markers, support_band, support_band_upper, resistance_band, resistance_band_upper = prepare_chart_data(df)
        chart_series = [
            {"type": "Candlestick", "data": candles},
            {"type": "Line", "data": support_band, "color": "green", "lineWidth": 2, "title": "Support Lower"},
            {"type": "Line", "data": support_band_upper, "color": "green", "lineWidth": 2, "title": "Support Upper"},
            {"type": "Line", "data": resistance_band, "color": "red", "lineWidth": 2, "title": "Resistance Lower"},
            {"type": "Line", "data": resistance_band_upper, "color": "red", "lineWidth": 2, "title": "Resistance Upper"},
        ]
        chart_options = {"height": 600, "rightPriceScale": {"visible": True}}
        renderLightweightCharts([
            {"series": chart_series, "markers": markers, "options": chart_options}
        ])

    with tab2:
        st.header("Ask Gemini about TSLA Data")
        df = load_data("TSLA_data - Sheet1.csv")
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        user_input = st.text_input("Ask a question about TSLA data:")
        if st.button("Ask") and user_input:
            with st.spinner("Gemini is thinking..."):
                answer = gemini_chat(user_input, df)
            st.session_state.chat_history.append((user_input, answer))
        for q, a in st.session_state.chat_history:
            st.markdown(f"**You:** {q}")
            st.markdown(f"**Gemini:** {a}")
        st.info("Your API key should be set in Streamlit secrets as 'GEMINI_API_KEY'.")

if __name__ == "__main__":
    main() 