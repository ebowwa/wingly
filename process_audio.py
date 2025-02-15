import os
import json
from datetime import datetime
from utils.ai.process_llm_request import ProcessLLMRequestContent
from gemini_process import process_with_gemini

def process_audio_file(
    audio_path: str,
    speaker_name: str = None,
    prompt_type: str = "default_transcription",
    temperature: float = 0.7,
    max_output_tokens: int = 4096
) -> dict:
    """
    Process an audio file using Gemini API with the specified parameters.
    """
    # Create variables dictionary
    variables = {
        "session_date": datetime.now().strftime("%B %d, %Y"),
        "session_time": datetime.now().strftime("%I:%M %p"),
    }
    
    if speaker_name:
        variables["speaker_name"] = speaker_name

    # Create request content
    request_content = ProcessLLMRequestContent(
        path=audio_path,
        variables=variables
    )

    # Process with Gemini
    result = process_with_gemini(
        uploaded_files=request_content.to_gemini_request(),
        prompt_type=prompt_type,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        step_variables={
            "step_name": "initial_analysis",
            "analysis_type": "detailed",
            "custom_instruction": "Focus on emotional content"
        }
    )

    return result

if __name__ == "__main__":
    # Example usage
    audio_path = "/Users/ebowwa/wingly/audio-samples/Elijah_October_27_2024_9__59PM.ogg"
    
    try:
        # Process without speaker name
        print("\n=== Processing Audio (Without Speaker) ===")
        result1 = process_audio_file(audio_path)
        
        # Save result
        output_path1 = os.path.join(
            os.path.dirname(audio_path),
            "analysis_result_no_speaker.json"
        )
        with open(output_path1, 'w', encoding='utf-8') as f:
            json.dump(result1, f, indent=2)
        print(f"Result saved to: {output_path1}")

        # Process with speaker name
        print("\n=== Processing Audio (With Speaker) ===")
        result2 = process_audio_file(
            audio_path,
            speaker_name="Elijah Cornelius Arbee"
        )
        
        # Save result
        output_path2 = os.path.join(
            os.path.dirname(audio_path),
            "analysis_result_with_speaker.json"
        )
        with open(output_path2, 'w', encoding='utf-8') as f:
            json.dump(result2, f, indent=2)
        print(f"Result saved to: {output_path2}")

    except Exception as e:
        print(f"Error processing audio: {str(e)}")