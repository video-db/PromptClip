
def get_windowed_transcript(transcript, window=10):
    """
    Function to combine word based timestamps into sentences.
    """
    windowed_transcript = []
    window_start_time = 0
    current_window_end = 0
    text_buffer = ''
    for i, word in enumerate(transcript):
        word_text = word.get('text')
        word_end_time = float(word.get('end'))

        # Append word to the buffer, prepend space except for the first word
        text_buffer += (' ' if text_buffer else '') + word_text

        # Check if the word contains a full stop or if it's the last word in the transcript
        if "." in word_text or i == len(transcript) - 1:
            current_window_end = word_end_time
            if word_end_time // window > window_start_time // window or i == len(transcript) - 1:
                # Find the last full stop in the buffer to determine the end of a sentence
                if "." in text_buffer:
                    last_full_stop_index = text_buffer.rindex(".") + 1
                    complete_text = text_buffer[:last_full_stop_index]
                    remaining_text = text_buffer[last_full_stop_index:]
                else:
                    complete_text = text_buffer
                    remaining_text = ""
                # Create transcript block
                transcript_block = {
                    's': round(window_start_time, 2),
                    'e': round(current_window_end, 2),
                    't': complete_text
                }
                windowed_transcript.append(transcript_block)

                # Prepare for the next window
                text_buffer = remaining_text
                window_start_time = current_window_end if remaining_text else word_end_time

    return windowed_transcript

# Sample transcript for testing
sample_transcript = [
    {"start": "0.0", "end": "1.0", "text": "Hello"},
    {"start": "1.0", "end": "2.0", "text": "world."},
    {"start": "2.0", "end": "3.0", "text": "This"},
    {"start": "3.0", "end": "4.0", "text": "is"},
    {"start": "4.0", "end": "5.0", "text": "a"},
    {"start": "5.0", "end": "6.0", "text": "test."},
    {"start": "6.0", "end": "7.0", "text": "Another"},
    {"start": "7.0", "end": "8.0", "text": "sentence"},
    {"start": "8.0", "end": "9.0", "text": "here."},
]

# Verify the function with the sample transcript
# get_windowed_transcript(sample_transcript, window=10)

def get_windowed_transcript_ver(transcript, window=20):
    """
    Function to combine word based timestamps into sentences.
    """
    windowed_transcript = []
    initial_start = 0
    processed_count = 0  # to track if end of window is reached
    last_full_stop_start = 0
    last_full_stop_end = 0
    input_text = ''
    len_of_transcript = len(transcript)
    for i, word in enumerate(transcript):
        start = float(word.get("start"))
        end = float(word.get("end"))
        transcript_block_text = word.get('text')
        if i == 0:
            input_text += f"{transcript_block_text}"
        else:
            input_text += f" {transcript_block_text}"
        if "." in transcript_block_text:
            last_full_stop_start = start
            last_full_stop_end = end
        if (end // window > processed_count) or (i == len_of_transcript - 1):
            # if chunk of window or remaning text at end
            # input_text = stiched text for window size, incomplete sentence carried forward from last iteration
            # strategy conservative, shave extra incomplete sentence
            processed_count += 1
            if "." in input_text:
                full_stop_position = input_text.rindex(".") + 1
                complete_paragraph = input_text[:full_stop_position]
                incomplete_paragraph = input_text[full_stop_position:]
            else:
                # no '.' found in chunk
                complete_paragraph = input_text
                incomplete_paragraph = ""
                last_full_stop_start = end
                last_full_stop_end = end
            transcript_block_dict = {'s': round(initial_start, 2), 'e': round(last_full_stop_end, 2),
                                     't': complete_paragraph}
            if i == len_of_transcript - 1:
                # i.e incomplete_paragraph will be stuck
                transcript_block_dict['t'] += f"{incomplete_paragraph}"
                transcript_block_dict['e'] = end
            windowed_transcript.append(transcript_block_dict)
            input_text = incomplete_paragraph
            initial_start = last_full_stop_start
    return windowed_transcript
