import json

import concurrent.futures

from llm_agent import LLM
from videodb import connect
from videodb import SearchType, IndexType
from videodb.timeline import VideoAsset


from dotenv import load_dotenv

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


def chunk_docs(docs, chunk_size):
    """
    chunk docs to fit into context of your LLM
    :param docs:
    :param chunk_size:
    :return:
    """
    chunks = []
    for i in range(0, len(docs), chunk_size):
        chunks.append(docs[i : i + chunk_size])
    return chunks


# Creating and returning timeline of given result timestamps
def build_video_timeline(
    video, result_timestamps, timeline, top_n=None, max_duration=None, debug=False
):
    """
    This function takes the matched segments list (result_timestamps) and creates a VideoDB Timeline based on the given conditions.
    The user can specify top_n to select the top n results.
    Additionally, the user can set max_duration to stop adding results to the Timeline if the total duration exceeds this limit.
    """
    duration = 0
    if top_n:
        existing_count = len(result_timestamps)
        result_timestamps = result_timestamps[:top_n]
        if debug:
            print(f"Picked top {top_n} from {existing_count}")
    for result_timestamp in result_timestamps:
        start = float(result_timestamp[0])
        end = float(result_timestamp[1])
        description = result_timestamp[2]
        if debug:
            print(start, end, description)
        duration += end - start
        if max_duration and duration > max_duration:
            duration -= end - start
            break
        timeline.add_inline(VideoAsset(asset_id=video.id, start=start, end=end))
    return timeline, duration


def filter_transcript(transcript, start, end):
    result = []
    for entry in transcript:
        if float(entry["end"]) > start and float(entry["start"]) < end:
            result.append(entry)
    return result


def get_multimodal_docs(transcript, scenes, club_on="scene"):
    # TODO: Implement club on transcript
    docs = []
    if club_on == "scene":
        for scene in scenes:
            spoken_result = filter_transcript(
                transcript, float(scene["start"]), float(scene["end"])
            )
            spoken_text = " ".join(
                entry["text"] for entry in spoken_result if entry["text"] != "-"
            )
            data = {
                "visual": scene["description"],
                "spoken": spoken_text,
                "start": scene["start"],
                "end": scene["end"],
            }
            docs.append(data)
    return docs


def send_msg_llm(chunk_prompt, llm):
    output = llm.chat(message=chunk_prompt)
    return output

def text_prompter(transcript, prompt, llm=None):
    chunk_size = 2000
    # sentence tokenizer
    chunks = chunk_docs(transcript, chunk_size=chunk_size)

    if llm is None:
        llm = LLM()

    matches = []
    prompts = []
    i = 0
    for chunk in chunks:
        chunk_prompt = """
        You are a video editor who uses AI. Given a user prompt and transcript of a video analyze the text to identify sentences in the transcript relevant to the user prompt for making clips. 
        - **Instructions**: 
          - Evaluate the sentences for relevance to the specified user prompt.
          - Make sure that sentences start and end properly and meaningfully complete the discussion or topic. Choose the one with the greatest relevance and longest.
          - We'll use the sentences to make video clips in future, so optimize for great viewing experience for people watching the clip of these.
          - If the matched sentences are not too far, merge them into one sentence.
          - Strictly make each result minimum 20 words long. If the match is smaller, adjust the boundries and add more context around the sentences.

        - **Output Format**: Return a JSON list of strings named 'relevant_timestamps' that containes the start and end timestamps along with the text of the relevant sentences.
        - **User Prompts**: User prompts may include requests like 'find funny moments' or 'find moments for social media'. Interpret these prompts by 
        identifying keywords or themes in the transcript that match the intent of the prompt.
        """

        # pass the data
        chunk_prompt += f"""
        Transcript: {chunk}
        User Prompt: {prompt}
        """

        # Add instructions to always return JSON at the end of processing.
        chunk_prompt += """
        Ensure the final output strictly adheres to the JSON format specified without including additional text or explanations. \
        If there is no match return empty list without additional text. Use the following structure for your response:
        {
          "relevant_timestamps": [
            {
              "start": __,
              "end": __,
              "text": __
            },
            ...
          ]
        }
        """
        prompts.append(chunk_prompt)
        i += 1

    # make a parallel call to all chunks with prompts
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_index = {
            executor.submit(send_msg_llm, prompt, llm): prompt for prompt in prompts
        }
        for future in concurrent.futures.as_completed(future_to_index):
            try:
                results = future.result()
                matches.extend([(timestamp["start"], timestamp["end"], timestamp["text"]) for timestamp in results["relevant_timestamps"]])
            except Exception as e:
                print(f"Chunk failed to work with LLM {str(e)}")
    return matches


