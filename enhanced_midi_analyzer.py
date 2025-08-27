#!/usr/bin/env python3
"""
Enhanced MIDI Analyzer - Advanced musical analysis with comprehensive features
"""

import os
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
matplotlib.rcParams["font.family"] = "DejaVu Sans"
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Lazy-import heavy deps
def lazy_import():
    try:
        import pretty_midi
        import mido
        import pandas as pd
        return pretty_midi, mido, pd
    except ImportError as e:
        raise SystemExit(f"Required packages missing: {e}\nInstall with: pip install pretty_midi mido pandas")

# Enhanced chord definitions
CHORD_TYPES = {
    # Triads
    "": [0, 4, 7],           # Major
    "m": [0, 3, 7],          # Minor
    "dim": [0, 3, 6],        # Diminished
    "aug": [0, 4, 8],        # Augmented
    "sus2": [0, 2, 7],       # Suspended 2nd
    "sus4": [0, 5, 7],       # Suspended 4th
    
    # 7ths
    "maj7": [0, 4, 7, 11],  # Major 7th
    "7": [0, 4, 7, 10],     # Dominant 7th
    "m7": [0, 3, 7, 10],    # Minor 7th
    "m7b5": [0, 3, 6, 10],  # Half-diminished 7th
    "dim7": [0, 3, 6, 9],   # Diminished 7th
    "maj7#5": [0, 4, 8, 11], # Major 7th #5
    "7#5": [0, 4, 8, 10],   # Dominant 7th #5
    "7b5": [0, 4, 6, 10],   # Dominant 7th b5
    
    # 9ths
    "maj9": [0, 4, 7, 11, 14], # Major 9th
    "9": [0, 4, 7, 10, 14],    # Dominant 9th
    "m9": [0, 3, 7, 10, 14],   # Minor 9th
    
    # Extended
    "add9": [0, 4, 7, 14],     # Add 9th
    "add11": [0, 4, 7, 17],    # Add 11th
    "6": [0, 4, 7, 9],         # Major 6th
    "m6": [0, 3, 7, 9],        # Minor 6th
}

# Scale definitions for key detection
SCALES = {
    'C': [0, 2, 4, 5, 7, 9, 11],
    'G': [7, 9, 11, 0, 2, 4, 6],
    'D': [2, 4, 6, 7, 9, 11, 1],
    'A': [9, 11, 1, 2, 4, 6, 8],
    'E': [4, 6, 8, 9, 11, 1, 3],
    'B': [11, 1, 3, 4, 6, 8, 10],
    'F#': [6, 8, 10, 11, 1, 3, 5],
    'C#': [1, 3, 5, 6, 8, 10, 0],
    'F': [5, 7, 9, 10, 0, 2, 4],
    'Bb': [10, 0, 2, 3, 5, 7, 9],
    'Eb': [3, 5, 7, 8, 10, 0, 2],
    'Ab': [8, 10, 0, 1, 3, 5, 7],
    'Db': [1, 3, 5, 6, 8, 10, 0],
    'Gb': [6, 8, 10, 11, 1, 3, 5],
    'Cb': [11, 1, 3, 4, 6, 8, 10],
}

# Minor scales
MINOR_SCALES = {
    'Am': [9, 11, 0, 2, 4, 5, 7],
    'Em': [4, 6, 7, 9, 11, 0, 2],
    'Bm': [11, 1, 2, 4, 6, 7, 9],
    'F#m': [6, 8, 9, 11, 1, 2, 4],
    'C#m': [1, 3, 4, 6, 8, 9, 11],
    'G#m': [8, 10, 11, 1, 3, 4, 6],
    'D#m': [3, 5, 6, 8, 10, 11, 1],
    'A#m': [10, 0, 1, 3, 5, 6, 8],
    'Dm': [2, 4, 5, 7, 9, 10, 0],
    'Gm': [7, 9, 10, 0, 2, 4, 5],
    'Cm': [0, 2, 3, 5, 7, 8, 10],
    'Fm': [5, 7, 8, 10, 0, 1, 3],
    'Bbm': [10, 0, 1, 3, 5, 6, 8],
    'Ebm': [3, 5, 6, 8, 10, 11, 1],
    'Abm': [8, 10, 11, 1, 3, 4, 6],
}

