import app.handler as handler
from lib.prompt import BANNED_PROMPT
from exceptions import BannedPromptError


def check_banned(prompt: str):
    words = set(w.lower() for w in prompt.split())

    v = words & BANNED_PROMPT
    print(v)
    if len(v) != 0:
        raise BannedPromptError(f"banned prompt: {prompt}")


if __name__ == "__main__":
    check_banned("A full-body portrait of a serene human figure, the very embodiment of a pure soul, standing perfectly still and facing directly forward within a divine, celestial space. The composition is frontal and unobscured, capturing the subject in their entirety. The figure's facial features are a harmonious and androgynous blend, transcending specific gender or ethnicity, radiating a profound sense of inner peace and tranquil devotion. Their gaze is gentle yet captivating, directed straight at the viewer. They are clad in a simple, immaculate white robe, its ethereal and weightless fabric cascading in soft, graceful folds that seem to catch and diffuse the ambient light. The background is a boundless expanse of soft, luminous mist and ethereal light, suggesting an infinite heavenly realm where faint, abstract structures of pure light and crystalline geometry shimmer in the distance. A brilliant, yet gentle, radiant light emanates from an unseen source, bathing the entire scene in a warm, golden-white glow. This celestial illumination enhances the purity of the robe and casts soft, subtle shadows, creating a sense of depth and sacred presence. Captured in a hyperrealistic, cinematic style, the image is a masterpiece of digital painting, rendered with ultra-fine detail, sharp focus, and a tranquil, divine atmosphere. ")