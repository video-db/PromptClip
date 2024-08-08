import concurrent.futures
import json
from dotenv import load_dotenv
from videodb import connect
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


def chunk_docs(docs, chunk_size):
    """
    chunk docs to fit into context of your LLM
    :param docs:
    :param chunk_size:
    :return:
    """
    for i in range(0, len(docs), chunk_size):
        yield docs[i : i + chunk_size]  # Yield the current chunk


def send_msg_openai(chunk_prompt, llm=LLM()):
    response = llm.chat(message=chunk_prompt)
    output = json.loads(response["choices"][0]["message"]["content"])
    sentences = output.get("sentences")
    return sentences


def send_msg_claude(chunk_prompt, llm):
    response = llm.chat(message=chunk_prompt)
    # TODO : add claude reposnse parser
    return response


def send_msg_gemini(chunk_prompt, llm):
    response = llm.chat(message=chunk_prompt)
    # TODO : add claude reposnse parser
    return response


def text_prompter(transcript_text, prompt, llm=None):
    chunk_size = 10000
    # sentence tokenizer
    chunks = chunk_docs(transcript_text, chunk_size=chunk_size)
    # print(f"Length of the sentence chunk are {len(chunks)}")

    if llm is None:
        llm = LLM()

    # 400 sentence at a time
    if llm.type == LLMType.OPENAI:
        llm_caller_fn = send_msg_openai
    elif llm.type == LLMType.GEMINI:
        llm_caller_fn = send_msg_gemini
    else:
        # claude for now
        llm_caller_fn = send_msg_claude

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

        - **Output Format**: Return a JSON list of strings named 'sentences' that containes the output sentences, make sure they are exact substrings.
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
          "sentences": [
            {},
            ...
          ]
        }
        """
        prompts.append(chunk_prompt)
        i += 1

    # make a parallel call to all chunks with prompts
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_index = {
            executor.submit(llm_caller_fn, prompt, llm): prompt for prompt in prompts
        }
        for future in concurrent.futures.as_completed(future_to_index):
            try:
                matches.extend(future.result())
            except Exception as e:
                print(f"Chunk failed to work with LLM {str(e)}")
    return matches


def scene_prompter(transcript_text, prompt, llm=None, run_concurrent=True):
    chunk_size = 20
    chunks = chunk_docs(transcript_text, chunk_size=chunk_size)

    llm_caller_fn = send_msg_openai
    if llm is None:
        llm = LLM()

    # TODO:  llm should have caller function
    # 400 sentence at a time
    if llm.type == LLMType.OPENAI:
        llm_caller_fn = send_msg_openai
    else:
        # claude for now
        llm_caller_fn = send_msg_claude

    matches = []
    prompts = []
    i = 0

    for chunk in chunks:
        descriptions = [scene["description"] for scene in chunk]
        chunk_prompt = """
        You are a video editor who uses AI. Given a user prompt and AI-generated scene descriptions of a video, analyze the descriptions to identify segments relevant to the user prompt for creating clips.

        - **Instructions**: 
            - Evaluate the scene descriptions for relevance to the specified user prompt.
            - Choose description with the highest relevance and most comprehensive content.
            - Optimize for engaging viewing experiences, considering visual appeal and narrative coherence.

            - User Prompts: Interpret prompts like 'find exciting moments' or 'identify key plot points' by matching keywords or themes in the scene descriptions to the intent of the prompt.
        """

        chunk_prompt += f"""
        Descriptions: {json.dumps(descriptions)}
        User Prompt: {prompt}
        """

        chunk_prompt += """
         **Output Format**: Return a JSON list of strings named 'result' that containes the  fileds `sentence`, `start`, `end` Ensure the final output
        strictly adheres to the JSON format specified without including additional text or explanations. \
        If there is no match return empty list without additional text. Use the following structure for your response:
        {"sentences": []}
        """
        prompts.append(chunk_prompt)
        i += 1

    if run_concurrent:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_index = {
                executor.submit(llm_caller_fn, prompt, llm): prompt
                for prompt in prompts
            }
            for future in concurrent.futures.as_completed(future_to_index):
                try:
                    matches.extend(future.result())
                except Exception as e:
                    print(f"Chunk failed to work with LLM {str(e)}")
    else:
        for prompt in prompts:
            try:
                res = llm_caller_fn(prompt)
                matches.extend(res)
            except Exception as e:
                print(f"Chunk failed to work with LLM {str(e)}")
    return matches