class EnhancedMIDIAnalyzer:
    def __init__(self, midi_path: str):
        self.midi_path = midi_path
        self.pretty_midi, self.mido, self.pd = lazy_import()
        self.pm = None
        self.analysis_results = {}
        
    def load_midi(self):
        """Load and validate MIDI file"""
        try:
            logger.info(f"Loading MIDI file: {self.midi_path}")
            self.pm = self.pretty_midi.PrettyMIDI(self.midi_path)
            logger.info(f"Successfully loaded MIDI with {len(self.pm.instruments)} instruments")
            return True
        except Exception as e:
            logger.error(f"Failed to load MIDI file: {e}")
            return False
    
    def detect_key(self) -> Tuple[str, float]:
        """Detect the musical key using pitch class distribution"""
        if not self.pm:
            return "Unknown", 0.0
            
        # Get pitch class histogram
        histogram = np.zeros(12)
        for inst in self.pm.instruments:
            for note in inst.notes:
                pc = note.pitch % 12
                duration = note.end - note.start
                histogram[pc] += duration
        
        # Normalize
        if histogram.sum() > 0:
            histogram = histogram / histogram.sum()
        
        # Test all keys
        best_key = "C"
        best_score = -1
        
        for key, scale in {**SCALES, **MINOR_SCALES}.items():
            # Create key template
            template = np.zeros(12)
            template[scale] = 1.0
            
            # Calculate correlation
            score = np.corrcoef(histogram, template)[0, 1]
            if np.isnan(score):
                score = 0.0
                
            if score > best_score:
                best_score = score
                best_key = key
        
        return best_key, best_score
    
    def analyze_rhythm(self) -> Dict[str, Any]:
        """Analyze rhythm and groove patterns"""
        if not self.pm:
            return {}
            
        # Get tempo changes
        tempo_times, tempos = self.pm.get_tempo_changes()
        
        # Calculate average tempo
        avg_tempo = np.mean(tempos) if len(tempos) > 0 else 120
        
        # Analyze note density patterns
        fs = 10  # 10 Hz sampling
        roll = self.pm.get_piano_roll(fs=fs)
        density = (roll > 0).sum(axis=0)
        times = np.arange(roll.shape[1]) / fs
        
        # Detect beats (simplified)
        if avg_tempo > 0:
            beat_interval = 60.0 / avg_tempo
            beat_frames = int(beat_interval * fs)
            
            # Find peaks in density (potential beats)
            from scipy.signal import find_peaks
            try:
                peaks, _ = find_peaks(density, height=np.mean(density), distance=beat_frames//2)
                beat_times = times[peaks]
            except:
                beat_times = []
        else:
            beat_times = []
        
        return {
            'avg_tempo': avg_tempo,
            'tempo_changes': self.pd.DataFrame({'time_sec': tempo_times, 'bpm': tempos}),
            'note_density': self.pd.DataFrame({'time_sec': times, 'density': density}),
            'beat_times': beat_times,
            'total_duration': self.pm.get_end_time()
        }
    
    def analyze_harmony(self) -> Dict[str, Any]:
        """Advanced harmony analysis"""
        if not self.pm:
            return {}
            
        # Enhanced chord detection
        window = 0.5
        hop = 0.1
        fs = int(round(1.0 / hop))
        
        roll = self.pm.get_piano_roll(fs=fs)
        chroma = np.zeros((12, roll.shape[1]))
        
        # Build chromagram
        for p in range(128):
            chroma[p % 12] += roll[p]
        
        times = np.arange(chroma.shape[1]) / fs
        win_frames = max(1, int(round(window * fs)))
        
        chords = []
        chord_times = []
        chord_scores = []
        
        for i in range(0, chroma.shape[1], win_frames):
            seg = chroma[:, i:i+win_frames].mean(axis=1)
            
            if seg.sum() < 1e-6:
                chords.append("N")
                chord_times.append(times[min(i, len(times)-1)])
                chord_scores.append(0.0)
                continue
            
            # Test all chord types
            best_name = "N"
            best_score = -1
            
            for base_note in range(12):
                for chord_type, intervals in CHORD_TYPES.items():
                    # Create chord template
                    template = np.zeros(12)
                    for interval in intervals:
                        template[(base_note + interval) % 12] = 1.0
                    
                    # Calculate score
                    score = float(np.dot(template, seg))
                    if score > best_score:
                        best_score = score
                        best_name = f"{['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][base_note]}{chord_type}"
            
            chords.append(best_name)
            chord_times.append(times[min(i, len(times)-1)])
            chord_scores.append(best_score)
        
        # Find common chord progressions
        chord_progressions = self._find_chord_progressions(chords)
        
        return {
            'chords': self.pd.DataFrame({
                'time_sec': chord_times, 
                'chord': chords, 
                'confidence': chord_scores
            }),
            'progressions': chord_progressions,
            'chromagram': chroma,
            'chroma_times': times
        }
    
    def _find_chord_progressions(self, chords: List[str]) -> List[Tuple[str, str, int]]:
        """Find common chord progressions"""
        progressions = []
        for i in range(len(chords) - 1):
            if chords[i] != "N" and chords[i+1] != "N":
                prog = (chords[i], chords[i+1], 1)
                
                # Check if this progression already exists
                found = False
                for j, (p1, p2, count) in enumerate(progressions):
                    if p1 == prog[0] and p2 == prog[1]:
                        progressions[j] = (p1, p2, count + 1)
                        found = True
                        break
                
                if not found:
                    progressions.append(prog)
        
        # Sort by frequency
        progressions.sort(key=lambda x: x[2], reverse=True)
        return progressions
    
    def analyze_melody(self) -> Dict[str, Any]:
        """Analyze melodic content"""
        if not self.pm:
            return {}
            
        all_notes = []
        for inst in self.pm.instruments:
            if inst.is_drum:
                continue
            for note in inst.notes:
                all_notes.append({
                    'pitch': note.pitch,
                    'start': note.start,
                    'end': note.end,
                    'velocity': note.velocity,
                    'instrument': inst.program
                })
        
        if not all_notes:
            return {}
        
        # Sort by start time
        all_notes.sort(key=lambda x: x['start'])
        
        # Analyze intervals
        intervals = []
        for i in range(1, len(all_notes)):
            interval = all_notes[i]['pitch'] - all_notes[i-1]['pitch']
            intervals.append(interval)
        
        # Melodic contour
        contour = []
        for i in range(1, len(all_notes)):
            if all_notes[i]['pitch'] > all_notes[i-1]['pitch']:
                contour.append('up')
            elif all_notes[i]['pitch'] < all_notes[i-1]['pitch']:
                contour.append('down')
            else:
                contour.append('same')
        
        return {
            'notes': all_notes,
            'intervals': intervals,
            'contour': contour,
            'pitch_range': (min(n['pitch'] for n in all_notes), max(n['pitch'] for n in all_notes)),
            'avg_velocity': np.mean([n['velocity'] for n in all_notes])
        }
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete analysis"""
        if not self.load_midi():
            return {}
        
        logger.info("Starting comprehensive MIDI analysis...")
        
        # Basic analysis
        self.analysis_results['basic'] = {
            'instruments': [inst.name for inst in self.pm.instruments],
            'total_notes': sum(len(inst.notes) for inst in self.pm.instruments),
            'duration': self.pm.get_end_time()
        }
        
        # Key detection
        logger.info("Detecting musical key...")
        key, confidence = self.detect_key()
        self.analysis_results['key'] = {'key': key, 'confidence': confidence}

        # Scale notes for the detected key (as names)
        pitch_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
        scale_pcs = []
        if key in SCALES:
            scale_pcs = SCALES[key]
        elif key in MINOR_SCALES:
            scale_pcs = MINOR_SCALES[key]
        self.analysis_results['scale_notes'] = [pitch_names[pc] for pc in scale_pcs] if scale_pcs else []

        # Time signature (first one if present)
        try:
            ts_changes = getattr(self.pm, 'time_signature_changes', [])
            if ts_changes:
                ts0 = ts_changes[0]
                self.analysis_results['time_signature'] = {
                    'numerator': int(getattr(ts0, 'numerator', 4)),
                    'denominator': int(getattr(ts0, 'denominator', 4))
                }
            else:
                self.analysis_results['time_signature'] = {'numerator': 4, 'denominator': 4}
        except Exception:
            self.analysis_results['time_signature'] = {'numerator': 4, 'denominator': 4}
        
        # Rhythm analysis
        logger.info("Analyzing rhythm and groove...")
        self.analysis_results['rhythm'] = self.analyze_rhythm()
        # Convenience: initial tempo if available
        try:
            tempo_df = self.analysis_results['rhythm'].get('tempo_changes')
            if tempo_df is not None and not tempo_df.empty:
                self.analysis_results['initial_tempo_bpm'] = float(tempo_df['bpm'].iloc[0])
            else:
                self.analysis_results['initial_tempo_bpm'] = None
        except Exception:
            self.analysis_results['initial_tempo_bpm'] = None
        
        # Harmony analysis
        logger.info("Analyzing harmony...")
        self.analysis_results['harmony'] = self.analyze_harmony()
        
        # Melody analysis
        logger.info("Analyzing melody...")
        self.analysis_results['melody'] = self.analyze_melody()
        
        # Pitch class histogram
        logger.info("Computing pitch class distribution...")
        histogram = np.zeros(12)
        for inst in self.pm.instruments:
            for note in inst.notes:
                pc = note.pitch % 12
                duration = note.end - note.start
                histogram[pc] += duration
        
        if histogram.sum() > 0:
            histogram = histogram / histogram.sum()
        
        self.analysis_results['pitch_class'] = histogram
        
        logger.info("Analysis complete!")
        return self.analysis_results
    
    def save_analysis(self, output_dir: str):
        """Save analysis results and visualizations"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON results
        with open(os.path.join(output_dir, 'analysis_results.json'), 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        
        # Generate and save visualizations
        self._create_visualizations(output_dir)
        
        # Save CSV data
        self._save_csv_data(output_dir)
        
        logger.info(f"Results saved to {output_dir}")
    
    def _create_visualizations(self, output_dir: str):
        """Create enhanced visualizations"""
        # Set style
        plt.style.use('seaborn-v0_8')
        
        # 1. Key and Scale Visualization
        self._plot_key_analysis(output_dir)
        
        # 2. Enhanced Chord Progression
        self._plot_chord_progressions(output_dir)
        
        # 3. Rhythm Analysis
        self._plot_rhythm_analysis(output_dir)
        
        # 4. Melodic Contour
        self._plot_melodic_contour(output_dir)
        
        # 5. Instrument Analysis
        self._plot_instrument_analysis(output_dir)
    
    def _plot_key_analysis(self, output_dir: str):
        """Plot key analysis with scale visualization"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Pitch class histogram
        pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        bars = ax1.bar(pitch_classes, self.analysis_results['pitch_class'])
        
        # Highlight scale notes
        key = self.analysis_results['key']['key']
        if key in SCALES:
            scale_notes = SCALES[key]
        elif key in MINOR_SCALES:
            scale_notes = MINOR_SCALES[key]
        else:
            scale_notes = []
        
        for i, (bar, pc) in enumerate(zip(bars, range(12))):
            if pc in scale_notes:
                bar.set_color('red')
                bar.set_alpha(0.7)
        
        ax1.set_title(f'Pitch Class Distribution (Key: {key})')
        ax1.set_ylabel('Proportion')
        
        # Scale visualization
        if scale_notes:
            piano_keys = []
            for i in range(12):
                if i in scale_notes:
                    piano_keys.append(1)
                else:
                    piano_keys.append(0)
            
            ax2.bar(pitch_classes, piano_keys, color='lightblue', alpha=0.6)
            ax2.set_title(f'Scale Notes for {key}')
            ax2.set_ylabel('In Scale')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'key_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_chord_progressions(self, output_dir: str):
        """Plot chord progression analysis"""
        chord_df = self.analysis_results['harmony']['chords']
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Chord timeline
        unique_chords = sorted(set(chord_df['chord']))
        chord_mapping = {c: i for i, c in enumerate(unique_chords)}
        
        chord_indices = [chord_mapping.get(c, -1) for c in chord_df['chord']]
        
        ax1.step(chord_df['time_sec'], chord_indices, where='post', linewidth=2)
        ax1.set_yticks(list(chord_mapping.values()))
        ax1.set_yticklabels(list(chord_mapping.keys()))
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Chord')
        ax1.set_title('Chord Progression Timeline')
        ax1.grid(True, alpha=0.3)
        
        # Top progressions
        progressions = self.analysis_results['harmony']['progressions'][:10]
        if progressions:
            prog_names = [f"{p[0]} → {p[1]}" for p in progressions]
            counts = [p[2] for p in progressions]
            
            bars = ax2.barh(prog_names, counts, color='skyblue')
            ax2.set_xlabel('Frequency')
            ax2.set_title('Most Common Chord Progressions')
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                ax2.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                        str(count), va='center')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chord_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_rhythm_analysis(self, output_dir: str):
        """Plot rhythm and groove analysis"""
        rhythm = self.analysis_results['rhythm']
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Tempo changes
        tempo_df = rhythm['tempo_changes']
        if not tempo_df.empty:
            ax1.step(tempo_df['time_sec'], tempo_df['bpm'], where='post', linewidth=2)
            ax1.set_xlabel('Time (s)')
            ax1.set_ylabel('Tempo (BPM)')
            ax1.set_title('Tempo Changes')
            ax1.grid(True, alpha=0.3)
        
        # Note density
        density_df = rhythm['note_density']
        ax2.plot(density_df['time_sec'], density_df['density'], alpha=0.7)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Active Notes')
        ax2.set_title('Note Density Over Time')
        ax2.grid(True, alpha=0.3)
        
        # Beat detection
        if len(rhythm['beat_times']) > 0:
            ax3.vlines(rhythm['beat_times'], 0, 1, color='red', alpha=0.7, linewidth=2)
            ax3.set_xlabel('Time (s)')
            ax3.set_ylabel('Beat Detection')
            ax3.set_title('Detected Beats')
            ax3.set_ylim(0, 1)
        
        # Tempo distribution
        if not tempo_df.empty:
            ax4.hist(tempo_df['bpm'], bins=20, alpha=0.7, color='green')
            ax4.axvline(rhythm['avg_tempo'], color='red', linestyle='--', 
                       label=f'Average: {rhythm["avg_tempo"]:.1f} BPM')
            ax4.set_xlabel('Tempo (BPM)')
            ax4.set_ylabel('Frequency')
            ax4.set_title('Tempo Distribution')
            ax4.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'rhythm_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_melodic_contour(self, output_dir: str):
        """Plot melodic analysis"""
        melody = self.analysis_results['melody']
        
        if not melody.get('notes'):
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Pitch over time
        times = [note['start'] for note in melody['notes']]
        pitches = [note['pitch'] for note in melody['notes']]
        
        ax1.scatter(times, pitches, alpha=0.6, s=20)
        ax1.plot(times, pitches, alpha=0.3, linewidth=1)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Pitch (MIDI)')
        ax1.set_title('Melodic Contour')
        ax1.grid(True, alpha=0.3)
        
        # Interval distribution
        if melody['intervals']:
            ax2.hist(melody['intervals'], bins=50, alpha=0.7, color='purple')
            ax2.axvline(0, color='red', linestyle='--', alpha=0.7)
            ax2.set_xlabel('Interval (semitones)')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Melodic Interval Distribution')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'melody_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_instrument_analysis(self, output_dir: str):
        """Plot instrument analysis"""
        if not self.pm:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Instrument note counts
        inst_names = []
        note_counts = []
        
        for inst in self.pm.instruments:
            if inst.name:
                inst_names.append(inst.name)
            else:
                inst_names.append(f"Instrument {inst.program}")
            note_counts.append(len(inst.notes))
        
        if inst_names:
            bars = ax1.bar(range(len(inst_names)), note_counts, color='lightcoral')
            ax1.set_xticks(range(len(inst_names)))
            ax1.set_xticklabels(inst_names, rotation=45, ha='right')
            ax1.set_ylabel('Number of Notes')
            ax1.set_title('Notes per Instrument')
            
            # Add value labels
            for bar, count in zip(bars, note_counts):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        str(count), ha='center', va='bottom')
        
        # Velocity distribution
        all_velocities = []
        for inst in self.pm.instruments:
            for note in inst.notes:
                all_velocities.append(note.velocity)
        
        if all_velocities:
            ax2.hist(all_velocities, bins=30, alpha=0.7, color='lightblue')
            ax2.set_xlabel('Velocity')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Velocity Distribution')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'instrument_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _save_csv_data(self, output_dir: str):
        """Save analysis data as CSV files"""
        # Save chord data
        if 'harmony' in self.analysis_results:
            chord_df = self.analysis_results['harmony']['chords']
            chord_df.to_csv(os.path.join(output_dir, 'chords.csv'), index=False)
        
        # Save tempo data
        if 'rhythm' in self.analysis_results:
            tempo_df = self.analysis_results['rhythm']['tempo_changes']
            tempo_df.to_csv(os.path.join(output_dir, 'tempo_changes.csv'), index=False)
            
            density_df = self.analysis_results['rhythm']['note_density']
            density_df.to_csv(os.path.join(output_dir, 'note_density.csv'), index=False)
        
        # Save pitch class data
        if 'pitch_class' in self.analysis_results:
            pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            pitch_df = self.pd.DataFrame({
                'pitch_class': pitch_classes,
                'proportion': self.analysis_results['pitch_class']
            })
            pitch_df.to_csv(os.path.join(output_dir, 'pitch_class_histogram.csv'), index=False)
        
        # Save melody data
        if 'melody' in self.analysis_results and self.analysis_results['melody'].get('notes'):
            melody_df = self.pd.DataFrame(self.analysis_results['melody']['notes'])
            melody_df.to_csv(os.path.join(output_dir, 'melody_notes.csv'), index=False)

def main():
    parser = argparse.ArgumentParser(description='Enhanced MIDI Analyzer with Advanced Features')
    parser.add_argument('--midi', type=str, required=True, help='Path to MIDI file (.mid)')
    parser.add_argument('--outdir', type=str, default='enhanced_outputs', help='Output directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create analyzer and run analysis
    analyzer = EnhancedMIDIAnalyzer(args.midi)
    results = analyzer.run_full_analysis()
    
    if results:
        analyzer.save_analysis(args.outdir)
        print(f"\n🎵 Analysis complete! Results saved to: {args.outdir}")
        print(f"🎼 Detected key: {results['key']['key']} (confidence: {results['key']['confidence']:.3f})")
        print(f"⏱️  Duration: {results['basic']['duration']:.2f} seconds")
        print(f"🎹 Total notes: {results['basic']['total_notes']}")
        print(f"🎸 Instruments: {', '.join(results['basic']['instruments'])}")
    else:
        print("❌ Analysis failed. Check the MIDI file and try again.")

if __name__ == '__main__':
    main()