def scene_prompter(scenes, prompt, llm=None, run_concurrent=True):
    chunk_size = 100
    chunks = chunk_docs(scenes, chunk_size=chunk_size)

    if llm is None:
        llm = LLM()

    matches = []
    prompts = []
    i = 0

    for chunk in chunks:
        descriptions = {idx : (scene["start"], scene["end"], scene["description"]) for idx, scene in enumerate(chunk)}
        chunk_prompt = """
        You are a video editor who uses AI. Given a user prompt and AI-generated scene descriptions of a video, analyze the descriptions to identify segments relevant to the user prompt for creating clips.

        - **Instructions**: 
            - Evaluate the scene descriptions for relevance to the specified user prompt.
            - Choose description with the highest relevance and most comprehensive content.
            - Optimize for engaging viewing experiences, considering visual appeal and narrative coherence.

            - User Prompts: Interpret prompts like 'find exciting moments' or 'identify key plot points' by matching keywords or themes in the scene descriptions to the intent of the prompt.
        """

        descriptions_str = json.dumps([{idx : description} for idx, (start, end, description) in descriptions.items()])
        chunk_prompt += f"""
        Descriptions: {descriptions_str}
        User Prompt: {prompt}
        """

        chunk_prompt += """
         **Output Format**: Return a JSON list of relevant ids with a field 'relevant_ids'
        Ensure the final output strictly adheres to the JSON format specified without including additional text or explanations. \
        If there is no match return empty list without additional text. Use the following structure for your response:
        {"relevant_ids": []}
        """

        prompts.append((chunk_prompt, descriptions))
        i += 1

    if run_concurrent:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_index = {
                executor.submit(send_msg_llm, prompt, llm): descriptions
                for prompt, descriptions in prompts
            }
            for future in concurrent.futures.as_completed(future_to_index):
                try:
                    results = future.result()
                    descriptions = future_to_index[future]
                    matches.extend(descriptions[int(res_idx)] for res_idx in results["relevant_ids"])
                except Exception as e:
                    print(f"Chunk failed to work with LLM {str(e)}")
    else:
        for prompt, descriptions in prompts:
            try:
                res = send_msg_llm(prompt, llm)
                matches.extend(descriptions[int(res_idx)] for res_idx in res["relevant_ids"])
            except Exception as e:
                print(f"Chunk failed to work with LLM {str(e)}")
    return matches


def multimodal_prompter(transcript, scenes, prompt, llm=None, run_concurrent=True):
    docs = get_multimodal_docs(transcript, scenes)
    chunk_size = 100
    chunks = chunk_docs(docs, chunk_size=chunk_size)

    if llm is None:
        llm = LLM()

    matches = []
    prompts = []
    i = 0

    for chunk in chunks:
        chunk_lookup = {idx: (doc["start"], doc["end"], (doc["spoken"], doc["visual"])) for idx, doc in enumerate(chunk)}
        chunk = {idx: (spoken, visual) for idx, (start, end, (spoken, visual)) in chunk_lookup.items()}
        chunk_prompt = f"""
        You are given visual and spoken information of the video of each second, and a transcipt of what's being spoken along with timestamp.
        Your task is to evaluate the data for relevance to the specified user prompt.
        Corelate visual and spoken content to find the relevant video segment.

        Multimodal Data:
        video: {chunk}
        User Prompt: {prompt}

    
        """
        chunk_prompt += """
         **Output Format**: Return a JSON list of relevant ids (list(str)) in a field named 'relevant_ids'.

        Ensure the final output strictly adheres to the JSON format specified without including additional text or explanations.
        If there is no match return empty list without additional text. Use the following structure for your response:
        {"relevant_ids": []}
        """
        prompts.append((chunk_prompt, chunk_lookup))
        i += 1

    if run_concurrent:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_index = {
                executor.submit(send_msg_llm, prompt, llm): chunk_lookup
                for prompt, chunk_lookup in prompts
            }
            for future in concurrent.futures.as_completed(future_to_index):
                try:
                    results = future.result()
                    chunk_lookup = future_to_index[future]
                    matches.extend(chunk_lookup[int(res_idx)] for res_idx in results["relevant_ids"])
                except Exception as e:
                    print(f"Chunk failed to work with LLM {str(e)}")
    else:
        for prompt, chunk_lookup in prompts:
            try:
                res = send_msg_llm(prompt, llm)
                matches.extend(chunk_lookup[int(res_idx)] for res_idx in res["relevant_ids"])
            except Exception as e:
                import traceback

                print(traceback.print_exc())
                print(f"Chunk failed to work with LLM {str(e)}")
    return matches
