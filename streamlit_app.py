import os
import io
import json
import tempfile
import streamlit as st

from enhanced_midi_analyzer import EnhancedMIDIAnalyzer
from enhanced_visualizations import EnhancedVisualizer

st.set_page_config(page_title="Enhanced MIDI Analyzer", layout="wide")
st.title("🎵 Enhanced MIDI Analyzer")
st.caption("Analyze MIDI files: key, chords, tempo, melody, density, instruments. View plots and interactive HTML.")

outdir = st.sidebar.text_input("Output directory", value="enhanced_outputs")
os.makedirs(outdir, exist_ok=True)

uploaded = st.file_uploader("Upload a MIDI file (.mid)", type=["mid", "midi"]) 
use_sample = st.sidebar.checkbox("Use sample Pirates.mid from project", value=not uploaded)
run_button = st.sidebar.button("Run Analysis")

status = st.empty()
col1, col2 = st.columns([1,1])

midi_path = None
if uploaded and not use_sample:
	# Save uploaded to temp file
	with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp:
		tmp.write(uploaded.read())
		midi_path = tmp.name
elif use_sample and os.path.exists("Pirates.mid"):
	midi_path = "Pirates.mid"

if run_button:
	if not midi_path:
		st.error("Please upload a MIDI file or enable 'Use sample'.")
		st.stop()
	try:
		status.info("Running analysis...")
		analyzer = EnhancedMIDIAnalyzer(midi_path)
		results = analyzer.run_full_analysis()
		analyzer.save_analysis(outdir)
		status.success(f"Analysis complete. Results saved to {outdir}")
		# Show summary
		with col1:
			st.subheader("Summary")
			key_txt = results.get("key", {}).get("key")
			conf = results.get("key", {}).get("confidence", 0.0)
			scale_txt = ", ".join(results.get("scale_notes", []))
			tempo_val = results.get("initial_tempo_bpm")
			tempo_txt = f"{tempo_val:.2f}" if isinstance(tempo_val, (int, float)) else "N/A"
			ts = results.get('time_signature', {})
			ts_txt = f"{ts.get('numerator','?')}/{ts.get('denominator','?')}"
			duration = results.get("basic", {}).get("duration", 0.0)
			notes_n = results.get("basic", {}).get("total_notes", 0)
			summary_html = f"""
			<p><span style='color:#ff1744; font-weight:700;'>🎼 Key:</span> <span style='color:#ff5252;'>{key_txt}</span></p>
			<p><span style='color:#d500f9; font-weight:700;'>🎯 Confidence:</span> <span style='color:#e040fb;'>{conf:.3f}</span></p>
			<p><span style='color:#00e5ff; font-weight:700;'>🎶 Scale notes:</span> <span style='color:#18ffff;'>{scale_txt}</span></p>
			<p><span style='color:#ffea00; font-weight:700;'>⏱️ Tempo (BPM):</span> <span style='color:#ffd600;'>{tempo_txt}</span></p>
			<p><span style='color:#00e676; font-weight:700;'>🕒 Time signature:</span> <span style='color:#69f0ae;'>{ts_txt}</span></p>
			<p><span style='color:#2979ff; font-weight:700;'>⌛ Duration (s):</span> <span style='color:#82b1ff;'>{duration:.2f}</span></p>
			<p><span style='color:#ff4081; font-weight:700;'>🎹 Total notes:</span> <span style='color:#ff80ab;'>{notes_n}</span></p>
			"""
			st.markdown(summary_html, unsafe_allow_html=True)
			st.image(os.path.join(outdir, "key_analysis.png"), caption="Key Analysis", use_column_width=True)
			st.image(os.path.join(outdir, "chord_analysis.png"), caption="Chords Timeline", use_column_width=True)
		with col2:
			st.subheader("Rhythm & Instruments")
			st.image(os.path.join(outdir, "rhythm_analysis.png"), caption="Tempo & Density", use_column_width=True)
			st.image(os.path.join(outdir, "instrument_analysis.png"), caption="Instruments", use_column_width=True)
		st.subheader("Melody")
		st.image(os.path.join(outdir, "melody_analysis.png"), caption="Melodic Contour & Intervals", use_column_width=True)
		# Data downloads
		st.subheader("Data files")
		for fname in [
			"tempo_changes.csv",
			"chords.csv",
			"note_density.csv",
			"pitch_class_histogram.csv",
			"melody_notes.csv",
			"analysis_results.json",
		]:
			fpath = os.path.join(outdir, fname)
			if os.path.exists(fpath):
				st.download_button(label=f"Download {fname}", data=open(fpath, "rb").read(), file_name=fname)
		# Interactive HTML links
		st.subheader("Interactive")
		for html in ["demo_interactive_chords.html", "demo_sonification.html", "demo_3d_piano_roll.html"]:
			h = os.path.join(outdir, html)
			if os.path.exists(h):
				st.markdown(f"- {html}: {os.path.abspath(h)}")
	except Exception as e:
		st.error(f"Analysis failed: {e}")
