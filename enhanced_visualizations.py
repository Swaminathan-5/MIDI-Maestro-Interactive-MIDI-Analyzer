#!/usr/bin/env python3
"""
Enhanced Visualizations for MIDI Analysis
3D Piano Roll, Interactive Charts, and Advanced Plotting
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
import json
from pathlib import Path

# Note: Do not call init_notebook_mode in Streamlit/CLI contexts.

class EnhancedVisualizer:
    """Advanced visualization system for MIDI analysis"""
    
    def __init__(self, output_dir: str = "enhanced_outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def create_3d_piano_roll(self, midi_data: Dict, filename: str = "3d_piano_roll"):
        """Create interactive 3D piano roll visualization"""
        try:
            # Extract note data
            notes = midi_data.get('notes', [])
            if not notes:
                return None
                
            # Prepare 3D data
            x = []  # Time
            y = []  # Pitch
            z = []  # Velocity
            colors = []  # Duration-based colors
            
            for note in notes:
                x.append(note['start_time'])
                y.append(note['pitch'])
                z.append(note['velocity'])
                
                # Color based on duration
                duration = note['end_time'] - note['start_time']
                colors.append(duration)
            
            # Create 3D scatter plot
            fig = go.Figure(data=[go.Scatter3d(
                x=x, y=y, z=z,
                mode='markers',
                marker=dict(
                    size=5,
                    color=colors,
                    colorscale='Viridis',
                    opacity=0.8,
                    colorbar=dict(title="Duration")
                ),
                text=[f"Note: {note['pitch']}<br>Time: {note['start_time']:.2f}s<br>Velocity: {note['velocity']}" 
                      for note in notes],
                hovertemplate='<b>%{text}</b><extra></extra>'
            )])
            
            fig.update_layout(
                title=f"3D Piano Roll - {filename}",
                scene=dict(
                    xaxis_title="Time (seconds)",
                    yaxis_title="Pitch (MIDI note)",
                    zaxis_title="Velocity",
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.5)
                    )
                ),
                width=1000,
                height=800
            )
            
            # Save as HTML for interactivity
            html_path = self.output_dir / f"{filename}_3d_piano_roll.html"
            fig.write_html(str(html_path))
            
            # Also save as static PNG
            png_path = self.output_dir / f"{filename}_3d_piano_roll.png"
            fig.write_image(str(png_path))
            
            return str(html_path)
            
        except Exception as e:
            print(f"Error creating 3D piano roll: {e}")
            return None
    
    def create_interactive_chord_progressions(self, chord_data: Dict, filename: str = "interactive_chords"):
        """Create interactive chord progression visualization with audio playback"""
        try:
            chords = chord_data.get('chord_progressions', [])
            if not chords:
                return None
            
            # Create chord timeline
            fig = go.Figure()
            
            # Add chord blocks
            for i, chord_info in enumerate(chords):
                chord = chord_info['chord']
                start_time = chord_info['start_time']
                duration = chord_info.get('duration', 1.0)
                
                fig.add_shape(
                    type="rect",
                    x0=start_time,
                    y0=0,
                    x1=start_time + duration,
                    y1=1,
                    fillcolor="lightblue",
                    opacity=0.7,
                    line=dict(color="black", width=1)
                )
                
                # Add chord label
                fig.add_annotation(
                    x=start_time + duration/2,
                    y=0.5,
                    text=chord,
                    showarrow=False,
                    font=dict(size=14, color="black")
                )
            
            fig.update_layout(
                title=f"Interactive Chord Progressions - {filename}",
                xaxis_title="Time (seconds)",
                yaxis_title="Chords",
                yaxis=dict(range=[0, 1], showticklabels=False),
                width=1200,
                height=400,
                showlegend=False
            )
            
            # Add play button functionality
            fig.add_annotation(
                x=0.02,
                y=0.98,
                xref="paper",
                yref="paper",
                text="▶️ Play",
                showarrow=False,
                font=dict(size=16, color="green"),
                bgcolor="white",
                bordercolor="green",
                borderwidth=2
            )
            
            # Save interactive HTML
            html_path = self.output_dir / f"{filename}_interactive_chords.html"
            fig.write_html(str(html_path))
            
            return str(html_path)
            
        except Exception as e:
            print(f"Error creating interactive chord progressions: {e}")
            return None
    
    def create_comparative_analysis(self, midi_files: List[Dict], filename: str = "comparative_analysis"):
        """Create side-by-side comparison of multiple MIDI files"""
        try:
            if len(midi_files) < 2:
                return None
            
            # Create subplots for comparison
            fig = make_subplots(
                rows=len(midi_files),
                cols=3,
                subplot_titles=[f"{f['name']} - Key, Tempo, Complexity" for f in midi_files],
                specs=[[{"type": "pie"}, {"type": "bar"}, {"type": "scatter"}] for _ in midi_files]
            )
            
            for i, midi_file in enumerate(midi_files):
                row = i + 1
                
                # Key distribution (pie chart)
                key_data = midi_file.get('key_analysis', {})
                if key_data:
                    keys = list(key_data.keys())
                    values = list(key_data.values())
                    fig.add_trace(
                        go.Pie(labels=keys, values=values, name=f"{midi_file['name']} - Key"),
                        row=row, col=1
                    )
                
                # Tempo analysis (bar chart)
                tempo_data = midi_file.get('rhythm_analysis', {}).get('tempo_changes', [])
                if tempo_data:
                    tempos = [t['tempo'] for t in tempo_data]
                    times = [t['time'] for t in tempo_data]
                    fig.add_trace(
                        go.Bar(x=times, y=tempos, name=f"{midi_file['name']} - Tempo"),
                        row=row, col=2
                    )
                
                # Note density over time (scatter)
                notes = midi_file.get('notes', [])
                if notes:
                    times = [n['start_time'] for n in notes]
                    pitches = [n['pitch'] for n in notes]
                    fig.add_trace(
                        go.Scatter(x=times, y=pitches, mode='markers', 
                                 name=f"{midi_file['name']} - Notes", opacity=0.6),
                        row=row, col=3
                    )
            
            fig.update_layout(
                title=f"Comparative Analysis - {len(midi_files)} MIDI Files",
                height=300 * len(midi_files),
                showlegend=True
            )
            
            # Save interactive HTML
            html_path = self.output_dir / f"{filename}_comparative.html"
            fig.write_html(str(html_path))
            
            return str(html_path)
            
        except Exception as e:
            print(f"Error creating comparative analysis: {e}")
            return None
    
    def create_real_time_analysis_display(self, analysis_data: Dict, filename: str = "realtime_analysis"):
        """Create real-time analysis display components"""
        try:
            # Create dashboard-style layout
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=["Live Tempo", "Live Key Changes", "Live Note Density", "Live Chord Progressions"],
                specs=[[{"type": "scatter"}, {"type": "bar"}],
                       [{"type": "scatter"}, {"type": "scatter"}]]
            )
            
            # Live tempo tracking
            tempo_data = analysis_data.get('rhythm_analysis', {}).get('tempo_changes', [])
            if tempo_data:
                times = [t['time'] for t in tempo_data]
                tempos = [t['tempo'] for t in tempo_data]
                fig.add_trace(
                    go.Scatter(x=times, y=tempos, mode='lines+markers', 
                             name="Live Tempo", line=dict(color="red", width=3)),
                    row=1, col=1
                )
            
            # Live key changes
            key_data = analysis_data.get('key_analysis', {})
            if key_data:
                keys = list(key_data.keys())
                values = list(key_data.values())
                fig.add_trace(
                    go.Bar(x=keys, y=values, name="Key Distribution", marker_color="blue"),
                    row=1, col=2
                )
            
            # Live note density
            notes = analysis_data.get('notes', [])
            if notes:
                # Group notes by time windows
                time_windows = np.linspace(0, max(n['end_time'] for n in notes), 50)
                densities = []
                for i in range(len(time_windows)-1):
                    count = sum(1 for n in notes if time_windows[i] <= n['start_time'] < time_windows[i+1])
                    densities.append(count)
                
                fig.add_trace(
                    go.Scatter(x=time_windows[:-1], y=densities, mode='lines', 
                             name="Note Density", line=dict(color="green", width=2)),
                    row=2, col=1
                )
            
            # Live chord progressions
            chords = analysis_data.get('chord_progressions', [])
            if chords:
                times = [c['start_time'] for c in chords]
                chord_names = [c['chord'] for c in chords]
                fig.add_trace(
                    go.Scatter(x=times, y=chord_names, mode='markers', 
                             name="Chords", marker=dict(size=10, color="purple")),
                    row=2, col=2
                )
            
            fig.update_layout(
                title=f"Real-Time Analysis Dashboard - {filename}",
                height=800,
                showlegend=True
            )
            
            # Save interactive HTML
            html_path = self.output_dir / f"{filename}_realtime.html"
            fig.write_html(str(html_path))
            
            return str(html_path)
            
        except Exception as e:
            print(f"Error creating real-time analysis display: {e}")
            return None
    
    def create_sonification_visualization(self, analysis_data: Dict, filename: str = "sonification"):
        """Create visualization for sonification data"""
        try:
            # Extract musical features for sonification
            notes = analysis_data.get('notes', [])
            chords = analysis_data.get('chord_progressions', [])
            tempo_data = analysis_data.get('rhythm_analysis', {}).get('tempo_changes', [])
            
            # Create sonification parameters
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=["Pitch Sonification", "Rhythm Sonification", "Harmony Sonification", "Dynamics Sonification"]
            )
            
            # Pitch sonification - frequency mapping
            if notes:
                times = [n['start_time'] for n in notes]
                frequencies = [440 * (2 ** ((n['pitch'] - 69) / 12)) for n in notes]  # Convert MIDI to Hz
                fig.add_trace(
                    go.Scatter(x=times, y=frequencies, mode='markers', 
                             name="Pitch Frequencies", marker=dict(size=8, color="red")),
                    row=1, col=1
                )
            
            # Rhythm sonification - tempo mapping
            if tempo_data:
                times = [t['time'] for t in tempo_data]
                tempos = [t['tempo'] for t in tempo_data]
                # Convert tempo to beat frequency
                beat_freqs = [t / 60 for t in tempos]
                fig.add_trace(
                    go.Scatter(x=times, y=beat_freqs, mode='lines+markers', 
                             name="Beat Frequency", line=dict(color="blue", width=2)),
                    row=1, col=2
                )
            
            # Harmony sonification - chord complexity
            if chords:
                times = [c['start_time'] for c in chords]
                complexities = [len(c['chord'].split()) for c in chords]  # Simple complexity measure
                fig.add_trace(
                    go.Scatter(x=times, y=complexities, mode='markers', 
                             name="Harmonic Complexity", marker=dict(size=10, color="green")),
                    row=2, col=1
                )
            
            # Dynamics sonification - velocity mapping
            if notes:
                times = [n['start_time'] for n in notes]
                velocities = [n['velocity'] for n in notes]
                # Convert velocity to amplitude
                amplitudes = [v / 127 for v in velocities]
                fig.add_trace(
                    go.Scatter(x=times, y=amplitudes, mode='markers', 
                             name="Dynamic Amplitudes", marker=dict(size=6, color="purple")),
                    row=2, col=2
                )
            
            fig.update_layout(
                title=f"Sonification Analysis - {filename}",
                height=800,
                showlegend=True
            )
            
            # Save interactive HTML
            html_path = self.output_dir / f"{filename}_sonification.html"
            fig.write_html(str(html_path))
            
            return str(html_path)
            
        except Exception as e:
            print(f"Error creating sonification visualization: {e}")
            return None

# Utility functions
def create_enhanced_plots(midi_data: Dict, output_dir: str = "enhanced_outputs"):
    """Create all enhanced visualizations for a MIDI file"""
    visualizer = EnhancedVisualizer(output_dir)
    
    results = {}
    
    # Create 3D piano roll
    results['3d_piano_roll'] = visualizer.create_3d_piano_roll(midi_data)
    
    # Create interactive chord progressions
    results['interactive_chords'] = visualizer.create_interactive_chord_progressions(midi_data)
    
    # Create real-time analysis display
    results['realtime_analysis'] = visualizer.create_real_time_analysis_display(midi_data)
    
    # Create sonification visualization
    results['sonification'] = visualizer.create_sonification_visualization(midi_data)
    
    return results
