import concurrent.futures
import re
import time

from dotenv import load_dotenv
from videodb import connect

import utils
from llm_agent import LLM, LLMType

load_dotenv()


def get_connection():
    """
    Get connection and load the env.
    :return:
    """
    conn = connect()
    return conn


def get_video(id):
    """
    Get video object
    :param id:
    :return:
    """
    conn = get_connection()
    all_videos = conn.get_collection().get_videos()
    video = next(vid for vid in all_videos if vid.id == id)
    return video


def timestamp_parser(resp):
    """
    parse LLM response and convert into timestamps or temporal index for VideoDB
    :param resp:
    :return:
    """
    s_values = re.findall(r'[\'"]s[\'"]: (\d+\.\d+)', resp)
    e_values = re.findall(r'[\'"]e[\'"]: (\d+\.\d+)', resp)

    # Convertvalues to float
    s_values = [float(s) for s in s_values]
    e_values = [float(e) for e in e_values]

    # Put together in a list as timestamps
    timestamps = [{"s": s, "e": e} for s, e in zip(s_values, e_values)]
    return timestamps


def chunk_transcript(docs, chunk_size):
    """
    chunk transcript to fir into context of your LLM
    :param docs:
    :param chunk_size:
    :return:
    """
    for i in range(0, len(docs), chunk_size):
        yield docs[i : i + chunk_size]  # Yield the current chunk


def send_msg_openAI(chunk_prompt, llm):
    response = llm.chat(message=chunk_prompt)
    print(response)
    output = response["choices"][0]["message"]["content"]
    return timestamp_parser(output)


def send_msg_claude(chunk_prompt, llm):
    response = llm.chat(message=chunk_prompt)
    return timestamp_parser(response)


def video_prompter(video, prompt, llm=LLM()):
    timestamps = []
    windowed_transcript = utils.get_windowed_transcript(
        transcript=video.get_transcript()
    )

    # 400 sentence at a time
    if llm.type == LLMType.OPENAI:
        chunk_size = 100
        llm_caller_fn = send_msg_openAI
    else:
        # claude for now
        chunk_size = 350
        llm_caller_fn = send_msg_claude

    chunks = chunk_transcript(windowed_transcript, chunk_size=chunk_size)
    # print(f"Length of the sentence chunk are {len(chunks)}")
    prompts = []
    i = 0
    for chunk in chunks:
        if i > 2:
            break
        chunk_prompt = """
        Create a compilation based on video transcript chunks, where 'video' and 'chunks' are used interchangeably. 
        Given a user prompt and transcript chunks with fields 's' (start time), 'e' (end time), and 't' (text), 
        analyze the text ('t') of each chunk to identify segments relevant to the user prompt. 
        - **Instructions**: 
          - Evaluate each chunk's text for relevance to the specified user prompt.
          - Exclude overlapping segments. If segments overlap, choose the one with the greatest relevance or longest duration.
          - Exclude very short segments that do not provide meaningful content (e.g., shorter than 5 seconds, but adjust as needed).
          - Return the results in JSON format, listing only the timestamps of relevant segments.

        - **Output Format**: Return a JSON list named 'timestamps', with each item containing 's' and 'e' keys for the start and end times of relevant segments. Example format: [{"s": start_time, "e": end_time}, ...].
        - **User Prompts**: User prompts may include requests like 'find funny moments' or 'find moments for social media'. Interpret these prompts by identifying keywords or themes in the transcript chunks that match the intent of the prompt.
        """

        # pass the data
        chunk_prompt += f"""
        Chunks: {chunk}
        User Prompt: {prompt}
        """

        # Add instructions to always return JSON at the end of processing.
        chunk_prompt += """
        Ensure the final output strictly adheres to the JSON format specified, without including additional text or explanations. Use the following structure for your response:
        {
          "timestamps": [
            {"s": start_time, "e": end_time},
            ...
          ]
        }
        """
        prompts.append(chunk_prompt)
        time.sleep(2)
        i += 1

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_index = {
            executor.submit(llm_caller_fn, prompt, llm): prompt for prompt in prompts
        }
        for future in concurrent.futures.as_completed(future_to_index):
            try:
                timestamps.extend(future.result())
            except:
                print("Chunk failed to work with LLM")
    return timestamps
