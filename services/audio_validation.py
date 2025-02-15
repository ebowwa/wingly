import webrtcvad
import wave
import logging
from pathlib import Path
from typing import Tuple
import numpy as np
import array
import struct
from scipy import signal
import subprocess
import tempfile
import os
import asyncio
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from rich.style import Style
from rich.box import ROUNDED

# Custom theme with improved colors and styles
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green bold",
    "metric": "cyan",
    "value": "white",
    "header": "blue bold"
})

console = Console(theme=custom_theme)
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_time=True, show_path=False)]
)

logger = logging.getLogger(__name__)

class AudioValidationError(Exception):
    """Custom exception for audio validation errors"""
    pass

class AudioValidator:
    def __init__(self, aggressiveness: int = 3):
        """Initialize VAD with specified aggressiveness (0-3)."""
        self.vad = webrtcvad.Vad(aggressiveness)
        self.frame_duration_ms = 30  # Use 30ms frames for better accuracy
        self.min_speech_frames = 15  # Reduced from 20
        self.min_speech_ratio = 0.25  # Reduced from 0.35
        self.consecutive_speech_frames = 8  # Reduced from 10
        self.max_silence_duration = 1.5  # Increased from 1.0
        self.min_duration_seconds = 1.0
        self.max_duration_seconds = 300.0
        console.print(Panel.fit(
            f"[success]VAD Initialized[/success]\nAggressiveness: {aggressiveness}",
            title="Audio Validator"
        ))

    def _frame_generator(self, audio: bytes, sample_rate: int) -> bytes:
        """Generate frames from audio data."""
        n = int(sample_rate * (self.frame_duration_ms / 1000.0) * 2)
        offset = 0
        timestamp = 0.0
        while offset + n < len(audio):
            yield audio[offset:offset + n], timestamp
            timestamp += self.frame_duration_ms / 1000.0
            offset += n

    def _analyze_audio_energy(self, audio_array: array.array) -> Tuple[bool, dict]:
        """Analyze audio energy levels and patterns."""
        samples = np.array(audio_array, dtype=np.float32) / 32768.0  # Normalize to [-1, 1]
        
        frame_length = int(16000 * 0.03)  # 30ms frames
        energies = []
        for i in range(0, len(samples), frame_length):
            frame = samples[i:i + frame_length]
            if len(frame) == frame_length:
                energy = np.sqrt(np.mean(frame ** 2))
                energies.append(float(energy))
        
        if not energies:
            return False, {"error": "No energy frames detected"}
            
        energies = np.array(energies)
        
        mean_energy = float(np.mean(energies))
        std_energy = float(np.std(energies))
        peak_energy = float(np.max(energies))
        
        MIN_MEAN_ENERGY = 0.015
        MIN_PEAK_ENERGY = 0.15
        MIN_STD_ENERGY = 0.01
        
        energy_percentile_95 = float(np.percentile(energies, 95))
        energy_percentile_5 = float(np.percentile(energies, 5))
        dynamic_range = float(energy_percentile_95 - energy_percentile_5)
        MIN_DYNAMIC_RANGE = 0.06
        
        zero_crossings = np.sum(np.abs(np.diff(np.signbit(samples))))
        zcr = float(zero_crossings) / float(len(samples))
        MIN_ZCR = 0.03
        
        stats = {
            "mean_energy": mean_energy,
            "peak_energy": peak_energy,
            "std_energy": std_energy,
            "dynamic_range": dynamic_range,
            "zero_crossing_rate": zcr,
            "thresholds": {
                "min_mean_energy": MIN_MEAN_ENERGY,
                "min_peak_energy": MIN_PEAK_ENERGY,
                "min_std_energy": MIN_STD_ENERGY,
                "min_dynamic_range": MIN_DYNAMIC_RANGE,
                "min_zcr": MIN_ZCR
            }
        }
        
        energy_checks = {
            "mean_energy": mean_energy > MIN_MEAN_ENERGY,
            "peak_energy": peak_energy > MIN_PEAK_ENERGY,
            "std_energy": std_energy > MIN_STD_ENERGY,
            "dynamic_range": dynamic_range > MIN_DYNAMIC_RANGE,
            "zcr": zcr > MIN_ZCR
        }
        
        stats["checks"] = energy_checks
        
        console.print(Panel.fit(
            "[bold]Energy validation results:[/bold]",
            title="Energy Validation"
        ))
        for check, passed in energy_checks.items():
            status = "[success]✓ PASSED[/success]" if passed else "[error]✗ FAILED[/error]"
            console.print(f"  {check}: {status}")
        
        passes_checks = all(energy_checks.values())
        
        return passes_checks, stats

    def _process_audio_frames(self, frames_with_timestamps, sample_rate: int) -> Tuple[int, int, bool, dict]:
        """Process audio frames and count speech frames."""
        speech_frames = 0
        total_frames = 0
        window = []
        consecutive_speech = 0
        max_consecutive_speech = 0
        current_silence_duration = 0
        last_speech_timestamp = None
        window_size = 8  # Window size for context
        silence_periods = []
        speech_segments = []
        current_segment = None
        
        for frame, timestamp in frames_with_timestamps:
            if len(frame) < 480:  # Minimum frame size for 30ms at 8kHz
                continue
                
            try:
                is_speech = self.vad.is_speech(frame, sample_rate)
            except Exception as e:
                console.print(f"[yellow]Frame processing error[/yellow] at {timestamp:.2f}s: {e}")
                continue
                
            if is_speech:
                if current_segment is None:
                    current_segment = {"start": float(timestamp)}
                consecutive_speech += 1
                max_consecutive_speech = max(max_consecutive_speech, consecutive_speech)
                if current_silence_duration > 0:
                    silence_periods.append(float(current_silence_duration))
                current_silence_duration = 0
                last_speech_timestamp = timestamp
            else:
                if current_segment is not None:
                    current_segment["end"] = float(timestamp)
                    speech_segments.append(current_segment)
                    current_segment = None
                consecutive_speech = 0
                if last_speech_timestamp is not None:
                    current_silence_duration = float(timestamp - last_speech_timestamp)
            
            window.append(is_speech)
            if len(window) > window_size:
                window.pop(0)
            
            if len(window) == window_size:
                total_frames += 1
                if sum(window) >= int(window_size * 0.7):
                    speech_frames += 1
        
        if current_segment is not None:
            current_segment["end"] = float(timestamp)
            speech_segments.append(current_segment)
        
        stats = {
            "max_consecutive_speech_frames": int(max_consecutive_speech),
            "silence_periods": [float(x) for x in silence_periods],
            "speech_segments": speech_segments,
            "total_silence_duration": float(sum(silence_periods) if silence_periods else 0),
            "speech_ratio": float(speech_frames) / float(total_frames) if total_frames > 0 else 0
        }
        
        console.print(Panel.fit(
            "[bold]Speech detection stats:[/bold]",
            title="Speech Detection"
        ))
        console.print(f"  Total frames: {total_frames}")
        console.print(f"  Speech frames: {speech_frames}")
        console.print(f"  Speech ratio: {stats['speech_ratio']:.2%}")
        console.print(f"  Max consecutive speech frames: {max_consecutive_speech}")
        console.print(f"  Number of speech segments: {len(speech_segments)}")
        console.print(f"  Total silence duration: {stats['total_silence_duration']:.2f}s")
        
        has_consecutive = max_consecutive_speech >= self.consecutive_speech_frames
        return speech_frames, total_frames, has_consecutive, stats

    async def _convert_to_wav(self, input_path: Path, output_path: Path) -> bool:
        """Convert audio file to WAV format using ffmpeg."""
        try:
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5',
                '-acodec', 'pcm_s16le',
                '-ac', '1',
                '-ar', '16000',
                '-y',
                '-loglevel', 'error',
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                console.print(f"[red]FFmpeg conversion failed:[/red] {stderr.decode()}")
                return False
            
            if not output_path.exists() or output_path.stat().st_size == 0:
                console.print("[red]Converted file is empty or does not exist[/red]")
                return False
                
            return True
            
        except Exception as e:
            console.print(f"[red]Audio conversion error:[/red] {str(e)}")
            return False

    def _create_audio_properties_panel(self, properties: dict) -> Panel:
        """Create a formatted panel for audio properties."""
        content = [
            "[header]Audio Properties[/header]",
            f"[metric]Format:[/metric] {properties['channels']}ch {properties['width']*8}bit {properties['rate']}Hz",
            f"[metric]Duration:[/metric] {self.format_duration(properties['duration'])}",
            f"[metric]Frames:[/metric] {properties['frames']:,}"
        ]
        return Panel("\n".join(content), title="Audio File", box=ROUNDED)

    def _create_validation_table(self, results: dict) -> Table:
        """Create a formatted table for validation results."""
        table = Table(
            title="Energy Validation Results",
            box=ROUNDED,
            show_header=True,
            header_style="header",
            title_style="header"
        )
        table.add_column("Metric", style="metric")
        table.add_column("Status", justify="center")
        
        for metric, passed in results.items():
            status = "[success]✓ PASSED[/success]" if passed else "[error]✗ FAILED[/error]"
            table.add_row(metric.replace('_', ' ').title(), status)
        return table

    def _create_speech_stats_table(self, stats: dict) -> Table:
        """Create a formatted table for speech statistics."""
        table = Table(
            title="Speech Detection Statistics",
            box=ROUNDED,
            show_header=True,
            header_style="header",
            title_style="header"
        )
        table.add_column("Metric", style="metric")
        table.add_column("Value", justify="right", style="value")
        
        # Format values with appropriate units and precision
        formatted_stats = {
            "Total Frames": f"{stats['Total frames']:,}",
            "Speech Frames": f"{stats['Speech frames']:,}",
            "Speech Ratio": f"{float(stats['Speech ratio'].rstrip('%')):.1f}%",
            "Max Consecutive Speech": f"{stats['Max consecutive speech']:,} frames",
            "Speech Segments": str(stats['Speech segments']),
            "Total Silence": self.format_duration(float(stats['Total silence'].rstrip('s')))
        }
        
        for key, value in formatted_stats.items():
            table.add_row(key, value)
        return table

    def format_duration(self, seconds: float) -> str:
        """Format duration in a human-readable way."""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        return f"{seconds:.1f}s"

    async def validate_wav(self, audio_path: Path) -> Tuple[bool, dict]:
        """
        Validate WAV file for speech content.
        Returns (has_speech, validation_details).
        """
        validation_details = {"passed": False, "reason": None}

        try:
            with wave.open(str(audio_path), 'rb') as wf:
                properties = {
                    "channels": wf.getnchannels(),
                    "width": wf.getsampwidth(),
                    "rate": wf.getframerate(),
                    "frames": wf.getnframes(),
                    "duration": wf.getnframes() / wf.getframerate()
                }
                
                console.print("\n")  # Add some spacing
                console.print(self._create_audio_properties_panel(properties))

                # Read all audio data
                wf.setpos(0)
                audio_data = wf.readframes(properties['frames'])

                # Convert to array for energy analysis
                audio_array = array.array('h')
                audio_array.frombytes(audio_data)
                
                # Analyze energy levels
                energy_passed, energy_stats = self._analyze_audio_energy(audio_array)
                if not energy_passed:
                    validation_details["reason"] = "Failed energy level checks"
                    validation_details.update(energy_stats)
                    return False, validation_details

                # Analyze speech content
                speech_frames, total_frames, has_consecutive, frame_stats = self._process_audio_frames(
                    self._frame_generator(audio_data, properties['rate']), properties['rate']
                )

                speech_ratio = frame_stats["speech_ratio"]
                has_speech = (
                    speech_ratio >= self.min_speech_ratio and
                    has_consecutive and
                    speech_frames >= self.min_speech_frames
                )

                validation_details.update(frame_stats)
                validation_details["energy_stats"] = energy_stats
                
                if not has_speech:
                    validation_details["reason"] = (
                        f"Insufficient speech content: ratio={speech_ratio:.2%}, "
                        f"frames={speech_frames}/{total_frames}"
                    )
                else:
                    validation_details["passed"] = True
                
                # Display results in well-formatted tables
                console.print("\n")  # Add spacing between sections
                console.print(self._create_validation_table(energy_stats["checks"]))
                console.print("\n")  # Add spacing between tables
                console.print(self._create_speech_stats_table({
                    "Total frames": total_frames,
                    "Speech frames": speech_frames,
                    "Speech ratio": f"{speech_ratio:.1f}%",
                    "Max consecutive speech": frame_stats.get("max_consecutive", 0),
                    "Speech segments": len(frame_stats.get("speech_segments", [])),
                    "Total silence": f"{frame_stats.get('total_silence_duration', 0):.2f}s"
                }))
                
                # Final status with clear visual indicator
                result_style = "success" if has_speech else "error"
                result_icon = "✓" if has_speech else "✗"
                console.print("\n")  # Add spacing before final status
                console.print(Panel(
                    f"[{result_style}]{result_icon} Speech validation {has_speech and 'PASSED' or 'FAILED'}[/{result_style}]" +
                    (f"\nReason: {validation_details['reason']}" if not has_speech else ""),
                    title="Validation Result",
                    box=ROUNDED
                ))
                console.print("\n")  # Add final spacing
                
                return has_speech, validation_details

        except Exception as e:
            validation_details["reason"] = f"Validation error: {str(e)}"
            console.print(Panel(
                f"[error]✗ Error during audio validation[/error]\n{str(e)}",
                title="Error",
                box=ROUNDED
            ))
            logger.exception("Audio processing error")
            return False, validation_details

    async def validate_audio(self, audio_path: Path, content_type: str = None) -> Tuple[bool, dict]:
        """
        Validate audio file for speech content.
        Converts non-WAV files to WAV format before validation.
        Returns (has_speech, validation_details).
        """
        if not audio_path.exists():
            return False, {"error": "Audio file does not exist"}
            
        if content_type and 'wav' not in content_type.lower():
            console.print(f"[yellow]Converting {content_type} to WAV format[/yellow]")
            temp_wav = audio_path.parent / f"{audio_path.stem}_temp.wav"
            if not await self._convert_to_wav(audio_path, temp_wav):
                return False, {"error": "Failed to convert audio to WAV format"}
            audio_path = temp_wav
            
        try:
            return await self.validate_wav(audio_path)
        finally:
            if 'temp_wav' in locals():
                try:
                    temp_wav.unlink()
                except Exception as e:
                    console.print(f"[yellow]Failed to clean up temp WAV file:[/yellow] {e}")

# Create singleton instance
audio_validator = AudioValidator()
