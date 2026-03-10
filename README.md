<!-- This is the markdown template for the final project of the Building AI course, 
created by Reaktor Innovations and University of Helsinki. 
Copy the template, paste it to your GitHub README and edit! -->

# Creating avatars with AI
Final project for the Building AI course

## Summary

This project uses artificial intelligence to generate personalized avatars from user descriptions or photos. It allows anyone to create a unique digital identity in seconds, without design skills. Perfect for social media profiles, gaming, and creative projects.

## Background

Which problems does this idea solve?

* Many people lack design skills to create a professional-looking avatar
* Hiring a designer for a profile picture is expensive and slow
* Generic avatar tools produce bland, repetitive results
* People want to express their unique identity online but don't know how

My personal motivation comes from wanting an easy way to create a fun, unique avatar for online communities. This topic is increasingly relevant as more of our social and professional lives move online — a good avatar matters more than ever.

## How is it used?

The user visits the web app and either:
1. **Types a description** of the avatar they want (e.g. "a cyberpunk woman with blue hair and neon glasses")
2. **Uploads a selfie** to transform into an artistic style of their choice

The AI processes the input and generates several avatar options to choose from. The user can download the result in high resolution.

**Who uses it:**
- Gamers looking for a unique profile picture
- Remote workers needing a professional but personal avatar
- Anyone active on social media or online communities

![AI Avatar Example](https://upload.wikimedia.org/wikipedia/commons/5/5e/Sleeping_cat_on_her_back.jpg)

<img src="https://upload.wikimedia.org/wikipedia/commons/5/5e/Sleeping_cat_on_her_back.jpg" width="300">

Example of how a generation request might look in code:

```python
def generate_avatar(description, style="realistic"):
    styles = ['realistic', 'anime', 'pixel', 'fantasy', 'cyberpunk']
    
    if style not in styles:
        print("Style not available. Choose from:", styles)
        return None
    
    prompt = f"{description}, {style} style, high quality avatar, portrait"
    
    # Call to AI image generation API
    result = ai_model.generate(prompt=prompt, size="512x512")
    
    return result.image_url

# Example usage
avatar = generate_avatar("a young astronaut with curly hair", style="anime")
print("Your avatar is ready:", avatar)
```

## Data sources and AI methods

The project relies on pre-trained generative AI models. No personal data is collected or stored after the session ends.

| Component | Source / Method |
| --------- | --------------- |
| Image generation | Stable Diffusion / DALL·E API |
| Style transfer | Pre-trained CNN models |
| Text-to-image | [OpenAI API](https://platform.openai.com/docs/) |
| Face detection | OpenCV / MediaPipe |

Training data for the underlying models comes from large open image datasets (LAION-5B). Users' uploaded photos are processed in real time and never stored.

## Challenges

This project does **not** solve:

* **Deepfake misuse** — the tool could be used to create fake profile pictures impersonating real people. Safeguards like watermarking are needed.
* **Bias in AI models** — pre-trained models may reflect biases in their training data, producing skewed results for certain ethnicities or features.
* **Copyright of generated images** — the legal status of AI-generated content is still evolving.
* **Accessibility** — users with slow internet connections may struggle with real-time generation.

Ethical considerations around consent and identity representation must be taken seriously before any public deployment.

## What next?

The project could grow by:

* Adding **video avatar** generation (animated profile pictures)
* Supporting **3D avatars** compatible with VR/metaverse platforms
* Building a **style marketplace** where artists can contribute their styles
* Implementing a **mobile app** for on-the-go generation

To move forward, I would need skills in backend development, cloud deployment, and collaboration with a UI/UX designer. API access to more advanced models would also be helpful.

## Acknowledgments

* Inspired by tools like [Ready Player Me](https://readyplayer.me/) and [Lensa AI](https://prisma-ai.com/lensa)
* AI image generation based on open-source Stable Diffusion by Stability AI / [CreativeML Open RAIL-M License](https://huggingface.co/spaces/CompVis/stable-diffusion-license)
* Example image: [Sleeping Cat on Her Back by Umberto Salvagnin](https://commons.wikimedia.org/wiki/File:Sleeping_cat_on_her_back.jpg#filelinks) / [CC BY 2.0](https://creativecommons.org/licenses/by/2.0)
* Building AI course by [Reaktor Innovations](https://www.reaktor.com/) and [University of Helsinki](https://www.helsinki.fi/en)
* Do not use code, images, or data from others without permission — always credit the original creator
