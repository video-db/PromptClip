<!-- PROJECT SHIELDS -->
<!--
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![PyPI version][pypi-shield]][pypi-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Website][website-shield]][website-url]


<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://videodb.io/">
    <img src="https://codaio.imgix.net/docs/_s5lUnUCIU/blobs/bl-RgjcFrrJjj/d3cbc44f8584ecd42f2a97d981a144dce6a66d83ddd5864f723b7808c7d1dfbc25034f2f25e1b2188e78f78f37bcb79d3c34ca937cbb08ca8b3da1526c29da9a897ab38eb39d084fd715028b7cc60eb595c68ecfa6fa0bb125ec2b09da65664a4f172c2f" alt="Logo" width="300" height="">
  </a>

<h3 align="center">PromptCuts ✄ </h3>

  <p align="center">
    Create video supercuts using LLM prompts
    <br />
    <a href="https://github.com/video-db/streamRAG/issues">🐞Report a Bug</a> 
    ·
    <a href="https://github.com/video-db/streamRAG/issues">💡Suggest a Feature</a> 
  </p>
</p>

<!-- ABOUT THE PROJECT -->

# PromptCuts: Create & stream video supercuts with LLM prompts 🚀

## What does it do? 🤔

It allows any developer to:
* 📚 Upload a video from any source (Youtube etc)
* 🔍 Prompt that video in natural language with queries like `Show funny moments in the video` or `find the moments useful for social media trailer for this video`
* 🎛️ Use any LLM like OpenAI,  Claude or Gemeni Pro. 
* 🌟 Instantly stream a supercut of those moments
* 🛠️ Finetune the supercuts editing length/ frequency etc of the cut length
* 🎸 Add music to supercut. 

## How do I use it? 🛠️
- **Get your API key:** Sign up on [VideoDB console](https://console.videodb.io) (Free for the first 50 uploads, no
  credit card required). 🆓
- **Set `VIDEO_DB_API_KEY`:** Enter your key in the `env` file.
- **Set `OPENAI_KAY` or `ANTHROPIC_KEY`:** Add your LLM API Key in the `env` file.
- **Install dependencies:** Run `pip install -r requirements.txt` in your terminal.
- **Run locally:**  Run the notebook `PromptCut.ipynb` and experiment with your prompts and ranking of results.

---
<!-- ROADMAP -->

## Roadmap 🛣️
1. Add support music generation Models to jazzup the cuts.
2. Integrate with other projects such as Pika Labs and Midjourney

---
<!-- CONTRIBUTING -->

## Contributing 🤝

Your contributions make the open-source community an incredible place for learning, inspiration, and creativity. We
welcome and appreciate your input! Here's how you can contribute:

- Open issues to share your use cases.
- Participate in brainstorming solutions for our roadmap.
- Suggest improvements to the codebase.

### Contribution Steps

1. Fork the Project 🍴
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 📬

---

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[pypi-shield]: https://img.shields.io/pypi/v/videodb?style=for-the-badge

[pypi-url]: https://pypi.org/project/videodb/

[python-shield]:https://img.shields.io/pypi/pyversions/videodb?style=for-the-badge

[stars-shield]: https://img.shields.io/github/stars/video-db/promptCuts.svg?style=for-the-badge

[stars-url]: https://github.com/video-db/promptCuts/stargazers

[issues-shield]: https://img.shields.io/github/issues/video-db/videodb-python.svg?style=for-the-badge

[issues-url]: https://github.com/video-db/promptCuts/issues

[website-shield]: https://img.shields.io/website?url=https%3A%2F%2Fvideodb.io%2F&style=for-the-badge&label=videodb.io

[website-url]: https://videodb.io/

