import random

def generate_random_color() -> str:
    """Return a random hex color excluding near-black and near-white shades."""
    while True:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        if (r <= 30 and g <= 30 and b <= 30) or (r >= 225 and g >= 225 and b >= 225):
            continue
        return f"#{r:02X}{g:02X}{b:02X}"
